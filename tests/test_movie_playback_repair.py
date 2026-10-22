"""Synthetic lossless repair tests, including cross-PES picture starts."""
from fractions import Fraction
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_playback import picture_header, structure, timestamp
from movie_playback import repair_sfd, picture_timeline, timestamp_bytes

PREFIX=b'\x00\x00\x01'
SEQ=PREFIX+b'\xb3\x28\x01\x60\x24\xff\xff\xe0\x00'
END=PREFIX+b'\xb9'+b'\xff'*2044


def pic(tr,kind=2):
    return PREFIX+b'\x00'+bytes([tr>>2,((tr&3)<<6)|(kind<<3)])+b'\xff\xff\x01\x02'


def pack(video,dts=0,pts=0,header=None):
    head=PREFIX+b'\xba'+timestamp_bytes(0,2)+b'\x80\x01\x01'
    h=header or b'\x60\x2e'+timestamp_bytes(pts,3)+timestamp_bytes(dts,1)
    body=h+video;remaining=2048-len(head)-6-len(body)
    if remaining<6:raise ValueError('fixture too large')
    padding=PREFIX+b'\xbe'+struct.pack('>H',remaining-6)+b'\x0f'+b'\xff'*(remaining-7)
    return head+PREFIX+b'\xe0'+struct.pack('>H',len(body))+body+padding


class PlaybackRepairTests(unittest.TestCase):
    def test_lossless_sequence_end_and_timestamps(self):
        v=SEQ+pic(0,1)+pic(1)+pic(2)
        source=pack(v,9009,9009)+END
        out,proof=repair_sfd(source);s,new_v,a=structure(out)
        self.assertEqual(len(out),len(source));self.assertEqual(new_v,v+PREFIX+b'\xb7')
        self.assertEqual(a,b'');self.assertEqual(proof['frames'],3)
        self.assertEqual(s['timing']['e0']['first']['pts'],0)
        self.assertEqual(s['video']['sequence_end_offsets'],[len(v)])

    def test_cross_sector_picture_prefix(self):
        a=SEQ+pic(0,1)+pic(1)[:2];b=pic(1)[2:]+pic(2)
        source=pack(a,9009,9009)+pack(b,0,0)+END
        out,proof=repair_sfd(source);s,v,_=structure(out)
        self.assertEqual(proof['frames'],3);self.assertEqual(v,a+b+PREFIX+b'\xb7')
        self.assertEqual(s['timing']['e0']['last']['pts'],6006)
        self.assertFalse(s['timing']['e0']['explicit_dts_backwards'])

    def test_gop_reset_does_not_reset_global_time(self):
        v=SEQ+pic(0,1)+pic(1)+pic(2)+SEQ+pic(0,1)+pic(1)
        positions,period=picture_timeline(v)
        self.assertEqual(len(positions),5);self.assertEqual(period,Fraction(3003))

    def test_all_10_bits_of_temporal_reference(self):
        v=SEQ+pic(0,1)+b''.join(pic(i) for i in range(1,100))
        positions,_=picture_timeline(v)
        self.assertEqual(len(positions),100)
        self.assertEqual(picture_header(v,positions[99]),(2,99))

    def test_b_frame_rejected_without_mutation(self):
        source=pack(SEQ+pic(0,1)+pic(1,3))+END;before=source
        with self.assertRaisesRegex(ValueError,'B/D'):repair_sfd(source)
        self.assertEqual(source,before)

    def test_missing_i_start_rejected(self):
        with self.assertRaises(ValueError):picture_timeline(SEQ+pic(0,2))

    def test_nonsequential_reference_rejected(self):
        with self.assertRaises(ValueError):picture_timeline(SEQ+pic(0,1)+pic(3))

    def test_rate_change_rejected(self):
        changed=bytearray(SEQ);changed[7]=0x25
        with self.assertRaises(ValueError):picture_timeline(SEQ+pic(0,1)+bytes(changed)+pic(1))

    def test_unknown_frame_rate_rejected(self):
        seq=bytearray(SEQ);seq[7]=0x20
        with self.assertRaises(ValueError):picture_timeline(bytes(seq)+pic(0,1))

    def test_double_repair_rejected(self):
        fixed,_=repair_sfd(pack(SEQ+pic(0,1))+END)
        with self.assertRaisesRegex(ValueError,'double repair'):repair_sfd(fixed)

    def test_no_picture_rejected(self):
        with self.assertRaises(ValueError):repair_sfd(pack(SEQ)+END)

    def test_no_container_end_rejected(self):
        with self.assertRaises(ValueError):repair_sfd(pack(SEQ+pic(0,1)))

    def test_audio_packet_byte_identical(self):
        audio=b'\x80\x00\x01\x1c\x03\x12\x04\x02'+struct.pack('>II',48000,32)+b'\0'*300
        head=PREFIX+b'\xba'+timestamp_bytes(0,2)+b'\x80\x01\x01'
        body=b'\x40\x04'+timestamp_bytes(0,2)+audio
        sector=head+PREFIX+b'\xc0'+struct.pack('>H',len(body))+body
        sector+=b'\xff'*(2048-len(sector))
        source=sector+pack(SEQ+pic(0,1))+END
        fixed,_=repair_sfd(source)
        self.assertEqual(fixed[:2048],sector)
        self.assertEqual(structure(fixed)[2],audio)

    def test_scr_and_program_end_unchanged(self):
        source=pack(SEQ+pic(0,1))+END;fixed,_=repair_sfd(source)
        self.assertEqual(source[:12],fixed[:12]);self.assertEqual(source[-2048:],fixed[-2048:])

    def test_missing_padding_rejected(self):
        source=bytearray(pack(SEQ+pic(0,1))+END)
        s,_,_=structure(bytes(source));end=s['timing']['e0']['first']['offset']+6+12+s['timing']['e0']['first']['bytes']
        source[end:end+4]=b'\xff'*4
        with self.assertRaisesRegex(ValueError,'padding'):repair_sfd(bytes(source))

    def test_timestamp_all_bits_roundtrip(self):
        for mark in (1,2,3):
            for value in (0,3003,90000,(1<<33)-1):self.assertEqual(timestamp(timestamp_bytes(value,mark)),value)

    def test_timestamp_invalid_rejected(self):
        for value in (-1,1<<33,1.5):
            with self.assertRaises(ValueError):timestamp_bytes(value,3)

    def test_unsupported_header_rejected(self):
        source=pack(SEQ+pic(0,1),header=timestamp_bytes(0,2))+END
        with self.assertRaisesRegex(ValueError,'header length'):repair_sfd(source)


if __name__=='__main__':unittest.main()
