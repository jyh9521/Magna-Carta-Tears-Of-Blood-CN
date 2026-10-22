# Field, detection and battle-speed candidates

Current complete installation: [ALL_HOTKEYS.md](ALL_HOTKEYS.md). Enemy-undetected
and battle speeds now use the shared SELECT latch; speed OFF releases the owned
coefficient while still in battle. Independent-switch instructions below are
historical component-stage instructions.

Update 2026-10-12: the walking candidate is withdrawn from the installed menu,
current source PNACH and new PNACH emission (`withdrawn` profile row retained
for research). The user reports undetected and battle speed work. The earlier
four-option output below is historical offline evidence. Current auto-QTE and
installation state are documented in [QTE_CHEATS.md](QTE_CHEATS.md).

Target: original SCKA-20043 / AE86E04C, 4,439,344-byte ELF,
SHA-256 `35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0`.
These are independent Korean-native experimental changes, not imported US/JP
addresses. The ISO, extracted original ELF, installed cheats and emulator settings
are unchanged. The combined candidate starts from the repository's grouped PNACH,
not from a snapshot of the user's installed PNACH.

## Evidence and actual changes

**Verified static:** exact PMF bindings associate ResetSpeed with callback
`00388870` and native target `003888A0`, SetSpeed with `00388A00`/`00388A80`,
monster TickNative with `003F6F90`, DetectedPlayer with `003F7440`, GameMagi
TickNative with `003FE140`, and SetGameSpeed with `003FAC30`/`003FACB0`.
Repeat the binding audit with `tools/audit_native_method_registration.py` and
the qualified identifiers in the profile's anchor documentation below. Local
reports are `work/field-cheats/native-bindings.json` and `mode-bindings.json`.

| Candidate | Changed branch/field | Exact change |
|---|---|---|
| walk_base_speed | ResetSpeed configuration selector | `00388924:2405009A -> 24050048`, `00388950:24050099 -> 24050048` |
| undetected | Monster Tick detection tail | `003F72C0:8E240268 -> 1000002C`; delay at `003F72C4` becomes NOP; destination `003F7374` |
| undetected | DetectedPlayer notification body | `003F746C:8C900268 -> 10000054`; delay at `003F7470` becomes NOP; destination `003F75C0` |
| battle_2x / battle_4x | GameMagi TickNative hook | `003FE208:8E220220 -> 08031000`, `003FE20C:C7A0003C -> 00000000` |
| battle_2x / battle_4x | native speed field | current object `+0078` points to speed owner, owner `+023C` is the original SetGameSpeed store; current mode byte `+024B == 2` gates multiplication |

ResetSpeed first obtains a configured integer speed (selector `48` or plug
record override), converts it to float, and stores pawn `+037C`/`+0248`. Two
mode-specific paths then overwrite `+037C` using selectors `9A`/`99`.
The walking candidate substitutes the same base selector `48`; it does not
force a fixed numeric speed or alter rendering/FPS. **High-confidence deduction:**
this removes a mode-specific configured speed difference. **Unverified hypothesis:**
the exact correspondence of these two mode values to player detect movement;
other walking situations or actors may also use ResetSpeed. It is not a confirmed
detect-only speed multiplier. The ordinary MrtsGame.u detect-state script calls
SetForceWalk, which supports investigation of a walking path, not an exact speed
ratio claim. User-selected speed values remain future work until runtime tracing.

The monster Tick tail performs player distance and visibility checks and changes
states named MrtsStateDetect/MrtsStateDetected. Skipping that tail retains the
earlier monster visibility-to-player processing. The second branch skips a
notification and reaction body after its VM parameter pointer has advanced.
Both branches retain their original stack/register epilogues. **High-confidence
deduction:** suppression of this native enemy-detection path. It does not change
bHidden or make the model transparent. Scripted encounters, prior alert state,
bosses, enemy contact and player-initiated battles require runtime verification.

SetNextGameModeField writes `1` to next-mode `+024C`; the native battle setter
writes `2`. The mode-transition path copies `+024C` to current-mode `+024B`.
A separate native battle path compares current-mode against `2`.
**Verified static:** these stores, transfer and comparison.
**High-confidence deduction:** `2` is the battle-state discriminator.

Speed code at `000C4000` saves six scratch GPRs with full-width SQ/LQ. State at
`000C43F0..000C43FB` holds owner/base/last-written float bits and initializes
only at startup. The code multiplies positive normal binary32 base values in
`[1/16,4]` exactly by adding one/two exponent units, without FPU arithmetic or
FCSR changes. Repeated ticks do not compound the multiplier. A new external
speed value becomes the base; leaving battle restores the captured base only
if the current value still equals the last value written. Changing owner never
dereferences the saved old pointer. Invalid pointers/values cause no speed write.
The two displaced instructions replay and execution resumes at `003FE210`.
The cave does not overlap ELF load segments or the existing C1000/C2000/C3000
cheat caves. Dynamic cave availability is still unverified.

## Build and verify

Region data: `profiles/cheats/SCKA-20043_AE86E04C-field-speed.json`.
Generic tool: `tools/build_field_speed_cheats.py`. Supply the exact original ELF.
Its full fingerprint, size and native instruction windows are checked before
any output. `apply` creates a separate 32 MiB offline EE-memory fixture, not an ELF
or runnable ISO; `modified` accepts only the exact expected candidate fixture;
`rollback` writes a separate restored fixture. No source file is patched in place.

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_field_speed_cheats.py baseline --elf work/kr/SCKA_200.43 --profile profiles/cheats/SCKA-20043_AE86E04C-field-speed.json
work/venv/Scripts/python.exe -X utf8 tools/build_field_speed_cheats.py pnach --elf work/kr/SCKA_200.43 --profile profiles/cheats/SCKA-20043_AE86E04C-field-speed.json --output build/field-speed-cheats/field-speed-only.pnach
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p '*cheat*.py' -v
```

For each case, use `apply --case CASE --output OUTPUT`, then `modified --case CASE
--input OUTPUT`, then `rollback --case CASE --input OUTPUT --output RESTORED`,
with the same `--elf` and `--profile` arguments. Four exact command sequences,
outputs and exit statuses are in `build/field-speed-cheats/VERIFICATION.txt`.
To reproduce the combined PNACH, preserve the grouped source bytes as
`original.pnach`, append the standalone candidate after removing its first
gametitle line, and retain every existing section. No proprietary game asset
belongs in tracked output.

**Verified offline:** 13 new instruction-model tests and 85 total cheat tests;
four candidate fixtures; four byte-identical original-map rollbacks; guarded
PNACH rollback on another copy. Tests cover original tick behavior, both factors,
non-compounding, nonbattle states, external changes, exit, owner change, invalid
pointer/float, scratch/FPU preservation and detection branch destinations.
This is not PCSX2 execution or full R5900 emulation.

## Player test procedure

Generated combined candidate: `build/field-speed-cheats/AE86E04C.pnach`.
Standalone additions: `src/patches/SCKA-20043_AE86E04C-field-speed.pnach`.
In PCSX2 Edit Cheats, append only these four sections to the active same-CRC
file; retain unrelated/current cheats. The combined file is for review and may
not match all current installed edits. Enable one new effect at a time; battle
2x/4x are mutually exclusive. These additions are **not** controlled by the
existing SELECT-Up/Down latch. Change selection with the game stopped, then
cold-boot and load an ordinary pre-test save, not a previously patched save state.
Test first with 60 FPS and the other new effects disabled.

- Walking: same straight route, same character, normal/detect OFF/on timing;
  inspect detect radius, animation, turns, collision and other walking scenes.
- Enemy detection: approach front/back, touch enemy, manually attack, change
  maps, and test scripted combat. Record whether enemies react or battles start.
- Battle: time the same complete action at OFF/2x/4x; inspect leadership,
  movement, rhythm-input windows, animations, audio and cutscene slow motion.
  Exit battle and measure field speed again. Requested whole-battle 2x/4x timing
  remains unverified until this comparison; the implemented quantity is a native
  speed-coefficient multiplier, not a guaranteed wall-clock ratio.

Disable additions and cold-boot to restore original instructions and fresh runtime
state. PNACH rollback restores file contents, not saves or a live process.
The executable `build/field-speed-cheats/ROLLBACK.sh` accepts a separate exact
combined PNACH copy and restores the preserved grouped baseline. It was tested
on `rollback-test.pnach`; the delivered combined file remains changed.
