# NTSC-K gameplay cheat ports

Target: SCKA-20043 / AE86E04C. Original ELF fingerprint and size are the same
as [FRAME_LIMIT_PATCH.md](FRAME_LIMIT_PATCH.md). The original ISO and installed
PCSX2 cheats are untouched. This is a partial port, not completion of the whole
US or JP list. The generated file retains the earlier 60 FPS section.

## Sources

- US list supplied by the user: [PS2Home](https://www.ps2home.co.uk/cheats/ps2/magnacarta-tears-of-blood).
- Actual US code data: [root670/CheatDevicePS2 CheatDatabase.txt](https://github.com/root670/CheatDevicePS2/blob/master/CheatDatabase.txt), GPL-3.0 upstream attribution retained. Local downloaded input is in ignored `work/cheat-port`; no original game data is downloaded.
- JP reference supplied by the user: [Xterminator Extreme, マグナカルタ](https://xterminatorex.seesaa.net/category/6006620-2.html), article dated 2009-03-30. No redistribution license is stated there; the repository records brief code references and independently derived Korean changes, not a full page copy.

## Verified static mappings

Qualified native names are resolved via their inline PMF descriptor copies,
not guessed from nearby strings. `work/cheat-port/native-bindings.json` was
produced by `tools/audit_native_method_registration.py` against the original ELF.

| Effect / case | KR VA | Original word | Replacement | Evidence |
|---|---|---|---|---|
| spend_no_decrease | 003A0700 | AC620000 | 00000000 | SpendMoney store omitted |
| spend_increase | 003A06F8 | 00451023 | 00451021 | SpendMoney subtract v0,a1 becomes add |
| gain_max_money | 003A0E78 | 14200003 | 00000000 | MakeMoney upper-clamp skip removed |
| item_no_decrease | 0039FBB0 | AC620004 | 00000000 | RemoveItem count store omitted |
| item_count_99 | 0039FB98 | 00461023 | 24020063 | RemoveItem calculated count replaced by 99 |
| item_increase | 0039FB98 | 00461023 | 00461021 | RemoveItem subtract v0,a2 becomes add |
| spend_free | 003A06F0 | 14200004 | 10000005 | Jump to 003A0708, bypass subtraction/store and insufficient-funds result |
| item_count_98 | 0039FB98 | 00461023 | 24020062 | JP variant: calculated count replaced by 98 |

`SpendMoney` callback 003A0650 calls 003A06E0; original native function reads
PartyData+28, then money+7EC. Its signed comparison and negative-result path
are retained by the first two modes, so those modes still require enough money.
The free-spend mode bypasses the comparison result path and preserves the
current-money return rather than forcing an arbitrary success constant.

`MakeMoney` callback 003A0DC0 calls 003A0E50. The original comparison checks
against 1,000,001 and clamps to 1,000,000; removing its branch always takes the
clamp assignment. This is the Korean function's own cap, not the US absolute
99,999,999 memory-write code. Corrected cap: native LUI 000F / ORI 4240 = 1,000,000.

`RemoveItem` callback 0039FA90 calls 0039FB60. This searches 8-byte key/count
entries, subtracts the requested quantity, rejects a negative result, stores
count+4 and removes the record only when the stored count becomes zero.
The profile locks full source SHA-256 and exact surrounding instructions;
US register operands are not blindly copied (US spending uses v1; KR uses v0).

These are **verified offline instruction changes** and **high-confidence
functional deductions**, not measured gameplay outcomes. No US/JP ELF was
available for whole-function cross-region matching.

## Selecting modes and testing

Copy or merge the generated `build/gameplay-cheats/AE86E04C.pnach` into the
currently active game's cheat file through PCSX2 Edit Cheats. Do not replace
unrelated existing cheats. Keep the `.pnach` extension; enable the individual
section and the overall cheats switch. Cold-boot and load an in-game save.

- Select at most ONE of the three spending modes.
- Select at most ONE of the four item modes; 98/99/increase share an address.
- Start testing with 60 FPS disabled, to isolate gameplay-code effects.
- Preserve an in-game save before testing; money/inventory changes may be saved.
- Disable all item modes before equipping/removing weapons or armor. The JP
  author reports equipment hangs for its quantity code; this is an upstream
  report, not an independently reproduced Korean failure.
- Disable a section and cold-boot to restore code. Existing modified save data
  is not undone by a code rollback; reload the pre-test save for that.

Runtime checklist: buy with sufficient/insufficient funds; gain money after
battle; use last item and multi-quantity items; change equipment with modes OFF;
save/load and scene transitions. Observe money/inventory values and return
behavior. General native functions may also affect non-shop spending and
non-consumable item removal; no narrower scope is asserted.

## Reproducible tool

`tools/build_gameplay_cheats.py` supports baseline, apply, modified, rollback
and pnach modes. Region data is in `profiles/cheats/SCKA-20043_AE86E04C.json`.
Supply the original ELF extracted from the Korean ISO. Apply each case to a
separate copy; do not combine mutually exclusive cases into one ELF.

```powershell
python tools/build_gameplay_cheats.py baseline --profile profiles/cheats/SCKA-20043_AE86E04C.json --input work/kr/SCKA_200.43
python tools/build_gameplay_cheats.py apply --profile profiles/cheats/SCKA-20043_AE86E04C.json --input work/kr/SCKA_200.43 --case spend_free --output build/gameplay-cheats/spend_free.elf
python tools/build_gameplay_cheats.py modified --profile profiles/cheats/SCKA-20043_AE86E04C.json --input build/gameplay-cheats/spend_free.elf --case spend_free
python tools/build_gameplay_cheats.py rollback --profile profiles/cheats/SCKA-20043_AE86E04C.json --input build/gameplay-cheats/spend_free.elf --case spend_free --output build/gameplay-cheats/spend_free.restored.elf
python -m unittest discover -s tests -p test_gameplay_cheats.py -v
```

Local `build/gameplay-cheats/VERIFICATION.txt` records exact commands, inputs,
literal outputs and exit statuses. Eight individual modified-ELF checks and
eight isolated rollback copies passed, all restored byte-identical to source.
Eight unit tests and 24 rejection cases passed. The PNACH rollback script was
executed on a separate copy and restored the original 60 FPS-only content.
`MODIFIED_FILE` remains changed, with `DIFF_FILE` and executable `ROLLBACK.sh`.
No runtime or save rollback acceptance is claimed.

## Still unported

Selected HP/enemy-HP/friendly-leadership battle candidates are now generated;
their separate proof and runtime limits are in [BATTLE_CHEAT_PORT.md](BATTLE_CHEAT_PORT.md).
The US absolute record/time/money RAM writes, all-talismans code, original battle
activation, enemy leadership, menu stat and level injections remain unverified
and are not in the PNACH. US master activation code is cheat-device
infrastructure, not a normal PCSX2 gameplay write; it is not copied into PNACH.
JP controller-button address, enemy-wipe and rest/stat modifications also
remain unverified. JP input-address differences are not used to infer a Korean
address delta. Further work can continue from Korean native data flow without
requiring a US ISO, but each injected function/return target and field needs
its own evidence.
