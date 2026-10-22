# NTSC-K frame-limit patch

## Input and attribution

Original NTSC-U 60 FPS code: Gabominated, SLUS-21221 / C0AC5781,
`patch=1,EE,201C69E4,extended,28410001` (original word `28410002`).
Reference: [PCSX2 upstream patch](https://github.com/PCSX2/pcsx2_patches/blob/main/patches/SLUS-21221_C0AC5781.pnach).
Upstream US ELF is not a local input; no complete cross-region function comparison is claimed.

Target: SCKA-20043, executable `SCKA_200.43`, 4,439,344 bytes,
SHA-256 `35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0`,
PCSX2 ELF CRC `AE86E04C`. CRC is XOR of ELF little-endian u32 words,
not ISO CRC32; see [PCSX2 GetCRC](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/Elfheader.cpp).

## Findings

**Verified static:** Korean VA `0x001C69E4` maps to ELF offset `0x000C6A64`.
The word is also `28410002`, `slti at,v0,2`. The preceding instructions load
GP-relative values at `-0x7608` and `-0x73f0`, subtract them, then test the result.
The subsequent `beqz at,0x001C6A00` skips a call to `0x001063E0` when the
difference reaches the threshold. Changing the immediate from 2 to 1 changes
the signed comparison; the instruction and branch remain otherwise intact.
Exactly one ELF byte changes (`02 -> 01`); full fingerprint and neighboring
instruction anchors are checked by the tool. The same virtual address is
coincidental here, not a general rule for region ports.

**High-confidence deduction:** this is the NTSC-K counterpart of the supplied
US frame-wait patch. Its threshold behavior is consistent with reducing a
two-tick wait to one tick.

**Unverified runtime:** actual rendered 60 FPS, unchanged game speed, FMV
timing, battle timing, loading/saving, and long-session stability. Offline
SLTI results are not a gameplay test. Start with normal EE clock, then evaluate
overclock only if the emulator cannot maintain full speed.

## Use without modifying the game

Copy `src/patches/SCKA-20043_AE86E04C.pnach` to the active PCSX2 cheats directory
as `AE86E04C.pnach`, or merge its 60 FPS section into an existing same-CRC file.
Enable cheats and this section; cold-boot the game. Disable the section and
cold-boot again to restore stock behavior. Do not use a savestate as the sole
OFF/on comparison. The original ISO has not been edited or the cheat installed
automatically. Do not use the modified offline ELF as a replacement game ELF:
its CRC becomes `AE86E04F`, so the original-CRC PNACH would no longer match it.

Record same-scene OFF/on rendered frame rate, emulator speed, movement duration,
battle input windows, FMV audio/video sync, save/load and scene transitions.
The emulator's 60 Hz output alone does not establish 60 unique game frames.

## Reproduce offline proof

```powershell
python tools/port_frame_limit_patch.py baseline work/kr/SCKA_200.43
python tools/port_frame_limit_patch.py apply work/kr/SCKA_200.43 --output build/fps-port/SCKA_200.43.60fps --pnach build/fps-port/AE86E04C.pnach
python tools/port_frame_limit_patch.py modified build/fps-port/SCKA_200.43.60fps
python tools/port_frame_limit_patch.py rollback build/fps-port/SCKA_200.43.60fps --output build/fps-port/SCKA_200.43.restored
python -m unittest discover -s tests -p test_frame_limit_patch.py -v
```

For a fresh checkout, extract the original ELF from the user-supplied Korean
ISO first; `work/kr` is a local input convention, not a shipped dependency.
No original executable is tracked. The tool rejects wrong size, fingerprint,
instruction/context, repeat application, and rollback against original data.
It only writes a separate output; source bytes remain untouched.

Local evidence: `build/fps-port/VERIFICATION.txt`, `DIFF_FILE`, patched ELF,
and executable `ROLLBACK.sh`. Baseline, modified comparison and isolated
rollback all returned exit 0; restored ELF is byte-identical to the source.
Four focused unit tests and four real-ELF rejection cases passed.
