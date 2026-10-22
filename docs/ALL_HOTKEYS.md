# Shared SELECT switch for every active effect

## Current installed behavior

All 14 active effect choices now share the existing controller latch:

- SELECT + D-pad Up: latch ON for currently selected effects.
- SELECT + D-pad Down: latch OFF for currently selected effects.
- Button release retains the latch. Both direction chords together resolve OFF.
- A fresh boot starts OFF. Invalid primary-controller packets/read reset OFF.
- Unselected effects do not apply. Money/HP alternatives and battle 2x/4x
  remain mutually exclusive choices; select at most one in each family.

The 14 effects are 60 FPS, three spending choices, gain-money cap, item quantity
preservation, three HP choices, friendly leadership, enemy-undetected, battle
2x/4x and first-input-started auto-QTE. The hint row and two explicit family
OFF rows are not positive cheats. OFF rows restore their family's original
instructions; the mandatory internal controller remains active to receive the
next ON chord. Do not try to gate the controller itself with its own latch.

The actual installed same-CRC PNACH was changed directly. All existing section
names/order and UI selection settings were preserved; no INI, emulator binary,
ISO or original ELF was written. Reload cheats, then cold-boot once before testing.
Keep the cheats master enabled and the internal controller child checked.
Use SELECT-Down before changing selection or disabling the master, and cold-boot
after changing selections/removing patches. Loading an old emulator save state
can reintroduce prior instructions/latches and is not a cold-boot test.

SELECT-Down does not undo money/items/HP already changed, stored QTE results,
or save data. It restores stateless code and releases an owned speed coefficient.

## Changes from the prior installed file

The prior menu had ten gated effects and four independent effects. Its controller
and earlier conditional instruction bodies are retained. The enemy-undetected
and QTE rows now have exact-count E-code ON blocks followed by original-byte OFF
blocks, using the existing latch at `000C3FE0`:

| Effect | Original restored on OFF |
|---|---|
| Enemy discovery bypass | original words at 003F72C0/003F72C4/003F746C/003F7470 |
| Auto-QTE | 002F8B8C restored from 24020001 to 000217FE |

`tools/unify_cheat_hotkeys.py` accepts only recognized profile-derived instruction
maps, exact original OFF maps, exact controller core and explicit original-only
restore controls. Unknown writes, malformed E counts, duplicate sections/writes,
or guessed restoration fail. The original ELF is checked by complete fingerprint,
native anchors and the existing input/gameplay/battle/field/QTE validators.

## Why speed needs a runtime OFF path

Simply restoring the Tick hook leaves the previously written owner `+023C` speed
coefficient in memory. Therefore the selected speed option retains its maintenance
hook at `003FE208/003FE20C` and code at `000C4000` in both ON and OFF states.
This is not an ungated speed effect: the emitted code reads the full shared latch
and scales only when it equals 1 and current mode `+024B` equals 2.

With no captured owner, OFF does not capture or write a coefficient. For a captured
same owner, OFF takes the release path even while current mode remains 2. It
restores the saved base only when the current speed still equals its own last
write, then clears ownership at `000C43F0`. If another subsystem supplied a new
value, that value remains unchanged. Owner changes never dereference a saved old
pointer. Corrupt/non-1 latch values also take the OFF path. The existing pointer,
positive float range, full-width scratch save/restore and displaced instruction
replay checks remain intact. Code/state do not overlap existing caves.

Restoration occurs on the next native GameMagi Tick, not by asynchronously writing
a guessed absolute heap address. The speed 2x and 4x options still share one code
cave and must not both be selected.

## Reproduce and verify

Current canonical complete source:
`src/patches/SCKA-20043_AE86E04C-all-hotkeys.pnach`.
The standalone field/QTE files are component research outputs, not an alternative
all-hotkey installation. Run the unifier after merging them into a complete menu.
The unified source itself rebuilds idempotently:

```powershell
work/venv/Scripts/python.exe -X utf8 tools/unify_cheat_hotkeys.py --elf work/kr/SCKA_200.43 --source src/patches/SCKA-20043_AE86E04C-all-hotkeys.pnach --output build/all-hotkeys-install/reproduced.pnach --audit-output build/all-hotkeys-install/reproduced-sections.json
work/venv/Scripts/python.exe -X utf8 tools/verify_all_hotkeys.py modified --elf work/kr/SCKA_200.43 --source src/patches/SCKA-20043_AE86E04C-all-hotkeys.pnach --pnach build/all-hotkeys-install/reproduced.pnach
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p '*cheat*.py' -v
```

**Verified offline:** 14 active effects, zero ungated effects, all 84 individual
ON/release/OFF/release/ON/OFF transitions; unselected effects untouched; actual
generated speed maintenance words restore the captured base while still in battle;
default OFF, external-value preservation, slow-motion base, non-compounding,
owner changes, invalid latch and full register/FPU preservation. Fourteen new
all-hotkey tests plus the prior 96 cheat tests pass (110 total). These are bounded
PNACH/instruction models, not physical controller/game execution.

The executable `build/all-hotkeys-install/ROLLBACK.sh` was tested on a separate
candidate copy and restores the exact previous PNACH, including its previous
four independent effects. The actual installed PNACH remains changed. Old/new
hashes, four artifact paths, exact commands, literal outputs/exits, diff and
rollback evidence are in `build/all-hotkeys-install/VERIFICATION.txt`.

**Runtime acceptance pending for this unified revision:** SELECT transitions
with enemy-undetected, normal/counter/combo QTE, mid-battle 2x/4x OFF, subsequent
ON, cutscene speed ownership, frame limiter interaction, menu/field and scene
transitions. Prior user reports that undetected and speed work apply to the older
independent effects, not proof of this new hotkey behavior.
