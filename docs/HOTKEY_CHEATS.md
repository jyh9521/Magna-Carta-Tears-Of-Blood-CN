# Korean cheat hotkey prototype

Current complete installed revision: [ALL_HOTKEYS.md](ALL_HOTKEYS.md). All 14
active effect choices, including enemy-undetected, battle speed and auto-QTE,
now share SELECT-Up/Down. Speed keeps a latch-gated maintenance hook for owned
coefficient restoration on OFF. Earlier counts/layouts below describe prior stages.

Target: original SCKA-20043 / AE86E04C. This optional variant preserves the
14 existing section names and implements a shared ON/OFF latch. Original
ELF SHA-256 is locked by the input, gameplay and battle profiles. Original
game files and PCSX2 selection/config settings are unchanged.

## Player use

The tested variant was installed into the active user's cheat file, with the
previous file preserved at `build/hotkey-cheats/original-installed.pnach`.
Stop the current game and cold-boot once after installing this variant.
Keep PCSX2 Enable Cheats ON and preselect desired sections before launching:

- The selected effects start OFF.
- SELECT + D-pad Up enables all selected effects and latches ON after release.
- SELECT + D-pad Down disables them and restores their original instructions
  on the next continuous patch pass. No game restart is designed to be needed
  for this hotkey OFF transition, but actual runtime acceptance is pending.
- Unselected sections are not applied. Money/item/HP alternatives remain
  mutually exclusive; select only one mode in each family.
- A gamepad or keyboard works through the PS2 controller bindings. Keyboard
  arrow keys alone are not guaranteed to represent D-pad Up/Down: use the
  configured PS2 SELECT and D-pad mappings.
- Both direction combinations together resolve to OFF. Additional buttons
  are tolerated. Another controller port or multitap slot does not control
  the latch. An invalid primary controller read/packet resets the latch OFF.
- Do not cancel section checkboxes or the overall cheats switch mid-game as
  a substitute for SELECT+Down: disabling its patch group also removes its
  OFF restoration writes. Use the hotkey OFF first; cold-boot after changing
  selected modes or removing the variant.

Numeric money/item/HP/leadership changes already made are not rolled back;
restoration means the original code executes again. Load a pre-test save to
restore saved values. Combinations are not swallowed, so the original game
may also react to those buttons. Runtime button response, sampling latency,
gameplay effects and code-cave ownership remain unverified.

The controller dispatcher is an **unlabelled** group before the first section.
PCSX2 automatically enables unlabelled commands when cheats are enabled,
while applying named groups only when selected. It also counts unlabelled
commands individually in its active-cheat count; a larger on-screen count
does not mean every named effect was enabled. Source:
[PCSX2 Patch.cpp EnablePatches](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/Patch.cpp).

## Input research

**Verified static data flow:** the main engine input call at 0017C738 targets
00120800. Its original delay slot constructs A2 = S0+2A4, while A0/A1 are the
port/slot values. The successful-read path at 0017C748..0017C764 loads packet
bytes 2/3, combines `(byte2 << 8) | byte3`, XORs FFFF, and stores the resulting
button mask at S0+2A0. No Japanese fixed pad-memory address was reused.

The function at 00120800 selects the libpad double buffer through 00120750,
copies its packet to A2, and returns its byte count/status. Its ABI and the
library's nearby diagnostics support the **high-confidence deduction** that
this is the original padRead-compatible function. No stripped symbol was
recovered and it is not replaced with an external SDK implementation.

Packet status/mode/button fields and standard SELECT=0001, UP=0010,
DOWN=0040 masks are cross-checked against
[PS2SDK libpad.h](https://github.com/ps2dev/ps2sdk/blob/master/ee/rpc/pad/include/libpad.h).
The Korean consumer uses a byte-swapped internal mask, not SDK bit positions.
The wrapper must combine `byte2 | (byte3 << 8)` before applying SDK masks. Digital 41,
analog 73 and pressure 79 packets are accepted; invalid packets turn OFF.

## Hook and patch design

Profile: `profiles/cheats/SCKA-20043_AE86E04C-hotkeys.json` locks exact original
input-consumer/library instruction anchors and ELF hash. The input call
0017C738 changes from 0C048200 to 0C030C00; the delay slot is unchanged.

The new wrapper at 000C3000 calls the original reader once. It saves input
port/slot/packet arguments on its own stack, then preserves the original
reader's returned scratch-register state with full-width R5900 SQ/LQ. It
reads the actual returned packet, updates the word latch at 000C3FE0 and
returns to 0017C740 with the reader's return value and caller state preserved.
The original packet contents and downstream input consumer remain unchanged.

The latch is zeroed once at ELF startup (`patch=0`). Control code is refreshed
every frame. Each selected named group has an E-code block for latch=1 with
its original effect writes, followed by a latch=0 block restoring original
file-backed instructions. Every conditional body uses extended 32-bit writes;
the count is computed exactly, and every block is under 256 commands.
PCSX2 E-code semantics were checked against the primary Patch.cpp source.

OFF leaves unreachable payload caves intact instead of clearing code during
a possible return. The controller dispatcher itself stays active so the next
SELECT+Up can work. 000C3000/000C3FE0 are outside the original ELF load map;
that does not prove their dynamic availability. Earlier HP/leadership cave
limits in [BATTLE_CHEAT_PORT.md](BATTLE_CHEAT_PORT.md) also remain.

The converter accepts only section names and exact writes produced by the
version-locked existing profiles. Unknown/custom source cheats fail rather
than receiving guessed original-byte restoration. Existing descriptions,
attribution and section names are retained; Chinese hotkey notes are appended.

## Reproduce and evidence

```powershell
python tools/build_hotkey_cheats.py --elf work/kr/SCKA_200.43 --source build/hotkey-cheats/original-installed.pnach --output build/hotkey-cheats/AE86E04C.pnach
python tools/verify_hotkey_cheats.py baseline --elf work/kr/SCKA_200.43 --source build/hotkey-cheats/original-installed.pnach --pnach build/hotkey-cheats/AE86E04C.pnach
python tools/verify_hotkey_cheats.py modified --elf work/kr/SCKA_200.43 --source build/hotkey-cheats/original-installed.pnach --pnach build/hotkey-cheats/AE86E04C.pnach
python -m unittest discover -s tests -p test_hotkey_cheats.py -q
```

For a fresh checkout, use `src/patches/SCKA-20043_AE86E04C.pnach` as
`--source`, with the original Korean ELF supplied by the user. The
`original-installed.pnach` filename above is a local snapshot convention,
not a mandatory private dependency. A source file can contain the supported
subset of sections; the currently installed test input contains all 14.

15 controller/conditional tests and 25 earlier gameplay/battle tests passed,
plus 4 frame-limit and 144 native regression tests. The real original ELF
anchors and generated PNACH were checked. A bounded callback model and a
small model of the emitted PNACH subset verified 84 ON/release/OFF/release/
ON/OFF transitions over the 14 groups, including unselected-group identity.
The original external padRead call is a **stub** in the callback model; this
does not establish physical input or PCSX2 runtime success.

`build/hotkey-cheats/VERIFICATION.txt` records literal commands, outputs,
exit statuses and original/modified installed hashes. `DIFF_FILE` compares
the preserved direct file and hotkey variant. Executable `ROLLBACK.sh`
restores the preserved direct file only when the target matches the tested
hotkey hash. It was tested on an isolated copy, byte-identical after restore.
Running it without a target restores the installed file; cold-boot afterward.
It does not modify configuration/selection settings or revert saved game data.

Manual acceptance: use a pre-test save; start with one observable mode, e.g.
consumption without money decrease. Check default OFF, SELECT+Up then buy,
release and buy again, SELECT+Down then buy, and repeat. Then test the HP/
leadership candidates independently, controller disconnect, scenes and saves.
Record active sections and observed values rather than treating unit models
as actual game acceptance. The direct-mode source remains available separately.

## 2026-10-12 raw-packet byte-order regression

**Verified live observation:** a read-only PCSX2 sample captured primary DMA
buffers 00550800/00550880 with packets `00 73 EE FF`, `00 73 CE FF` and
`00 73 EE F7` while the player held SELECT+Up. The latch 000C3FE0 stayed zero
and frame instruction 001C69E4 stayed 28410002. Extra pressed bits were also
observed; the chord detector must tolerate them.

**Verified model defect:** the old wrapper combined `(byte2 << 8) | byte3`
but used SDK masks 0011/0041. Replaying the actual packets reproduced latch=0.
The corrected wrapper combines `byte2 | (byte3 << 8)`; replay of all three
packets gives latch=1. The native downstream consumer remains untouched.
The original test fixture made the same byte-order mistake and therefore
passed despite this defect. Raw-packet regression tests now use captured
bytes directly. The SELECT+Down `00 73 BE FF` test remains a constructed
fixture, not a captured physical DOWN event.

**Pending live acceptance:** this repair establishes the byte-order defect,
not that the input call-site executes in every gameplay state. The installed
repair needs a cold boot and actual ON/OFF test. Static 17 tests and 84
transitions are not evidence of real 60 FPS. Evidence and isolated rollback:
`build/hotkey-byteorder/VERIFICATION.txt`. Rollback restores the previous
hotkey file including its byte-order defect; the earlier direct-mode restore
remains separately available in `build/hotkey-cheats/`.

## Player-reported acceptance and UI selection (2026-10-12)

The player reports that the corrected hotkeys work, buying increases money,
selling does not decrease item quantity, and 60 FPS works. These are player
reports, not an instrumented acceptance of all 14 effects or battle hooks.

Descriptions now use Arabic quantities: 99, 98, 9999, 1, 100, 1000000.
Only description metadata changed; section names, instructions and bindings
remain identical. Evidence: `build/cheat-description-numbers/VERIFICATION.txt`.

PCSX2 v2.8.2's native cheat list stores independently enabled section names.
Its checkbox handlers have no exclusive-family relationship; PNACH metadata
does not make siblings disabled or radio-selectable. Native UI exclusivity
requires an emulator UI change; a separate radio-based selector could enforce
it before writing the chosen names. Runtime priority is not UI exclusion.
Source: [v2.8.2 GameCheatSettingsWidget.cpp](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-qt/Settings/GameCheatSettingsWidget.cpp).

## Native consumption tree variant

`tools/build_grouped_cheats.py` validates the complete flat hotkey source
against the original Korean ELF/profile output before rearranging sections.
The optional `src/patches/SCKA-20043_AE86E04C-grouped.pnach` keeps 60 FPS first,
then emits `消费\关闭`, `消费\不扣钱`, `消费\反加钱`, and
`消费\钱不够也能消费`. Other existing names remain unchanged. PCSX2 splits
section names at backslashes and creates the parent as an ordinary Qt item,
without user-checkable flags. The parent is not a real `[消费]` patch section.
This is verified from the v2.8.2 UI source; local visual acceptance is pending.

The OFF child restores the original spending instructions at 003A06F0,
003A06F8 and 003A0700, independently of the global hotkey latch. Deselect
all three spending-effect siblings before selecting OFF; native checkboxes
remain independent and this layout does not implement radio exclusivity.
Existing effect bodies and the working hotkey wrapper remain identical.
Renamed consumption selections must be reselected after reload. No emulator
binary or selection INI is modified. Cold boot after changing selected modes;
use SELECT+Down before changing live groups, as documented above.

Reproduce:
```powershell
python tools/build_grouped_cheats.py --elf work/kr/SCKA_200.43 --source src/patches/SCKA-20043_AE86E04C-hotkeys.pnach --output build/cheat-grouping/AE86E04C.pnach
python -m unittest discover -s tests -p test_grouped_cheats.py -q
```
Evidence and file-only rollback: `build/cheat-grouping/VERIFICATION.txt`.

## Complete grouped layout and mandatory controller section

The current grouped generator supersedes the consumption-only variant.
60 FPS remains first, followed by a command-free shortcut explanation row.
Consumption, items and battle HP parents say `下方最多启用1项`; money gain
and leadership use independent groups. Each exclusive family has an OFF
child restoring verified original instructions; deselect sibling effects first.
The parent labels are not checkbox items. Parent descriptions are not supported
by the native UI, so the rule is included in the parent name itself.

The 64 formerly unlabelled commands consist of one startup latch reset plus
63 continuous controller wrapper/call-site commands. They are moved byte-for-
byte into a named mandatory controller child. This is not 64 separate cheats
or 64 separate pad tests. The installed selection INI must include this child's
full name; `migrate_selection_ini` maps old enabled effect names and appends
the controller once, preserving unrelated enabled patches/settings. Turning
that child off disables the detector. PNACH provides no noncheckable yet
mandatory executable child; the native UI still exposes its checkbox, labeled
`已自动启用，请保持勾选`. This is a displayed instruction, not a locked checkbox.

Evidence: `build/cheat-grouping-all/VERIFICATION.txt`. Rollback restores both
the preserved previous PNACH and selection INI with hash checks. Refresh the
settings window after installation so it reads renamed enabled names. No
emulator binary changed; repaired runtime input and effect instruction bodies
remain unchanged. Visual and in-game acceptance of this layout remain pending.

## Retired money-gain and item alternatives

The player reports that the money-gain maximum option has no useful effect,
and requests its removal. The active menu removes that entry and the item
OFF/99/increase/98 entries. The only retained item cheat is the standalone
`物品数量不减少（包括出售）`. Its body, the hotkey controller, player-edited
other descriptions and all retained effect bodies remain unchanged.
`tools/prune_cheat_menu.py` preserves retained lines and migrates the enabled
item name, dropping selections for removed entries. Prior experimental profiles
remain research inputs, not active menu choices. This is a menu removal, not a
claim that every retired candidate is independently proven defective.

Deleting patch sections does not restore instruction RAM already modified
in the running game. Cold boot after installation; do not load an old emulator
state to validate removal. Evidence and paired PNACH/INI rollback are recorded
in `build/cheat-menu-prune/VERIFICATION.txt`. Current grouped source stores the
trimmed menu; to regenerate from the full grouping generator, run the pruning
step afterward (with a separate output file).

## Money-gain restored for two-scenario comparison

The player later reported a balance of 1000000 after battle and requested the
money-gain entry back for shop versus battle testing. The menu now restores
`金钱获取（可独立启用）\获得金钱时设为1000000`, leaving only the standalone
item-count-preservation option. `prune_cheat_menu.py --restore-money --elf ...`
rebuilds this section from the exact version-locked original instruction and
conditional ON/OFF blocks. Other player-edited descriptions/bodies remain
unchanged. Evidence: `build/cheat-money-restore/VERIFICATION.txt`.

MakeMoney is the static binding; actual shop and battle call paths remain to
be tested. SpendMoney's increase-on-spend modification is a different hook.
Use a pre-test game save with balance below 1000000. Turn all spending modes
off, cold boot between runs, and compare hotkey OFF versus ON from the same
save for shop buy, shop sell and battle reward separately. A balance already
at the cap cannot demonstrate the trigger. Hotkey OFF restores the instruction,
not money previously changed. Avoid loading a patched emulator save state.

## Maximum-HP-only menu entry retired

The player reports suspected 1-HP survival behavior with maximum-HP-only,
while reporting the other three HP modes and leadership functional. The
1-HP mechanism has not been independently established. At the player's
request, only `我方最大HP9999（查询时）` is removed from the active menu.
Other user-edited descriptions and patch bodies remain exact. Research
profiles/tests keep the prior implementation for traceability, not as an
active option. `prune_cheat_menu.py --remove-section` reproduces removal.
The current selection INI did not enable this section and was left unchanged.
Evidence: `build/cheat-hp-max-remove/VERIFICATION.txt`. Cold boot after removal;
removing a section does not revert patched RAM or existing character values.
