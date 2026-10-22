"""Remove retired Korean cheat menu entries while preserving retained bodies."""
import argparse
from pathlib import Path
import build_grouped_cheats as groups
import build_hotkey_cheats as hotkey

KEEP_ITEM = groups.ITEM + '\\数量不减少（包括出售）'
ITEM_NAME = '物品数量不减少（包括出售）'
REMOVED = {
    '金钱获取（可独立启用）\\获得金钱时设为1000000',
    groups.ITEM + '\\关闭',
    groups.ITEM + '\\使用后数量99',
    groups.ITEM + '\\使用后数量增加',
    groups.ITEM + '\\使用后数量98',
}
MONEY_NAME = '金钱获取（可独立启用）\\获得金钱时设为1000000'


def remove_named_section(text, name):
    """Remove exactly one named section, preserving every other section body."""
    _, sections = groups.split_sections(text)
    if name not in sections:
        raise ValueError('requested section not found')
    result = []
    keep = True
    for line in text.splitlines():
        if line.startswith('[') and line.endswith(']'):
            keep = line[1:-1] != name
        if keep:
            result.append(line)
    return '\n'.join(result) + '\n'


def restore_money_gain(text, elf):
    """Restore the original version-locked conditional money-gain effect."""
    _, sections = groups.split_sections(text)
    if MONEY_NAME in sections or ITEM_NAME not in sections:
        raise ValueError('expected pruned menu without money-gain entry')
    profiles = hotkey.load_profiles()
    original = hotkey.original_memory(elf, profiles)
    writes = hotkey.cases(profiles)['获得金钱时设为最大值']
    body = [
        '[' + MONEY_NAME + ']',
        'description=获得金钱时设为1000000；商店交易与战斗结算的触发场景待实测。不由消费反加钱触发。SELECT＋上开启，SELECT＋下关闭；不会恢复已改变的余额。',
        '// gain_max_money; original 14200003; intUMrtsPartyDataexecMakeMoney',
        *hotkey.blocks(profiles[0], writes, hotkey.restore_words(original, writes)),
        '',
    ]
    marker = '[' + ITEM_NAME + ']'
    return text.replace(marker, '\n'.join(body) + '\n' + marker, 1)


def prune_pnach(text):
    _, sections = groups.split_sections(text)
    if KEEP_ITEM not in sections or not REMOVED.issubset(sections):
        raise ValueError('expected full grouped menu before pruning')
    result = []
    keep = True
    for line in text.splitlines():
        if line.startswith('[') and line.endswith(']'):
            name = line[1:-1]
            keep = name not in REMOVED
            if name == KEEP_ITEM:
                line = '[' + ITEM_NAME + ']'
        if keep:
            result.append(line)
    return '\n'.join(result) + '\n'


def prune_ini(text):
    result = []
    inside = False
    for line in text.splitlines():
        if line.startswith('[') and line.endswith(']'):
            inside = line == '[Cheats]'
        if inside and '=' in line and line.split('=', 1)[0].strip() == 'Enable':
            name = line.split('=', 1)[1].strip()
            if name in REMOVED:
                continue
            if name == KEEP_ITEM:
                line = 'Enable = ' + ITEM_NAME
        result.append(line)
    return '\n'.join(result) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--restore-money', action='store_true')
    parser.add_argument('--elf', type=Path)
    parser.add_argument('--remove-section')
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise ValueError('separate output required')
    if args.remove_section:
        if args.restore_money:
            raise ValueError('choose only one transformation')
        text = remove_named_section(args.source.read_text('utf8'), args.remove_section)
    elif args.restore_money:
        if args.elf is None or args.output.resolve() == args.elf.resolve():
            raise ValueError('separate original ELF required for restoration')
        text = restore_money_gain(args.source.read_text('utf8'), args.elf.read_bytes())
    else:
        text = prune_pnach(args.source.read_text('utf8'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding='utf8')
    assert args.output.read_text('utf8') == text
    print('REMOVE_BUILD PASS removed_sections=1' if args.remove_section else
          'RESTORE_BUILD PASS added=money_gain sections=15' if args.restore_money else
          'PRUNE_BUILD PASS removed=5 item_group_removed=true retained_sections=14')


if __name__ == '__main__':
    main()
