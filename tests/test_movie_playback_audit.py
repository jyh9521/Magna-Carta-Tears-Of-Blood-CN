"""Synthetic MPEG/SFD regressions, no copyrighted assets required."""
import copy
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_playback import (picture_header,timestamp,structure,video_info,
                                  pes_header,framehash_summary,compare)


def ts(value,mark=2):
    return bytes([(mark<<4)|((value>>29)&14)|1,(value>>22)&255,
                  ((value>>14)&254)|1,(value>>7)&255,((value<<1)&254)|1])


def pic(reference,kind=2):
    return b'\x00\x00\x01\x00'+bytes([reference>>2,((reference&3)<<6)|(kind<<3)])+b'\xff\xff'


def pack(payload,pts=0,dts=0,scr=0):
    header=b'\x00\x00\x01\xba'+ts(scr)+b'\x80\x01\x01'
    body=b'\x60\x2e'+ts(pts,3)+ts(dts,1)+payload
    block=header+b'\x00\x00\x01\xe0'+struct.pack('>H',len(body))+body
    return block+b'\xff'*(2048-len(block))


class MoviePlaybackAuditTests(unittest.TestCase):
    def test_full_temporal_reference_range(self):
        for value in range(1024):
            self.assertEqual(picture_header(pic(value)),(2,value))

    def test_all_picture_types(self):
        for kind in (1,2,3,4):self.assertEqual(picture_header(pic(11,kind)),(kind,11))

    def test_truncated_picture_rejected(self):
        with self.assertRaises(ValueError):picture_header(b'\x00\x00\x01\x00\x01')

    def test_timestamp_range(self):
        for value in (0,3003,90000,(1<<33)-1):self.assertEqual(timestamp(ts(value)),value)

    def test_timestamp_marker_rejected(self):
        with self.assertRaises(ValueError):timestamp(b'\x20\x00\x00\x00\x00')

    def test_pes_pts_dts(self):
        body=b'\xff\xff\x60\x2e'+ts(9009,3)+ts(6006,1)+pic(3)
        offset,pts,dts=pes_header(body,0,len(body))
        self.assertEqual((offset,pts,dts),(14,9009,6006))

    def test_video_inventory(self):
        data=b'\x00\x00\x01\xb3\x28\x01\x60\x24\xff\xff\xe0\x00'+pic(0,1)+pic(11)+b'\x00\x00\x01\xb7'
        info=video_info(data)
        self.assertEqual(info['pictures'],2);self.assertEqual(info['temporal_reference_max'],11)
        self.assertEqual(info['sequences'][0]['width'],640);self.assertEqual(info['sequences'][0]['height'],352)
        self.assertTrue(info['sequence_end_offsets'])

    def test_sector_demux_preserves_picture_split(self):
        frame=pic(11);a=frame[:3];b=frame[3:]
        result,v,audio=structure(pack(a)+pack(b)+b'\x00\x00\x01\xb9'+b'\xff'*2044)
        self.assertEqual(v,frame);self.assertEqual(audio,b'');self.assertEqual(result['video']['pictures'],1)
        self.assertEqual(result['issues'],[])

    def test_explicit_dts_backwards(self):
        result,_,_=structure(pack(pic(0),dts=9009)+pack(pic(1),dts=6006)+b'\x00\x00\x01\xb9'+b'\xff'*2044)
        self.assertEqual(len(result['timing']['e0']['explicit_dts_backwards']),1)

    def test_b_frame_pts_reordering_not_dts_error(self):
        result,_,_=structure(pack(pic(2),pts=9009,dts=3003)+pack(pic(1,3),pts=6006,dts=6006)+b'\x00\x00\x01\xb9'+b'\xff'*2044)
        self.assertFalse(result['timing']['e0']['explicit_dts_backwards'])

    def test_missing_end_detected(self):
        result,_,_=structure(pack(pic(0)));self.assertIn('missing_program_end_sector',result['issues'])

    def test_sequence_end_at_exact_eof(self):
        self.assertEqual(video_info(pic(0)+b'\x00\x00\x01\xb7')['sequence_end_offsets'],[8])

    def test_program_end_does_not_replace_sequence_end(self):
        result,_,_=structure(pack(pic(0))+b'\x00\x00\x01\xb9'+b'\xff'*2044)
        self.assertEqual(len(result['program_end_offsets']),1)
        self.assertEqual(result['video']['sequence_end_offsets'],[])

    def test_packet_overflow_detected(self):
        data=bytearray(pack(pic(0)));data[16:18]=b'\xff\xff'
        result,_,_=structure(bytes(data));self.assertTrue(any(x.startswith('PES_exceeds_sector') for x in result['issues']))

    def test_framehash_video_and_audio(self):
        data=b'#tb 0: 1001/30000\n0, 0, 0, 1, 20, aaaa\n1, 0, 0, 32, 128, bbbb\n0, 1, 1, 1, 20, cccc\n'
        summary=framehash_summary(data)
        self.assertEqual(summary['streams']['0']['frames'],2);self.assertEqual(summary['streams']['1']['frames'],1)

    def test_no_decode_success_when_exit_nonzero(self):
        row=dict(sha256='new',audio={'sha256':'audio'},picture_count_agrees=True,
                 video={'pictures':2,'sequence_end_offsets':[]},decode={'exit':1,'stderr':'failure'},
                 probe={'dts_backwards':[]},timing={'e0':{'explicit_dts_backwards':[]}},issues=[],mux_rates=[1])
        old=copy.deepcopy(row);old['sha256']='old'
        self.assertIn('full_decode_failed',compare(old,row))


if __name__=='__main__':unittest.main()
