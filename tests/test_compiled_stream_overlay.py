from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
from test_compiled_literal_rewrite import make,rewrite,TABLES,EXPORT
from audit_compiled_scripts import body
from overlay_compiled_stream_prefix import consensus_prefix,unique_prefix

class CompiledStreamOverlayTests(unittest.TestCase):
 def test_exact_prefix_overlay(self):
  raw=make(b'\x1fabc\0');new,report=rewrite(raw);s=body(raw,TABLES,EXPORT)['script'];seg,proof=unique_prefix(raw,raw,new,s,report['edits']);self.assertEqual(seg['modified'],new[:s['end']+3]);self.assertTrue(proof['all_alignment_outputs_identical'])
 def test_repeated_opcode_retained(self):
  raw=make(b'\x1fabc\0');new,report=rewrite(raw);s=body(raw,TABLES,EXPORT)['script'];bundle=raw[:s['start']]+b'\x1f'+raw[s['start']:];seg,proof=unique_prefix(bundle,raw,new,s,report['edits']);self.assertIn(b'\x1f\x1fabcdef\0',seg['modified']);self.assertFalse(proof['independent_stream_reader'])
 def test_ambiguous_original_alignment_same_output(self):
  raw=make(b'\x0b\x0b\x1fabc\0');new,report=rewrite(raw);s=body(raw,TABLES,EXPORT)['script'];bundle=raw[:s['start']]+b'\x0b'+raw[s['start']:];seg,proof=unique_prefix(bundle,raw,new,s,report['edits']);self.assertEqual(proof['original_alignment_paths'],'at-least-two');self.assertIn(b'\x0b\x0b\x0b\x1fabcdef\0',seg['modified'])
 def test_ambiguous_transform_rejected(self):
  raw=make(b'\x0b\x0b\x1fabc\0');s=body(raw,TABLES,EXPORT)['script'];bundle=raw[:s['start']]+b'\x0b'+raw[s['start']:];new=bytearray(raw);new[s['start']]=0x0c;edits=[dict(label='operand-fixture',old_offset=s['start'],new_offset=s['start'],old_bytes=1,new_bytes=1)]
  with self.assertRaises(ValueError):unique_prefix(bundle,raw,bytes(new),s,edits)
 def test_multiple_headers_rejected(self):
  raw=make(b'\x1fabc\0');new,report=rewrite(raw);s=body(raw,TABLES,EXPORT)['script']
  with self.assertRaises(ValueError):unique_prefix(raw+raw,raw,new,s,report['edits'])
 def test_unknown_payload_byte_rejected(self):
  raw=make(b'\x1fabc\0');new,report=rewrite(raw);s=body(raw,TABLES,EXPORT)['script'];bundle=bytearray(raw);bundle[s['start']+2]=ord('x')
  with self.assertRaises(ValueError):unique_prefix(bytes(bundle),raw,new,s,report['edits'])
 def test_metadata_tail_untouched(self):
  raw=make(b'\x1fabc\0');new,report=rewrite(raw);s=body(raw,TABLES,EXPORT)['script'];bundle=raw[:s['end']]+b'unknown metadata';seg,proof=unique_prefix(bundle,raw,new,s,report['edits']);self.assertEqual(bundle[seg['offset']+len(seg['original']):],b'unknown metadata');self.assertFalse(proof['metadata_tail_modified'])
 def test_repeated_context_word_low_byte_updated(self):
  raw=make(b'\x19\x01\x01\x05\0\0\x1fabc\0',14);new,report=rewrite(raw);s=body(raw,TABLES,EXPORT)['script'];word=report['branches'][0]['field_offset'];bundle=raw[:word]+raw[word:word+1]+raw[word:];seg,proof=unique_prefix(bundle,raw,new,s,report['edits']);self.assertIn(b'\x08\x08\0\0\x1fabcdef\0',seg['modified'])
if __name__=='__main__':unittest.main()
