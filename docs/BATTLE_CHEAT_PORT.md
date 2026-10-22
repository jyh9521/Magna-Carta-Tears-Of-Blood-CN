# NTSC-K battle cheat candidates

Target: SCKA-20043 / AE86E04C, original ELF SHA-256
`35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0`.
This is a Korean-native implementation of selected US battle-cheat effects,
not a complete port of every US/JP cheat. Actual gameplay acceptance is pending.

## Available sections

| Case | Effect at its trigger |
|---|---|
| ally_max_hp | Set living allied actors' base maximum HP to 9999 when HP is queried |
| ally_heal | Set living allied actors' base maximum and current HP to 9999 when HP is queried |
| enemy_one_hp | Set living enemy actors' current HP to 1 when HP is queried |
| heal_and_one_hp | Combine allied healing and enemy HP 1 |
| ally_leadership | Set the friendly team leadership float to 100 when the native friendly-leadership getter runs |

HP modes share one hook and one code cave: enable **only one** of the first
four sections. The leadership section has a separate hook/cave and may be
tested alongside one HP mode. No separate battle master/activation code is needed.

These labels deliberately describe the trigger. Query-time healing is not
verified invulnerability: a lethal hit or another update between queries can
still kill an actor. Enemy HP 1 does not guarantee a damaging hit if the game
calculates zero damage. Already dead allies/enemies are not revived.

## Verified original instructions and bindings

`tools/audit_native_method_registration.py` now accepts qualified `intA` as
well as `intU` names using the same exact inline PMF-copy template. The
descriptor/source/callback checks are unchanged. Reproduce the six relevant
bindings against the original Korean ELF:

```powershell
work/venv/Scripts/python.exe tools/audit_native_method_registration.py --elf work/kr/SCKA_200.43 --identifier intAMrtsBattlePlugexecIsFriendly --identifier intAMrtsGameMagiexecGetFriendlyCurLeadership --identifier intAMrtsGameMagiexecFillPlayerTeamHP --identifier intUMrtsCharacterexecGetCurHP --identifier intUMrtsStatusexecFillHP --identifier intUMrtsTeamInfoexecGetCurTeamLeadership --out work/battle-cheat-port/verified-bindings.json --callback-limit 2048
```

**Verified static:** BattlePlug IsFriendly native path compares actor team
bytes at +39C. GameMagi FillPlayerTeamHP explicitly accepts team byte 0 at
003F8148..003F8154; creation paths write 0 at 003FBCF8 and 5 at 003FBE6C.
Battle code also branches on 5 and 0 at 003FD948..003FD970. These support the
**high-confidence deduction** that 0 is the player team and 5 the enemy team.
Other team values are left unchanged.

The existing class-cast helper at 00365310 compares object class +24 and
superclass +28 against its cached class at GP-4D34. Its initializer calls the
BattlePlug class routines at 0042EBD0/0042ED30. The hook uses this same cache
and superclass traversal; if the cache is not yet initialized or the object's
class does not match, it skips all field modifications. No raw vtable-address
bit from the US activation code is reused as a Korean team discriminator.

AMrtsPlug HP getter at 00399190 calls Character GetCurHP 003EE660 with
actor+20C. Character GetCurHP follows +60, then reads status+AC. FillHP
003EFFA0 copies status+34 to +AC. The Korean health code therefore follows
actor+20C -> character+60 -> status. Both intermediate pointers are checked
before writes. HP <= 0 is retained; enemy maximum HP is not modified.

The HP patch replaces 00399190/00399194 with a J/NOP to 000C1000. Its cave
saves/restores full 128-bit AT/V0/V1/T0/T1/T2 using R5900 SQ/LQ, applies the
class/team/pointer/living-HP checks, replays the displaced stack prologue
(`ADDIU sp,-16; SD ra,0(sp)`), and jumps back to 00399198. Original RA,
arguments, GP and callee-saved registers retain their values.

Friendly leadership callback 003FD710 calls 003FD750. The native getter's
call at 003FD758 targets 004183F0 and its original delay slot loads team
pointer +390 into A0. The patch retains that delay slot and changes only the
call target to 000C2000. The cave writes float 100 (`42C80000`) at team+28,
then tail-jumps to the original getter. Its caller return address remains
003FD760 and the original float read/conversion executes unchanged.

**Verified offline:** both cave ranges lie outside all original ELF PT_LOAD
memory ranges. **Unverified hypothesis:** those ranges remain available during
actual gameplay and do not collide with another cheat or dynamic game/kernel
use. The ELF map alone does not prove runtime ownership. Never combine these
sections with another cheat using 000C1000/000C2000 or either hook address.

## Proof and reproduction

Profile: `profiles/cheats/SCKA-20043_AE86E04C-battle.json` contains original
ELF fingerprint and exact original instruction anchors. The tool maps that
ELF into a zero-initialized 32 MiB **synthetic EE memory fixture**, not a
captured emulator memory image. Complete fixture identity is checked before
apply/verify/rollback; unknown or modified originals are rejected.

```powershell
python tools/build_battle_cheats.py baseline --elf work/kr/SCKA_200.43 --profile profiles/cheats/SCKA-20043_AE86E04C-battle.json
python tools/build_battle_cheats.py apply --elf work/kr/SCKA_200.43 --profile profiles/cheats/SCKA-20043_AE86E04C-battle.json --case heal_and_one_hp --output build/battle-cheats/heal_and_one_hp.ee-memory
python tools/build_battle_cheats.py modified --elf work/kr/SCKA_200.43 --profile profiles/cheats/SCKA-20043_AE86E04C-battle.json --case heal_and_one_hp --input build/battle-cheats/heal_and_one_hp.ee-memory
python tools/build_battle_cheats.py rollback --elf work/kr/SCKA_200.43 --profile profiles/cheats/SCKA-20043_AE86E04C-battle.json --case heal_and_one_hp --input build/battle-cheats/heal_and_one_hp.ee-memory --output build/battle-cheats/heal_and_one_hp.restored.ee-memory
python -m unittest discover -s tests -p test_battle_cheats.py -v
```

15 bounded instruction tests cover baseline behavior, full-width register
preservation, stack/return/delay slots, player/enemy/other teams, dead actors,
derived/nonmatching classes, empty cache, null intermediate pointers and
leadership float data. They execute the generated hook in a small instruction
model, not in PCSX2. Five separate modified-fixture checks and five isolated
rollback copies passed; 15 corruption/repeat/reversed-state rejection cases
passed. Earlier gameplay 8 and frame-limit 4 tests also passed. The native
regression suite passed 144 tests in the documented local venv.

Exact commands, outputs and exits: `build/battle-cheats/VERIFICATION.txt`.
`MODIFIED_FILE` is the combined PNACH with previous 60 FPS and gameplay
sections plus these five candidates. `DIFF_FILE` compares it to the previous
PNACH. Executable `ROLLBACK.sh` restores an offline EE fixture into a separate
file, not a live emulator or a saved game. All restored fixtures equal their
original mapped-ELF baseline; source ELF/ISO and installed cheats are unchanged.

## Player use and runtime checklist

Use PCSX2 Edit Cheats to open the active Korean game's PNACH. Merge the five
new battle sections from `build/battle-cheats/AE86E04C.pnach`, preserving
unrelated existing sections. Alternatively, use the combined file in a fresh
cheat setup. Enable overall cheats and one chosen HP mode. Cold-boot the game
and load a pre-test in-game save. Start with 60 FPS and other gameplay modes
OFF. A convenient first candidate is the combined healing/enemy HP 1 mode.

Cold-boot after switching or disabling modes: disabling writes does not
automatically restore already patched memory. Reload the pre-test save if
health or other status changes have been saved. Do not apply the offline
`.ee-memory` proof files to an ISO, ELF or emulator.

Record game serial/CRC, emulator version and active sections, then test:
HP display before/after hits, lethal damage, ally/enemy/neutral targeting,
dead actors, healing items, multiple battles and bosses, leadership spend and
refill, scene changes and save/load. Observe whether query-time updates fire
at the intended moments and whether the caves stay intact. No actual-game
FPS, battle timing, sustained invulnerability or long-session stability has
been verified in this work.

Enemy leadership zero, level 99, stat injections, all-talismans and JP
instant enemy wipe remain unported. Selected effects were reimplemented from
Korean native evidence rather than copying US hook/return addresses.

## Display descriptions

All current PNACH descriptions are Chinese, with per-case effect/trigger notes.
Gameplay and battle description data is kept in their profiles; generators read
that data. Description-only verification confirms executable patch lines remain
unchanged. Evidence: `build/cheat-descriptions/VERIFICATION.txt`. The installed
9-section file was localized without adding the new battle sections.
