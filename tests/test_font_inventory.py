import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from collect_font_inventory import collect


class InventoryTests(unittest.TestCase):
    def base(self):return dict(locale='sample',characters=['先','后'])
    def batch(self,target='后新A新'):return dict(locale='sample',entries=[dict(id='resource/1',target=target)])
    def test_stable_order_and_ascii(self):
        x,r=collect(self.base(),[self.batch()]);self.assertEqual(x['characters'],['先','后','新']);self.assertEqual(r['added'],1);self.assertFalse(r['reinsertion_authorized'])
    def test_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError,'identity'):collect(self.base(),[self.batch(),self.batch()])
    def test_locale(self):
        b=self.batch();b['locale']='another'
        with self.assertRaisesRegex(ValueError,'locale'):collect(self.base(),[b])
    def test_empty_target(self):
        with self.assertRaisesRegex(ValueError,'target'):collect(self.base(),[self.batch('')])
    def test_surrogate(self):
        with self.assertRaisesRegex(ValueError,'surrogate'):collect(self.base(),[self.batch('\ud800')])
    def test_duplicate_base(self):
        b=self.base();b['characters'].append('先')
        with self.assertRaisesRegex(ValueError,'duplicate'):collect(b,[self.batch()])
    def test_base_metadata_is_preserved(self):
        b=self.base();b.update(status='not-final',preserved_inventory='source/seed.json')
        x,_=collect(b,[self.batch()]);self.assertEqual(x['status'],b['status']);self.assertEqual(x['preserved_inventory'],b['preserved_inventory'])


if __name__=='__main__':unittest.main()
