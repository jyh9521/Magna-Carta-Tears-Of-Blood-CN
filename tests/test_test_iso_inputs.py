from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from build_test_iso import checked_inputs,grouped_replacements

class TestIsoInputTests(unittest.TestCase):
 def test_directory_batch_order_matches_iso_writer(self):
  names=['/FILE.AFS','/SHIP.AFS','/MOVIE18/1.SFD','/MOVIE99/2.SFD','/MOVIE18/3.SFD'];self.assertEqual(list(grouped_replacements(dict.fromkeys(names,Path('fixture')))),['/FILE.AFS','/SHIP.AFS','/MOVIE18/1.SFD','/MOVIE18/3.SFD','/MOVIE99/2.SFD'])
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);d=Path(self.temp.name)
  def row(name):
   p=d/name;p.write_bytes(name.encode());return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
  self.plan=dict(schema=1,locale='zh-CN',archives={n:row(n) for n in ('FILE.AFS','SHIP.AFS')});sfd=row('1.SFD');review=row('1.mp4');self.movies=dict(selected_count=1,retained_original_count=1,movies=[dict(movie='1',sfd_path=sfd['path'],sfd_bytes=5,sfd_sha256=sfd['sha256'],accepted_review_path=review['path'],accepted_review_sha256=review['sha256'],manual_movie_acceptance=True,original_sfd_sha256='a'*64)]);self.files={'/FILE.AFS':(1,1),'/SHIP.AFS':(2,1),'/MOVIE18/1.SFD':(3,1),'/MOVIE99/2.SFD':(4,1)}
 def test_complete_inputs(self):
  replacements,proof,retained=checked_inputs(self.plan,self.movies,self.files);self.assertEqual(len(replacements),3);self.assertEqual(retained,['2']);self.assertEqual(proof[0]['iso_path'],'/MOVIE18/1.SFD')
 def test_optional_texture_archive(self):
  p=Path(self.temp.name)/'LINEAR.AFS';p.write_bytes(b'textures');self.plan['archives']['LINEAR.AFS']=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest());self.files['/LINEAR.AFS']=(5,8)
  replacements,_,_=checked_inputs(self.plan,self.movies,self.files);self.assertEqual(replacements['/LINEAR.AFS'],p)
 def test_unknown_archive_rejected(self):
  self.plan['archives']['UNKNOWN.AFS']=self.plan['archives']['FILE.AFS']
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_missing_source_archive_rejected(self):
  del self.files['/FILE.AFS']
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_bad_archive_hash_rejected(self):
  self.plan['archives']['FILE.AFS']['sha256']='0'*64
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_missing_ship_rejected(self):
  del self.plan['archives']['SHIP.AFS']
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_bad_locale_rejected(self):
  self.plan['locale']='../escape'
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_unaccepted_movie_rejected(self):
  self.movies['movies'][0]['manual_movie_acceptance']=False
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_sfd_tamper_rejected(self):
  self.movies['movies'][0]['sfd_sha256']='0'*64
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_mp4_tamper_rejected(self):
  self.movies['movies'][0]['accepted_review_sha256']='0'*64
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_movie_inventory_mismatch_rejected(self):
  self.movies['retained_original_count']=2
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
 def test_unknown_movie_rejected(self):
  self.movies['movies'][0]['movie']='3'
  with self.assertRaises(ValueError):checked_inputs(self.plan,self.movies,self.files)
if __name__=='__main__':unittest.main()
