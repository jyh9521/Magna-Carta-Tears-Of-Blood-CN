"""Arrange the validated Korean hotkey variant into native PCSX2 tree groups."""
import argparse
import hashlib
from pathlib import Path
import build_hotkey_cheats as hotkey

ROOT = Path(__file__).resolve().parents[1]
SPEND = '消费（下方最多启用1项）'
ITEM = '物品（下方最多启用1项）'
HP = '战斗生命值（下方最多启用1项）'
CONTROL = '内部控制（请勿手动选择或取消）\\快捷键控制（已自动启用，请保持勾选）'
HINT = '快捷键提示：SELECT＋上开启作弊，SELECT＋下关闭作弊'
NAMES = {
    '消费不扣钱': SPEND + '\\不扣钱',
    '消费反加钱': SPEND + '\\反加钱',
    '钱不够也可消费且不扣钱': SPEND + '\\钱不够也能消费',
    '获得金钱时设为最大值': '金钱获取（可独立启用）\\获得金钱时设为1000000',
    '使用物品不减少': ITEM + '\\数量不减少（包括出售）',
    '使用物品后数量99': ITEM + '\\使用后数量99',
    '使用物品反增加': ITEM + '\\使用后数量增加',
    '使用物品后数量98': ITEM + '\\使用后数量98',
    '战斗：我方最大HP9999（查询时）': HP + '\\我方最大HP9999（查询时）',
    '战斗：我方HP恢复9999（查询时）': HP + '\\我方HP恢复9999（查询时）',
    '战斗：存活敌人HP降至1（查询时）': HP + '\\敌人HP降至1（查询时）',
    '战斗：我方恢复9999＋敌人HP1': HP + '\\我方恢复9999＋敌人HP1',
    '战斗：我方领导力100（查询时）': '战斗其他（可独立启用）\\我方领导力100（查询时）',
}
FAMILIES = {
    SPEND: list(NAMES)[:3],
    ITEM: ['使用物品不减少', '使用物品后数量99', '使用物品反增加', '使用物品后数量98'],
    HP: ['战斗：我方最大HP9999（查询时）', '战斗：我方HP恢复9999（查询时）',
         '战斗：存活敌人HP降至1（查询时）', '战斗：我方恢复9999＋敌人HP1'],
}


def split_sections(text):
    header = []
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith('[') and line.endswith(']'):
            current = line[1:-1]
            if current in sections:
                raise ValueError('duplicate section')
            sections[current] = []
        elif current is None:
            header.append(line)
        else:
            sections[current].append(line)
    return header, sections


def migrate_selection_ini(text):
    """Rename only this variant's enabled names and enable its mandatory core."""
    aliases = dict(NAMES)
    aliases.update({
        '消费\\关闭': SPEND + '\\关闭',
        '消费\\不扣钱': NAMES['消费不扣钱'],
        '消费\\反加钱': NAMES['消费反加钱'],
        '消费\\钱不够也能消费': NAMES['钱不够也可消费且不扣钱'],
    })
    lines = text.splitlines()
    result = []
    inside = False
    found = False
    seen = set()
    def add_core():
        if CONTROL not in seen:
            result.append('Enable = ' + CONTROL)
            seen.add(CONTROL)
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            if inside:
                add_core()
            inside = stripped == '[Cheats]'
            found |= inside
        if inside and '=' in line and line.split('=', 1)[0].strip() == 'Enable':
            old = line.split('=', 1)[1].strip()
            name = aliases.get(old, old)
            if name not in seen:
                result.append('Enable = ' + name)
                seen.add(name)
        else:
            result.append(line)
    if not found:
        result.extend(['', '[Cheats]'])
    if inside or not found:
        add_core()
    return '\n'.join(result) + '\n'


def render(elf, source):
    profiles = hotkey.load_profiles()
    expected = hotkey.render(elf, profiles,
        (ROOT / 'src/patches/SCKA-20043_AE86E04C.pnach').read_text('utf8'))
    if source.splitlines() != expected.splitlines():
        raise ValueError('source is not the validated flat hotkey variant')
    original = hotkey.original_memory(elf, profiles)
    header, sections = split_sections(source)
    core = [line for line in header if line.startswith('patch=')]
    header = [line for line in header if not line.startswith('patch=')]
    assert len(core) == 64, 'unexpected controller command count'
    known = hotkey.cases(profiles)
    def off_body(family):
        restore = {}
        for label in FAMILIES[family]:
            restore.update(hotkey.restore_words(original, known[label]))
        return ['description=关闭本组修改；先取消同组其他项，再勾选关闭。仅恢复本组原指令，不恢复已改变的金钱、数量或HP数值。'] + [
            f'patch=1,EE,{va:08X},word,{word:08X}' for va, word in sorted(restore.items())]
    ordered = [('60 FPS', sections.pop('60 FPS')),
               (HINT, ['description=仅为操作说明；勾选本行没有效果。请预选需要的项目，SELECT＋上开启，SELECT＋下关闭；初始关闭。'])]
    for family in [SPEND, ITEM, HP]:
        ordered.append((family + '\\关闭', off_body(family)))
        for label in FAMILIES[family]:
            ordered.append((NAMES[label], sections.pop(label)))
        if family == SPEND:
            label = '获得金钱时设为最大值'
            ordered.append((NAMES[label], sections.pop(label)))
    for label, body in sections.items():
        ordered.append((NAMES.get(label, label), body))
    ordered.append((CONTROL, ['description=内部必需控制代码，已自动启用，请勿取消勾选。包含64条开关初始化、原始手柄读取和状态维护代码。取消后快捷键失效。'] + core))
    result = '\n'.join(header).rstrip() + '\n'
    for name, body in ordered:
        result += '\n[' + name + ']\n' + '\n'.join(body).strip() + '\n'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--elf', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in [args.elf.resolve(), args.source.resolve()]:
        raise ValueError('separate output required')
    text = render(args.elf.read_bytes(), args.source.read_text('utf8'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding='utf8')
    assert args.output.read_text('utf8') == text
    print('GROUP_BUILD PASS sections=19 families=3 controller_commands=64 unlabelled_commands=0 sha256=' +
          hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
