"""Reopen and verify an already-built isolated field/speed candidate package."""
import argparse
import json
from pathlib import Path
from build_field_speed_cheats import baseline, transformed, render, sha

ROOT=Path(__file__).resolve().parents[1]


def verify(phase):
    out=ROOT/'build/field-speed-cheats'
    p=json.loads((ROOT/'profiles/cheats/SCKA-20043_AE86E04C-field-speed.json').read_text('utf8'))
    original=baseline((ROOT/'work/kr/SCKA_200.43').read_bytes(),p)
    if phase=='baseline':
        print('BASELINE PASS original_ELF_SHA256='+p['elf_sha256']);return
    if phase=='modified':
        for case in p['cases']:
            assert (out/f'{case}.ee-memory').read_bytes()==transformed(original,p,case),case
        assert (out/'field-speed-only.pnach').read_text('utf8')==render(p)
        assert (ROOT/'src/patches/SCKA-20043_AE86E04C-field-speed.pnach').read_text('utf8')==render(p)
        assert sha((out/'AE86E04C.pnach').read_bytes())==json.loads((out/'artifact-hashes.json').read_text('utf8'))['modified']
        print('MODIFIED PASS four_cases=true PNACH_SHA256='+sha((out/'AE86E04C.pnach').read_bytes()));return
    for case in p['cases']:assert (out/f'{case}.restored.ee-memory').read_bytes()==original,case
    hashes=json.loads((out/'artifact-hashes.json').read_text('utf8'))
    assert sha((out/'original.pnach').read_bytes())==hashes['original']
    assert (out/'rollback-test.pnach').read_bytes()==(out/'original.pnach').read_bytes()
    print('ROLLBACK PASS four_fixtures_and_PNACH_byte_identical=true')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--phase',choices=['baseline','modified','rollback'],required=True)
    verify(ap.parse_args().phase)
