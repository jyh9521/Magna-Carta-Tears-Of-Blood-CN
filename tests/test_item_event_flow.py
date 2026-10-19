import struct
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_item_event_flow import parse_plans


def command(cmd,*params):
    return struct.pack('<15i',cmd,*(list(params)+[0]*(14-len(params))))


class EventFlowTests(unittest.TestCase):
    def fixture(self):
        return struct.pack('<III',1,1,1)+command(204,1,497,4,1)+struct.pack('<I',1)+command(901,1,497,1)

    def test_parse_bound_commands_and_offsets(self):
        blob=self.fixture();plans,end=parse_plans(blob,0)
        self.assertEqual(end,len(blob))
        self.assertEqual(plans[0]['pIf'][0]['offset'],12)
        self.assertEqual(plans[0]['pThen'][0]['params'][:3],[1,497,1])

    def test_unaligned_start_and_opaque_tail(self):
        blob=b'abc'+self.fixture()+b'opaque'
        plans,end=parse_plans(blob,3)
        self.assertEqual(blob[end:],b'opaque')
        self.assertEqual(plans[0]['offset'],7)

    def test_truncated_header(self):
        with self.assertRaises(ValueError):parse_plans(b'abc',0)

    def test_truncated_commands(self):
        with self.assertRaises(ValueError):parse_plans(self.fixture()[:-1],0)

    def test_invalid_count(self):
        for count in [-1,0,1001]:
            with self.assertRaises(ValueError):parse_plans(struct.pack('<i',count),0)

    def test_invalid_repetition(self):
        with self.assertRaises(ValueError):parse_plans(struct.pack('<III',1,2,0),0)

    def test_invalid_command_and_negative_offset(self):
        bad=struct.pack('<III',1,1,1)+command(-1)+struct.pack('<I',0)
        with self.assertRaises(ValueError):parse_plans(bad,0)
        with self.assertRaises(ValueError):parse_plans(self.fixture(),-1)


if __name__=='__main__':unittest.main()
