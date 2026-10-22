# Original-engine auto-QTE candidate

Update: current installed QTE now shares SELECT-Up/Down with every active effect.
Its former independent-switch instructions below are historical. Use the complete
source and procedure in [ALL_HOTKEYS.md](ALL_HOTKEYS.md).

## Current player-facing state

User feedback on 2026-10-12 reports that enemy-undetected and battle-speed
options work. This is user-reported runtime evidence, not an independent
multi-scene acceptance. The walking candidate was withdrawn at the user's
request, removed from the installed menu and current source PNACH, and marked
`withdrawn` in its research profile so new PNACH builds do not reintroduce it.
Old research offsets and offline tests remain available.

The new option is `战斗其他（可独立启用）\自动QTE（首键启动）`.
It is installed into the actual `SCKA-20043_AE86E04C.pnach` in the active PCSX2
cheats directory, while preserving all unrelated sections and never writing
emulator/game settings. Reload cheats, select this option, and cold-boot.
Select the skill/target and press the first QTE input to begin the attack rhythm;
the intended effect is automatic subsequent Great results without timing inputs.
It is not automatic battle selection or repeated keyboard/controller injection.
It is independent of the existing SELECT latch. Deselect and cold-boot to restore
original code. Use an ordinary save, not a save state holding old patched code.

The auto-QTE option is **pending runtime acceptance**. Test normal attacks at
OFF/1x/2x/4x, all three input patterns, wrong manual input, combo continuation,
defence and counterattack. Check that later beats finish without input, the
attack actually executes, the battle returns to targeting, and menus/field
remain unaffected. The existing timeout branch still passes RR_Miss to its
ProcessSound call even when GetGreat caused a successful RecordBit; sound cues
may therefore differ from normal timed success. No sound behavior is claimed
as tested or changed by this patch.

## Version and verified native change

Supported input: SCKA-20043 / AE86E04C, original ELF 4,439,344 bytes,
SHA-256 `35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0`.
Profile: `profiles/cheats/SCKA-20043_AE86E04C-qte.json`.

**Verified static:** the exact inline PMF initializer binds
`intUMrtsDataManagerexecGetGreat` to callback `002F8B40`, whose JAL at
`002F8B58` calls native leaf `002F8B80`. The callback advances its script
parameter pointer before the call and stores the returned value afterward.
The native leaf originally reads DataManager byte `+07B5`, extracts bit 1,
and returns that boolean. Its instructions are:

| VA | Original word | Meaning |
|---|---|---|
| 002F8B80 | 908207B5 | LBU v0,07B5(a0) |
| 002F8B84 | 000217BC | DSLL32 v0,v0,30 |
| 002F8B88 | 03E00008 | JR ra |
| 002F8B8C | 000217FE | delayed DSRL32 v0,v0,31 |

The single patch replaces the JR delay-slot word at `002F8B8C` with
`24020001`, ADDIU v0,zero,1. The return still executes its delay slot; the
original load/extraction precursor, callback parameter advancement and result
storage remain. No controller packet, new cave or persistent DataManager flag
is written. Existing SetGreat may still change the stored flag, but this
selected candidate overrides the getter return until cold-boot restoration.

## Why this is auto-completion, not only easier timing

**Verified package structure:** original FILE.AFS fingerprint
`a9f7e2b34bfb5475bab2793821520295d120e2a122ccd363812f2d03c025072b`;
MrtsGame.u contains MrtsRhythmManager TextBuffer source export 12857 and
ordinary compiled functions. Its GetGreat imported method has exactly two
ordinary compiled call-reference users: TimeOver (export 8221) and TestBit
(export 8311). Source and serial fingerprints are preserved in the audit.

**High-confidence source/compiled deduction:** TestBit's GetGreat branch sets
the current result to RR_Great and bypasses incorrect-key/timing comparisons.
Separately, TimeOver's GetGreat branch calls RecordBit(0,0), rather than taking
the MissBit/BreakRhythm path. It advances CurBit/Count, sets DesireBit, and
transitions to RMFinish after three beats. GetFinalResult and final notification
then remain original. Thus the candidate uses a native debug branch already
designed to record beats without fresh input; changing only GreatTime would
not achieve this automatic progression.

RMIdle returns from TimeOver, and its first Bit input calls PlayRhythm. Therefore
the candidate intentionally requires a first input to start a normal attack.
Tick's bNowPlaying and bBreak guards retain pause/break gating. Counterattack
uses Count+1 for its deadline. Subsequent HUD/combo/state behavior remains
original and requires runtime QA. Neither the source TextBuffer nor ordinary
compiled references alone proves full streaming VM execution or gameplay.

## Reproducible tools and tests

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_qte_flow.py --elf work/kr/SCKA_200.43 --archive work/kr/FILE.AFS --out work/qte-cheats/flow-audit.json
work/venv/Scripts/python.exe -X utf8 tools/build_qte_cheats.py baseline --profile profiles/cheats/SCKA-20043_AE86E04C-qte.json --input work/kr/SCKA_200.43
work/venv/Scripts/python.exe -X utf8 tools/build_qte_cheats.py pnach --profile profiles/cheats/SCKA-20043_AE86E04C-qte.json --input work/kr/SCKA_200.43 --output build/qte-cheats/qte-only.pnach
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p '*cheat*.py' -v
```

`build_qte_cheats.py` also provides apply/modified/rollback on separate ELF
copies, with full original hash, size and native context validation. It never
edits the input. Do not replace the ISO's ELF with the offline proof copy;
use the source `src/patches/SCKA-20043_AE86E04C-qte.pnach` on the original CRC.

**Verified offline:** 11 new tests exercise the actual original/replacement
leaf words with all 256 byte-flag inputs, JR delay semantics, full untouched
register lanes and no flag-memory writes. Explicit source-derived rhythm models
cover first-input gating, timeout completion, 1x/2x/4x/large step, original miss,
pause/break and counter timing. These models are not a full Unreal VM test.
The 96-test cheat regression set passes. Modified ELF rollback is byte-identical
to original. The delivered executable PNACH rollback script was run on another
copy and restored the exact pre-transaction file (which includes the withdrawn
walking option). The active installed file remains changed, with walking absent
and auto-QTE present. Original ELF/ISO and settings are not written.

Exact commands, literal outputs, exits, old/new hashes, diff and rollback are
recorded under `build/qte-install`. The first install attempt completed the
candidate write but stopped on an outdated INI hash assertion while the running
emulator persisted settings; the repaired transaction accepts only the exact
already-installed candidate and preserves the current INIs without duplicate
sections. This was an audit-state failure, not a QTE gameplay result.

Earlier `build/field-speed-cheats` artifacts/verification are historical four-option
research output. Current standalone field-speed source/generation emits only
undetected and two speed options; the withdrawn walking selector remains in the
profile solely as reproducible research.
