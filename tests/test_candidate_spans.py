import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from audit_candidate_spans import classify, placement


def row(start, length, identity='primary'):
    return dict(offset=start, source_bytes=length, id=identity)


class CandidateSpanTests(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(classify(row(2, 4), [row(2, 4)], 10)['relation'], 'exact-primary-span')

    def test_contained_not_missing(self):
        result = classify(row(3, 2), [row(2, 4)], 10)
        self.assertEqual(result['relation'], 'contained-in-primary-union')
        self.assertEqual(result['uncovered_intervals'], [])

    def test_partial(self):
        result = classify(row(1, 8), [row(2, 2), row(5, 2)], 10)
        self.assertEqual(result['covered_bytes'], 4)
        self.assertEqual(result['uncovered_intervals'], [dict(offset=1,source_bytes=1),
            dict(offset=4,source_bytes=1),dict(offset=7,source_bytes=2)])

    def test_union_not_double_counted(self):
        result = classify(row(2, 6), [row(2,4), row(4,4)], 10)
        self.assertEqual(result['covered_bytes'], 6)
        self.assertEqual(result['relation'], 'contained-in-primary-union')

    def test_adjacent_does_not_overlap(self):
        self.assertEqual(classify(row(4,2), [row(2,2)], 10)['relation'], 'outside-primary')

    def test_empty(self):
        self.assertEqual(classify(row(3,0), [], 10)['relation'], 'empty')

    def test_invalid_bounds(self):
        for start,length in [(-1,1),(9,2),(2,-1),(True,1)]:
            with self.assertRaisesRegex(ValueError, 'invalid source interval'):
                classify(row(start,length), [], 10)

    def test_placement_preserves_trailer_boundary(self):
        result = placement(0, 10, 2, [(b'ab\0\0CDxy', 8)], 8)
        self.assertEqual([r['region'] for r in result],
                         ['header','leading-field','terminator-or-padding','observed-trailer'])
        self.assertEqual(sum(r['source_bytes'] for r in result), 10)


if __name__ == '__main__':
    unittest.main()
