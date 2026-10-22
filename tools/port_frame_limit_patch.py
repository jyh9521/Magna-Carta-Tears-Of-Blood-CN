"""Version-locked offline frame-limit patch proof; never edits the input ELF."""
import argparse
import functools
import hashlib
from pathlib import Path
import struct

SOURCE_SHA256 = '35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0'
SIZE = 4439344
VA = 0x1C69E4
OLD, NEW = 0x28410002, 0x28410001
ANCHORS = {VA-12: 0x8F8389F8, VA-8: 0x8F828C10, VA-4: 0x00621023,
           VA+4: 0x10200005, VA+8: 0, VA+16: 0x24020001,
           VA+20: 0x0C0418F8, VA+24: 0xAF828C08}


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def offset(blob, va):
    if blob[:7] != b'\x7fELF\x01\x01\x01':
        raise ValueError('ELF32 little-endian required')
    phoff = struct.unpack_from('<I', blob, 28)[0]
    entsize, count = struct.unpack_from('<HH', blob, 42)
    if entsize != 32 or phoff + count * 32 > len(blob):
        raise ValueError('invalid program headers')
    found = []
    for i in range(count):
        typ, off, addr, _, size, _, _, _ = struct.unpack_from('<8I', blob, phoff+i*32)
        if typ == 1 and addr <= va and va+4 <= addr+size:
            found.append(off+va-addr)
    if len(found) != 1 or found[0]+4 > len(blob):
        raise ValueError('address not uniquely file-backed')
    return found[0]


def validate(blob, modified=False):
    if len(blob) != SIZE:
        raise ValueError('unsupported ELF size')
    off = offset(blob, VA)
    expected = NEW if modified else OLD
    if struct.unpack_from('<I', blob, off)[0] != expected:
        raise ValueError('unexpected patch instruction')
    for va, word in ANCHORS.items():
        if struct.unpack_from('<I', blob, offset(blob, va))[0] != word:
            raise ValueError('context anchor mismatch')
    original = bytearray(blob)
    struct.pack_into('<I', original, off, OLD)
    if sha(original) != SOURCE_SHA256:
        raise ValueError('unsupported ELF fingerprint')
    return off


def transform(blob, rollback=False):
    off = validate(blob, modified=rollback)
    result = bytearray(blob)
    struct.pack_into('<I', result, off, OLD if rollback else NEW)
    validate(result, modified=not rollback)
    return bytes(result)


def pnach():
    return ('gametitle=Magna Carta - Tears of Blood NTSC-K (SCKA-20043)\n'
            '// Original ELF CRC: AE86E04C; offline instruction/context verified.\n'
            '[60 FPS]\n'
            'author=Gabominated (NTSC-U original)\n'
            'description=韩版帧率解锁测试版；游戏内效果待验证。帧率不足时可尝试提高模拟器主处理器时钟。\n'
            '// 001C69E4: slti at,v0,2 -> slti at,v0,1\n'
            'patch=1,EE,201C69E4,extended,28410001\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['baseline', 'apply', 'modified', 'rollback'])
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--pnach', type=Path)
    args = parser.parse_args()
    blob = args.input.read_bytes()
    if args.mode in ('apply', 'rollback'):
        if args.output is None or args.output.resolve() == args.input.resolve():
            raise ValueError('a separate output path is required')
        result = transform(blob, rollback=args.mode == 'rollback')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(result)
        if args.output.read_bytes() != result:
            raise ValueError('output readback mismatch')
        print(f'{args.mode.upper()} PASS word={OLD if args.mode == "rollback" else NEW:08X} sha256={sha(result)}')
        if args.pnach:
            if args.mode != 'apply':
                raise ValueError('PNACH generation requires apply')
            args.pnach.parent.mkdir(parents=True, exist_ok=True)
            args.pnach.write_text(pnach(), encoding='utf8')
            if args.pnach.read_text('utf8') != pnach():
                raise ValueError('PNACH readback mismatch')
    else:
        off = validate(blob, modified=args.mode == 'modified')
        word = struct.unpack_from('<I', blob, off)[0]
        crc = functools.reduce(int.__xor__, (w[0] for w in struct.iter_unpack('<I', blob)), 0)
        # Signed SLTI semantics for the bounded counter-difference inputs.
        values = [-1, 0, 1, 2, 3]
        decisions = ','.join(f'{v}:{int(v < (word & 0xffff))}' for v in values)
        print(f'{args.mode.upper()} PASS va={VA:08X} offset={off:08X} word={word:08X} crc={crc:08X} slti=[{decisions}]')


if __name__ == '__main__':
    main()
