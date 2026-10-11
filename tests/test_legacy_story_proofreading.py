"""Source-bound legacy dialogue corrections, not automatic draft promotion."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LegacyStoryProofreadingTests(unittest.TestCase):
    def setUp(self):
        rows = json.loads((ROOT / 'locales/zh-CN/story-review-01.json').read_text('utf8'))['entries']
        self.rows = {row['id']: row for row in rows}

    def row(self, resource, seq):
        return self.rows[f'SHIP/{resource:08d}.fpb/seq/{seq}']

    def test_twenty_two_source_reviewed_scene_groups(self):
        counts = {1953: 11, 1954: 13, 1955: 9, 1956: 14, 1957: 2,
                  1958: 7, 1959: 10, 1960: 8, 1963: 12, 1964: 17,
                  1965: 25, 1969: 4, 1970: 13, 1972: 8, 1973: 13,
                  1977: 2, 1983: 9, 1984: 18, 1985: 7, 1986: 23,
                  1987: 12, 1988: 3}
        self.assertEqual(240, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            entries = [row for key, row in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(entries))
            self.assertTrue(all(row['status'] == 'reviewed' for row in entries))
            self.assertTrue(all(len(row['source_sha256']) == 64 for row in entries))

    def test_general_title_stays_whole_and_controls_remain(self):
        target = self.row(1956, 7)['target']
        self.assertIn('黄金雄狮', target)
        self.assertNotIn('黄金$n雄狮', target)
        self.assertEqual(3, target.count('$n'))
        self.assertIn('他深得吉拉特盟主', target)

    def test_familiar_and_unidentified_messenger_no_unproven_gender(self):
        for resource, seq in [(1964, 1), (1986, 8), (1988, 6)]:
            self.assertNotIn('他', self.row(resource, seq)['target'])
            self.assertNotIn('她', self.row(resource, seq)['target'])
        self.assertIn('那家伙', self.row(1964, 1)['target'])
        self.assertIn('拉埃杜山', self.row(1986, 8)['target'])

    def test_diary_roles_and_distinct_female_names(self):
        self.assertIn('日记主人', self.row(1970, 2)['target'])
        self.assertIn('阿莉安', self.row(1970, 9)['target'])
        self.assertNotIn('莉安娜', self.row(1970, 9)['target'])
        self.assertIn('莉安娜', self.row(1984, 8)['target'])
        self.assertIn('丈夫', self.row(1984, 8)['target'])
        self.assertIn('女人', self.row(1970, 13)['target'])
        self.assertIn('碧流·艾斯克拉诺', self.row(1970, 13)['target'])

    def test_lise_and_queen_use_female_pronouns_in_context(self):
        for seq in (5, 6):
            self.assertIn('她', self.row(1958, seq)['target'])
        for seq in (3, 4):
            self.assertIn('她', self.row(1984, seq)['target'])
        self.assertIn('蕾哈丝', self.row(1987, 22)['target'])
        self.assertIn('她', self.row(1987, 22)['target'])

    def test_revenge_claim_and_journal_fragments_not_flattened(self):
        self.assertIn('恐怕', self.row(1973, 4)['target'])
        self.assertIn('因为我', self.row(1973, 10)['target'])
        self.assertIn('……', self.row(1970, 12)['target'])
        self.assertIn('XX月XX日', self.row(1970, 9)['target'])
        self.assertEqual(6, self.row(1970, 9)['target'].count('$n'))
        self.assertEqual(3, self.row(1970, 13)['target'].count('$n'))

    def test_glossary_is_one_continuous_term_table(self):
        lines = (ROOT / 'GLOSSARY.md').read_text('utf8').splitlines()
        rows = []
        for index, line in enumerate(lines):
            parts = line.split('|')
            if len(parts) == 7 and parts[4].strip() in ('已统一', '暂定统一'):
                rows.append(index)
        self.assertGreaterEqual(len(rows), 1651)
        self.assertEqual(list(range(rows[0], rows[-1] + 1)), rows)
        self.assertIn('| 황금의 사자 | 黄金雄狮 |', '\n'.join(lines))
        self.assertGreater(lines.index('## 人物性别与第三人称校对基准'), rows[-1])

    def test_following_thirty_three_scene_groups_are_reviewed(self):
        counts = {1989: 12, 1990: 19, 2102: 8, 2118: 9, 2119: 3,
                  2120: 2, 2122: 10, 2123: 4, 2124: 19, 2125: 10,
                  2126: 20, 2127: 19, 2128: 8, 2129: 1, 2130: 6,
                  2131: 5, 2132: 5, 2133: 6, 2134: 3, 2135: 2,
                  2136: 8, 2137: 7, 2138: 7, 2139: 6, 2140: 29,
                  2141: 5, 2142: 3, 2143: 10, 2144: 10, 2145: 9,
                  2146: 15, 2147: 6, 2148: 8}
        self.assertEqual(294, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            entries = [row for key, row in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(entries))
            self.assertTrue(all(row['status'] == 'reviewed' for row in entries))

    def test_same_general_title_alias_is_unified(self):
        for resource, seq in [(1956, 7), (2137, 0)]:
            self.assertIn('黄金雄狮', self.row(resource, seq)['target'])
            self.assertNotIn('黄金狮子', self.row(resource, seq)['target'])
        self.assertEqual(4, self.row(2137, 0)['target'].count('$n'))

    def test_hagon_battle_and_aircraft_revisions_stay_distinct(self):
        self.assertIn('哈贡战役', self.row(1990, 6)['target'])
        self.assertIn('克里斯大帝二十二世', self.row(2124, 0)['target'])
        self.assertIn('克里斯大帝二十三世', self.row(2220, 1)['target'])
        self.assertNotIn('二十三世', self.row(2124, 0)['target'])

    def test_unknown_prisoner_gender_not_added(self):
        for resource, seq in [(2133, 3), (2140, 19), (2146, 4), (2146, 6)]:
            target = self.row(resource, seq)['target']
            self.assertNotIn('他', target)
            self.assertNotIn('她', target)

    def test_calinz_male_lise_female_pronouns_have_actual_referents(self):
        self.assertIn('她是我的救命恩人', self.row(2124, 8)['target'])
        self.assertIn('她', self.row(2140, 12)['target'])
        self.assertIn('他', self.row(2148, 2)['target'])
        self.assertIn('卡林兹', self.row(2148, 3)['target'])
        self.assertIn('阿泽尔', self.row(2144, 1)['target'])

    def test_opposed_revenge_statements_and_death_claim_remain(self):
        self.assertIn('不是所有亚逊都很坏', self.row(1990, 10)['target'])
        self.assertIn('所有亚逊都该死', self.row(2146, 9)['target'])
        self.assertIn('当然', self.row(2146, 10)['target'])
        self.assertIn('干掉', self.row(2146, 4)['target'])
        self.assertIn('谎', self.row(2148, 3)['target'])
        self.assertIn('战争会结束', self.row(2148, 7)['target'])

    def test_informant_secondary_assignment_preserves_order(self):
        target = self.row(2143, 5)['target']
        self.assertIn('尽可能把你救回来', target)
        self.assertIn('如果办不到', target)
        self.assertIn('就杀了你', target)
        self.assertLess(target.index('救回来'), target.index('杀了你'))
        self.assertEqual(4, target.count('$n'))

    def test_next_fifty_two_scene_groups_are_source_reviewed(self):
        counts = {2149: 14, 2150: 12, 2151: 8, 2152: 3, 2153: 11,
                  2154: 2, 2155: 13, 2156: 13, 2157: 9, 2161: 17,
                  2163: 9, 2165: 8, 2166: 11, 2167: 5, 2168: 5,
                  2169: 2, 2170: 3, 2171: 4, 2172: 9, 2173: 3,
                  2174: 10, 2175: 21, 2176: 4, 2177: 7, 2178: 5,
                  2179: 1, 2182: 3, 2184: 3, 2185: 2, 2186: 23,
                  2187: 11, 2190: 8, 2193: 17, 2194: 6, 2195: 6,
                  2196: 11, 2198: 30, 2199: 19, 2201: 7, 2204: 3,
                  2211: 13, 2213: 7, 2214: 1, 2215: 2, 2216: 10,
                  2217: 4, 2218: 10, 2219: 19, 2220: 16, 2221: 11,
                  2222: 8, 2223: 6}
        self.assertEqual(465, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            entries = [row for key, row in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(entries))
            self.assertTrue(all(row['status'] == 'reviewed' for row in entries))

    def test_complete_road_and_desert_names_not_split(self):
        target = self.row(2166, 0)['target']
        self.assertIn('吉拉特大道', target)
        self.assertNotIn('吉拉特$n大道', target)
        self.assertEqual(2, target.count('$n'))
        target = self.row(2218, 14)['target']
        self.assertIn('恩特雷斯沙漠', target)
        self.assertNotIn('恩特雷斯$n沙漠', target)
        self.assertEqual(2, target.count('$n'))

    def test_childhood_names_keep_their_display_forms(self):
        self.assertIn('玛诺', self.row(2196, 16)['target'])
        self.assertIn('休戈', self.row(2196, 18)['target'])
        self.assertIn('休戈', self.row(2219, 8)['target'])
        self.assertIn('玛诺', self.row(2219, 9)['target'])
        self.assertIn('拉德琳娜大人的儿子', self.row(2196, 23)['target'])
        reference = json.loads((ROOT / 'locales/zh-CN/character-reference.json').read_text('utf8'))
        characters = {row['canonical_source']: row for row in reference['characters']}
        for source, name in [('칼린츠', '마노'), ('아그레이언', '휴고')]:
            row = characters[source]
            self.assertEqual('male', row['gender'])
            entry = next(x for x in row['contextual_names'] if x['source'] == name)
            self.assertFalse(entry['automatic_substitution'])
            self.assertTrue(entry['source_ids_not_merged'])
            self.assertFalse(entry['runtime_cache_linking_verified'])
            self.assertTrue(all(key in self.rows for key in entry['evidence']))

    def test_phyllis_female_and_queen_woodification_distinct(self):
        self.assertIn('菲莉丝', self.row(2175, 5)['target'])
        self.assertIn('她', self.row(2175, 5)['target'])
        self.assertIn('她', self.row(2175, 6)['target'])
        self.assertIn('阿缪特病', self.row(2151, 1)['target'])
        self.assertIn('木化', self.row(2151, 2)['target'])
        self.assertNotIn('石化', self.row(2151, 2)['target'])

    def test_priestess_assumption_and_rejection_are_not_merged(self):
        self.assertIn('她是阿玛巴德的巫女', self.row(2157, 1)['target'])
        self.assertIn('并不是巫女', self.row(2186, 7)['target'])
        self.assertIn('我一直以为', self.row(2193, 6)['target'])
        self.assertIn('她不是巫女', self.row(2193, 8)['target'])
        self.assertIn('也许', self.row(2193, 5)['target'])

    def test_magic_legend_claims_and_doubt_stay_separate(self):
        self.assertIn('发动真名法典', self.row(2213, 2)['target'])
        self.assertIn('谣言', self.row(2218, 1)['target'])
        self.assertIn('不切实际的空想', self.row(2218, 2)['target'])
        self.assertEqual(4, self.row(2218, 2)['target'].count('$n'))
        self.assertIn('救赎之光', self.row(2198, 50)['target'])

    def test_coach_advice_not_mistranslated_as_travel(self):
        target = self.row(2219, 10)['target']
        self.assertIn('急于求成', target)
        self.assertNotIn('赶路', target)
        self.assertEqual(1, target.count('$n'))
        self.assertIn('师父', self.row(2219, 12)['target'])

    def test_aircraft_twenty_three_not_overwritten_with_twenty_two(self):
        self.assertIn('克里斯大帝二十三世', self.row(2220, 1)['target'])
        self.assertEqual(2, self.row(2220, 1)['target'].count('$n'))
        self.assertIn('克里斯大帝二十二世', self.row(2124, 0)['target'])


    def test_fifty_one_town_book_and_hero_groups_reviewed(self):
        counts = {2224: 20, 2225: 12, 2226: 1, 2227: 8, 2228: 8,
                  2229: 13, 2233: 11, 2526: 25, 2820: 22, 2832: 3,
                  2864: 14, 2890: 17, 3133: 17, 3449: 3, 3470: 4,
                  3479: 8, 3572: 53, 3622: 3, 3939: 11, 4505: 7,
                  4667: 9, 4668: 20, 4669: 19, 4671: 11, 4672: 8,
                  4673: 16, 5049: 11, 5173: 7, 5216: 3, 5372: 7,
                  4674: 3, 4675: 4, 4676: 4, 4698: 8, 4762: 9,
                  4800: 11, 4804: 2, 4855: 1, 4939: 4, 4985: 8,
                  4987: 2, 4994: 1, 4998: 4, 4999: 5, 5027: 6,
                  5033: 2, 5046: 3, 5047: 5, 5048: 4, 5051: 8, 5065: 6}
        self.assertEqual(471, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            entries = [row for key, row in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(entries))
            self.assertTrue(all(row['status'] == 'reviewed' for row in entries))

    def test_river_hero_not_steel_and_water_stays_distinct(self):
        for resource, seq in [(4669, 11), (5049, 6), (5051, 0)]:
            target = self.row(resource, seq)['target']
            self.assertIn('江之英雄', target)
            self.assertNotIn('钢之英雄', target)
        self.assertIn('水之英雄', self.row(4669, 12)['target'])
        glossary = (ROOT / 'GLOSSARY.md').read_text('utf8')
        self.assertIn('| 강의 영웅 | 江之英雄 |', glossary)

    def test_currency_term_distinct_from_person_and_values_retained(self):
        self.assertIn('10000希德币', self.row(4673, 10)['target'])
        self.assertIn('三千希德币', self.row(7685, 5)['target'])
        # Stage130 reviewed the complete resource; the price/source assertions remain.
        self.assertEqual('reviewed', self.row(7685, 5)['status'])
        glossary = (ROOT / 'GLOSSARY.md').read_text('utf8')
        self.assertIn('| 시드 | 希德币 |', glossary)
        self.assertIn('| 시드 에스타로트 | 席德·艾斯塔罗特 |', glossary)
        self.assertNotIn('埃尔德', self.row(4673, 10)['target'])

    def test_lise_aging_hypothesis_keeps_complete_phrase_and_scale(self):
        target = self.row(2225, 8)['target']
        self.assertIn('年龄退行', target)
        self.assertNotIn('年龄$n退行', target)
        self.assertIn('也许', target)
        self.assertEqual(1, target.count('$n'))
        self.assertIn('100', self.row(2225, 6)['target'])
        self.assertIn('10', self.row(2225, 6)['target'])
        self.assertIn('那些人明明就是亚逊', self.row(2228, 4)['target'])
        self.assertIn('解除了巫师们的变身', self.row(2228, 5)['target'])

    def test_memoir_fragment_and_estimation_not_recast_as_fact(self):
        self.assertTrue(self.row(4668, 19)['target'].endswith('，'))
        self.assertEqual(1, self.row(4668, 19)['target'].count('$n'))
        for resource, seq in [(4668, 18), (5051, 7)]:
            self.assertIn('我们不得不认为', self.row(resource, seq)['target'])
            self.assertNotIn('必然会被滥用', self.row(resource, seq)['target'])
        self.assertIn('约八年', self.row(5051, 6)['target'])
        for resource, seq in [(4668, 16), (5051, 11)]:
            self.assertIn('（此处中断）', self.row(resource, seq)['target'])
        self.assertNotIn('光之$n树', self.row(4668, 17)['target'])
        self.assertEqual(1, self.row(4668, 17)['target'].count('$n'))
        self.assertFalse(self.row(4669, 5)['target'].endswith('$n'))

    def test_hero_source_gender_and_male_disguise_do_not_change_gender(self):
        for resource, seq in [(4669, 20), (5049, 8)]:
            target = self.row(resource, seq)['target']
            self.assertIn('女战士', target)
            self.assertIn('她', target)
            self.assertIn('常被误认为男性', target)
        self.assertIn('少女', self.row(4669, 12)['target'])
        self.assertIn('她', self.row(4669, 12)['target'])
        for resource, seq in [(4669, 19), (5049, 9)]:
            self.assertIn('他', self.row(resource, seq)['target'])
            self.assertNotIn('渡海', self.row(resource, seq)['target'])
        self.assertIn('你要是个男人', self.row(2890, 14)['target'])

    def test_unknown_familiar_partner_homeowner_no_added_gender(self):
        for resource, seq in [(3572, 4), (3572, 15), (4505, 5), (4505, 6),
                              (5372, 5), (5372, 6), (5027, 1), (5047, 4), (5048, 3)]:
            target = self.row(resource, seq)['target']
            self.assertNotIn('他', target)
            self.assertNotIn('她', target)
        self.assertEqual('让奥尔哈进来。', self.row(5027, 1)['target'])
        self.assertIn('罗斯蒂28号', self.row(4999, 1)['target'])

    def test_tutorial_buttons_and_control_count_preserved(self):
        self.assertIn('R1', self.row(3939, 3)['target'])
        self.assertEqual(2, self.row(3939, 3)['target'].count('$n'))
        self.assertIn('○', self.row(3939, 6)['target'])
        self.assertEqual(3, self.row(3939, 6)['target'].count('$n'))
        target = self.row(3939, 8)['target']
        self.assertIn('□', target)
        self.assertIn('△', target)
        self.assertIn('HP', target)
        self.assertIn('不会恢复', target)
        self.assertEqual(8, target.count('$n'))


    def test_twenty_bracelet_tutorial_and_travel_groups_reviewed(self):
        counts = {5066: 12, 5140: 6, 5166: 8, 5167: 19, 5169: 17,
                  5182: 14, 5187: 4, 5197: 7, 5206: 15, 5213: 13,
                  5295: 4, 5296: 1, 5297: 2, 5298: 2, 5299: 2,
                  5300: 5, 5301: 1, 5302: 3, 5303: 2, 5304: 3}
        self.assertEqual(140, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            rows = [r for key, r in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(rows))
            self.assertTrue(all(r['status'] == 'reviewed' for r in rows))

    def test_bracelet_testimony_keeps_birth_hypothesis_and_complete_words(self):
        self.assertIn('席德·艾斯塔罗特', self.row(5167, 8)['target'])
        self.assertIn('说不定', self.row(5167, 10)['target'])
        self.assertIn('他的儿子', self.row(5167, 10)['target'])
        self.assertIn('感慨万千', self.row(5167, 15)['target'])
        self.assertNotIn('万$n千', self.row(5167, 15)['target'])
        self.assertEqual(1, self.row(5167, 15)['target'].count('$n'))
        self.assertIn('恐怕', self.row(5167, 13)['target'])

    def test_hugo_agreian_forms_and_butterfly_mark_preserved(self):
        target = self.row(5169, 6)['target']
        self.assertIn('休戈', target)
        self.assertIn('阿格雷安', target)
        self.assertIn('发动真名法典', self.row(5169, 7)['target'])
        self.assertIn('瞒着母亲', self.row(5169, 10)['target'])
        self.assertIn('黑色蝴蝶形宾迪', self.row(5169, 14)['target'])
        self.assertEqual(1, self.row(5169, 14)['target'].count('$n'))
        self.assertNotIn('他', self.row(5182, 4)['target'])

    def test_star_candy_currency_and_mutually_exclusive_choices_remain(self):
        for seq in [7, 13]:
            self.assertIn('300希德币', self.row(5206, seq)['target'])
            self.assertNotIn('300Sid', self.row(5206, seq)['target'])
        self.assertIn('给你', self.row(5206, 2)['target'])
        self.assertIn('不能给', self.row(5206, 3)['target'])
        self.assertIn('钱不够', self.row(5206, 14)['target'])
        self.assertIn('| 300Sid | 300希德币 |', (ROOT / 'GLOSSARY.md').read_text('utf8'))

    def test_style_quantities_and_buttons_without_added_kahn_types(self):
        target = self.row(5213, 3)['target']
        self.assertIn('三至七个卡恩', target)
        self.assertNotIn('七种卡恩', target)
        self.assertEqual(2, target.count('$n'))
        self.assertIn('SELECT', self.row(5213, 2)['target'])
        self.assertIn('DEF', self.row(5213, 8)['target'])
        self.assertIn('五级防护盾', self.row(5213, 8)['target'])
        self.assertIn('没有“罗刹”和“夜叉”', self.row(5213, 12)['target'])
        self.assertNotIn('$n吧', self.row(5300, 0)['target'])


    def test_thirty_two_queen_memoir_and_decoy_groups_reviewed(self):
        counts = {5350: 2, 5351: 3, 5352: 2, 5373: 11, 5374: 7,
                  5375: 7, 5377: 8, 5378: 11, 5390: 13, 5389: 16,
                  5391: 1, 5393: 6, 5500: 1, 5556: 7, 5557: 5,
                  5560: 3, 5613: 12, 5614: 4, 5615: 11, 5617: 25,
                  5618: 14, 5619: 3, 5620: 3, 5621: 8, 5622: 5,
                  5623: 2, 5624: 2, 5625: 1, 5626: 2, 5627: 1,
                  5628: 12, 5629: 31}
        self.assertEqual(239, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            rows = [r for key, r in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(rows))
            self.assertTrue(all(r['status'] == 'reviewed' for r in rows))

    def test_queen_and_frost_wyrm_disagree_without_normalizing_opinions(self):
        self.assertIn('可能', self.row(5373, 6)['target'])
        self.assertIn('绝不会让霜龙受到冷落', self.row(5373, 8)['target'])
        self.assertIn('逐步克服阿缪特病', self.row(5390, 6)['target'])
        self.assertIn('只要别让阿米拉得到', self.row(5390, 12)['target'])
        self.assertIn('复苏', self.row(5374, 5)['target'])

    def test_memoir_female_arian_and_isha_parenthetical_doubt(self):
        target = self.row(5389, 15)['target']
        self.assertIn('阿莉安', target)
        self.assertIn('她', target)
        self.assertIn('身为他恋人的阿莉安', target)
        target = self.row(5389, 10)['target']
        self.assertIn('（我想他大概', target)
        self.assertIn('有意推动', self.row(5389, 11)['target'])
        self.assertIn('似乎', self.row(5389, 8)['target'])
        self.assertIn('十个月以上', self.row(5389, 13)['target'])
        self.assertIn('三十多年', self.row(5389, 14)['target'])

    def test_prayer_decoy_order_and_mothers_opposition_remain(self):
        self.assertIn('我反对', self.row(5613, 0)['target'])
        self.assertIn('母亲', self.row(5613, 10)['target'])
        self.assertIn('大巫女替身', self.row(5617, 8)['target'])
        self.assertIn('朱斯蒂娜', self.row(5617, 23)['target'])
        self.assertIn('绑架大巫女', self.row(5618, 3)['target'])
        self.assertIn('凯莉安', self.row(5618, 4)['target'])
        self.assertIn('阿萨德', self.row(5618, 5)['target'])
        self.assertIn('罗茜', self.row(5618, 8)['target'])

    def test_disguise_viewpoint_and_rauls_explicit_male_context(self):
        self.assertEqual('奇怪，在我看来，他们都是不同的人。', self.row(5628, 2)['target'])
        self.assertIn('男人', self.row(5629, 9)['target'])
        self.assertIn('他', self.row(5629, 22)['target'])
        self.assertIn('劳尔', self.row(5629, 31)['target'])
        self.assertIn('他', self.row(5629, 26)['target'])
        self.assertIn('莉丝', self.row(5629, 21)['target'])

    def test_source_controls_do_not_split_clauses_and_names(self):
        for resource, seq, count in [(5373, 6, 1), (5374, 3, 2),
                                      (5390, 4, 2), (5556, 4, 2),
                                      (5615, 0, 1), (5629, 6, 1), (5629, 18, 2)]:
            target = self.row(resource, seq)['target']
            self.assertEqual(count, target.count('$n'))
            for bad in ['光之$n树', '命运$n', '欺负$n人', '吞下$n去', '更$n好了']:
                self.assertNotIn(bad, target)
        self.assertIn('自然恢复', self.row(5377, 5)['target'])
        self.assertEqual(3, self.row(5377, 5)['target'].count('$n'))
        self.assertIn('一两个月', self.row(5377, 4)['target'])


    def test_twenty_priestess_birthday_and_headquarters_groups_reviewed(self):
        counts = {5630: 8, 5631: 27, 5632: 11, 5634: 17, 5635: 9,
                  5636: 12, 5640: 5, 5641: 8, 5642: 16, 5643: 15,
                  5644: 3, 5645: 4, 5646: 6, 5647: 16, 5648: 9,
                  5420: 24, 5421: 7, 5649: 12, 5650: 10, 5651: 10}
        self.assertEqual(229, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            rows = [r for key, r in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(rows))
            self.assertTrue(all(r['status'] == 'reviewed' for r in rows))

    def test_real_priestess_reveal_does_not_replace_earlier_deception(self):
        self.assertIn('在雷斯蒂', self.row(5630, 6)['target'])
        self.assertIn('拉德琳娜', self.row(5631, 10)['target'])
        self.assertIn('欺骗了各位', self.row(5631, 13)['target'])
        self.assertIn('似乎有间谍', self.row(5632, 4)['target'])
        self.assertIn('24小时', self.row(5634, 15)['target'])
        self.assertIn('劳尔', self.row(5634, 3)['target'])

    def test_familiar_control_is_negative_question_and_conditional_claim(self):
        self.assertIn('该不会', self.row(5636, 1)['target'])
        self.assertTrue(self.row(5636, 1)['target'].endswith('吧？'))
        self.assertIn('如果真是这样', self.row(5636, 3)['target'])
        self.assertIn('我以为', self.row(5647, 14)['target'])
        self.assertIn('水之英雄', self.row(5641, 3)['target'])
        self.assertIn('只是推测', self.row(5641, 1)['target'])

    def test_japanese_faction_name_and_female_carian_preserved(self):
        for seq in [10, 19]:
            target = self.row(5420, seq)['target']
            self.assertIn('血泪', target)
            self.assertNotIn('赤色旋风', target)
        self.assertIn('女人', self.row(5420, 18)['target'])
        self.assertIn('凯莉安', self.row(5420, 17)['target'])
        self.assertNotIn('他', self.row(5420, 14)['target'])
        glossary = (ROOT / 'GLOSSARY.md').read_text('utf8')
        self.assertIn('| 뛤궻먿븮 | 血泪 |', glossary)
        self.assertIn('明确女，女性她', glossary)

    def test_rehas_final_birthday_and_gendered_later_testimony(self):
        self.assertIn('生日快乐', self.row(5649, 10)['target'])
        self.assertIn('蕾哈丝', self.row(5649, 0)['target'])
        self.assertIn('同伴们的墓前', self.row(5649, 6)['target'])
        self.assertIn('她', self.row(5651, 2)['target'])
        self.assertIn('她', self.row(5651, 3)['target'])
        self.assertIn('失忆', self.row(5650, 3)['target'])
        self.assertIn('阿泽尔', self.row(5650, 9)['target'])

    def test_complete_phrases_and_source_controls_in_headquarters_story(self):
        for resource, seq, count in [(5630, 3, 2), (5631, 10, 2),
                                      (5634, 10, 1), (5635, 4, 1),
                                      (5642, 10, 1), (5420, 38, 1), (5420, 39, 2)]:
            target = self.row(resource, seq)['target']
            self.assertEqual(count, target.count('$n'))
            for bad in ['可疑的$n人', '告诉莉丝$n一声', '故居$n吗', '压制$n使魔', '自家$n一样']:
                self.assertNotIn(bad, target)
        self.assertIn('克雷·巴斯特', self.row(5647, 9)['target'])
        self.assertIn('哈贡战役', self.row(5647, 10)['target'])
        self.assertIn('席本队长', self.row(5647, 13)['target'])


    def test_twenty_seven_birthday_mourning_and_lianna_groups_reviewed(self):
        counts = {5652: 29, 5653: 29, 5654: 12, 5655: 1, 5656: 7,
                  5657: 4, 5658: 2, 5659: 5, 5660: 4, 5661: 2,
                  5662: 12, 5663: 13, 5664: 1, 5665: 3, 5666: 24,
                  5667: 4, 5668: 2, 5669: 10, 5671: 6, 5672: 3,
                  5673: 7, 5674: 11, 5676: 2, 5677: 6, 5679: 4,
                  5680: 17, 5681: 3}
        self.assertEqual(223, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            rows = [r for key, r in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(rows))
            self.assertTrue(all(r['status'] == 'reviewed' for r in rows))

    def test_lianna_husband_is_male_and_mixed_race_remains_assumption(self):
        self.assertIn('丈夫', self.row(5666, 11)['target'])
        self.assertIn('骗人的', self.row(5666, 11)['target'])
        self.assertIn('他走之前', self.row(5666, 13)['target'])
        self.assertIn('他大概是混血', self.row(5666, 20)['target'])
        self.assertIn('我也不讨厌他', self.row(5666, 21)['target'])
        self.assertIn('不管是亚逊还是人类', self.row(5666, 21)['target'])
        self.assertIn('丈夫', self.row(5652, 5)['target'])
        self.assertIn('他', self.row(5652, 6)['target'])

    def test_rehas_birthday_preparation_and_funeral_not_rewritten(self):
        self.assertIn('蕾哈丝', self.row(5653, 1)['target'])
        self.assertIn('卡林兹的生日', self.row(5653, 2)['target'])
        self.assertIn('卡林兹先吃', self.row(5653, 16)['target'])
        self.assertIn('说不定', self.row(5653, 17)['target'])
        self.assertIn('死了', self.row(5662, 8)['target'])
        self.assertIn('蕾哈丝的葬礼', self.row(5680, 1)['target'])
        self.assertIn('她', self.row(5680, 4)['target'])

    def test_blame_and_reassurance_keep_opposed_speaker_positions(self):
        self.assertIn('不是你的错', self.row(5662, 11)['target'])
        self.assertIn('因为我', self.row(5663, 7)['target'])
        self.assertIn('都是因为你', self.row(5663, 8)['target'])
        self.assertIn('不觉得莉丝帮助亚逊是错的', self.row(5666, 6)['target'])
        self.assertIn('不必独自感到愧疚', self.row(5666, 6)['target'])
        self.assertIn('大概只是', self.row(5662, 2)['target'])

    def test_half_yason_correction_and_familiar_mystery_stay_distinct(self):
        self.assertIn('不，是半亚逊', self.row(5663, 9)['target'])
        self.assertEqual(1, self.row(5663, 9)['target'].count('$n'))
        self.assertIn('没有宾迪', self.row(5663, 10)['target'])
        self.assertIn('钢铁之心', self.row(5673, 4)['target'])
        self.assertIn('特殊剑术', self.row(5674, 6)['target'])
        self.assertIn('负担', self.row(5674, 6)['target'])
        self.assertIn('为什么没有攻击我们', self.row(5674, 9)['target'])
        self.assertNotIn('他', self.row(5667, 1)['target'])

    def test_clause_controls_preserved_and_separate_race_options_remain(self):
        for resource, seq, count in [(5652, 7, 1), (5653, 25, 1),
                                      (5654, 11, 1), (5666, 6, 1),
                                      (5666, 11, 2), (5666, 21, 1), (5668, 1, 2)]:
            target = self.row(resource, seq)['target']
            self.assertEqual(count, target.count('$n'))
            for bad in ['是$n错的', '补偿$n', '不会$n使用', '莉丝的$n心情']:
                self.assertNotIn(bad, target)
        self.assertIn('活捉', self.row(5680, 7)['target'])
        self.assertIn('不同的派系', self.row(5680, 8)['target'])
        self.assertIn('阿泽翼', self.row(5680, 15)['target'])


    def test_twenty_one_water_hero_arrest_and_responsibility_groups_reviewed(self):
        counts = {5682: 20, 5683: 31, 5684: 11, 5685: 2, 5686: 21,
                  5687: 16, 5688: 12, 5689: 2, 5690: 2, 5691: 8,
                  5692: 5, 5693: 5, 5694: 12, 5695: 13, 6066: 7,
                  6067: 10, 6068: 13, 6174: 8, 6277: 6, 6278: 3, 6279: 14}
        self.assertEqual(221, sum(counts.values()))
        for resource, count in counts.items():
            prefix = f'SHIP/{resource:08d}.fpb/seq/'
            rows = [r for key, r in self.rows.items() if key.startswith(prefix)]
            self.assertEqual(count, len(rows))
            self.assertTrue(all(r['status'] == 'reviewed' for r in rows))

    def test_water_hero_is_female_and_party_insult_does_not_gender_everyone(self):
        self.assertIn('伊蕾因·玛侬', self.row(5682, 15)['target'])
        self.assertIn('少女', self.row(5684, 8)['target'])
        self.assertIn('她丧命', self.row(5686, 6)['target'])
        self.assertIn('袭击她', self.row(5695, 4)['target'])
        for resource, seq in [(5682, 20), (5683, 9)]:
            self.assertNotIn('毛头小子', self.row(resource, seq)['target'])
            self.assertIn('乳臭未干', self.row(resource, seq)['target'])

    def test_arrest_suspicion_and_defense_claims_keep_separate_roles(self):
        target = self.row(5684, 7)['target']
        self.assertIn('涉嫌暗杀', target)
        self.assertNotIn('罪名', target)
        self.assertIn('我认为', self.row(5686, 0)['target'])
        self.assertIn('被利用', self.row(5686, 6)['target'])
        self.assertIn('不是我们做的', self.row(6067, 2)['target'])
        self.assertIn('杀了水之英雄', self.row(6067, 1)['target'])

    def test_son_like_bond_and_childhood_display_forms_are_not_merged(self):
        for seq in [7, 10]:
            target = self.row(5686, seq)['target']
            self.assertIn('我把他视作自己的儿子', target)
            self.assertNotIn('亲生儿子', target)
        self.assertIn('休戈', self.row(5687, 4)['target'])
        self.assertIn('玛诺', self.row(5691, 0)['target'])
        self.assertIn('也许见过', self.row(5688, 6)['target'])

    def test_headquarters_responsibility_not_partial_lise_blame(self):
        self.assertIn('这并不是莉丝的问题', self.row(5694, 4)['target'])
        self.assertIn('是我的错', self.row(5694, 4)['target'])
        self.assertIn('辞去队长', self.row(5694, 5)['target'])
        self.assertIn('负责到底', self.row(5694, 8)['target'])
        self.assertNotIn('加倍', self.row(6068, 12)['target'])
        self.assertIn('偿还', self.row(6068, 12)['target'])
        self.assertIn('男人的求婚', self.row(6068, 4)['target'])

    def test_whole_idioms_and_controls_remain(self):
        for resource, seq, count in [(5683, 18, 1), (5686, 7, 2),
                                      (6068, 4, 1), (6068, 5, 2),
                                      (6068, 8, 2), (6174, 5, 2), (6277, 3, 2), (6279, 2, 1)]:
            target = self.row(resource, seq)['target']
            self.assertEqual(count, target.count('$n'))
            for bad in ['善罢甘$n休', '迟$n到', '真名法典的$n事', '要$n收集']:
                self.assertNotIn(bad, target)
        self.assertIn('善罢甘休', self.row(6277, 3)['target'])
        self.assertIn('罗斯蒂28号', self.row(6174, 7)['target'])



    def test_twenty_four_astal_letters_and_lise_memory_groups_reviewed(self):
        counts = {6280:23,6281:9,6293:4,6294:14,6351:3,6357:1,6358:13,
                  6434:1,6435:3,6436:2,6442:19,6457:3,6464:1,6495:21,
                  6512:4,6513:16,6514:7,6515:5,6518:11,6542:13,6555:25,
                  6680:16,6715:2,6729:7}
        self.assertEqual(223,sum(counts.values()))
        for resource,count in counts.items():
            rows=[v for k,v in self.rows.items() if k.startswith(f'SHIP/{resource:08d}.fpb/seq/')]
            self.assertEqual(count,len(rows))
            self.assertTrue(all(v['status']=='reviewed' for v in rows))

    def test_astal_research_claim_and_spy_denial_remain_separate(self):
        self.assertIn('策划',self.row(6280,7)['target'])
        self.assertIn('目的并非纯粹的研究',self.row(6280,10)['target'])
        self.assertIn('不是亚逊的间谍',self.row(6280,18)['target'])
        self.assertIn('十年',self.row(6280,13)['target'])
        self.assertIn('阿斯塔尔',self.row(6281,6)['target'])
        self.assertIn('回去的路',self.row(6293,0)['target'])
        self.assertNotIn('绕远路',self.row(6293,0)['target'])

    def test_phyllis_delayed_letter_and_female_pronoun_retained(self):
        self.assertIn('相识满四年',self.row(6495,6)['target'])
        self.assertIn('两年后',self.row(6495,12)['target'])
        self.assertIn('她一定',self.row(6495,13)['target'])
        self.assertIn('两年后的我',self.row(6518,7)['target'])
        self.assertIn('不会忘记',self.row(6518,10)['target'])
        self.assertIn('菲莉丝',self.row(6518,1)['target'])

    def test_lianna_arrest_is_political_claim_not_guilty_verdict(self):
        self.assertIn('妻子',self.row(6555,16)['target'])
        self.assertIn('第三个男人',self.row(6555,5)['target'])
        self.assertIn('替罪羊',self.row(6555,21)['target'])
        self.assertIn('还没向你传达',self.row(6555,30)['target'])
        self.assertIn('潜伏',self.row(6555,6)['target'])

    def test_lise_memory_unknown_rescuer_and_party_not_gendered(self):
        self.assertIn('有人拉着我',self.row(6680,3)['target'])
        self.assertNotIn('他',self.row(6680,3)['target'])
        for resource,seq in [(6457,2),(6715,1)]:
            self.assertIn('莉丝一行人',self.row(resource,seq)['target'])
            self.assertNotIn('她们',self.row(resource,seq)['target'])
        self.assertIn('她一定遇到危险',self.row(6729,0)['target'])
        self.assertIn('侦测模式',self.row(6680,15)['target'])

    def test_letter_and_memory_phrase_boundaries_preserve_controls(self):
        for resource,seq,count in [(6280,6,1),(6435,0,2),(6513,8,1),
                                  (6513,10,3),(6513,12,2),(6514,5,1),
                                  (6515,1,4),(6555,13,1),(6680,9,2),(6680,14,1)]:
            target=self.row(resource,seq)['target']
            self.assertEqual(count,target.count('$n'))
            for bad in ['面$n前','笔记$n里','写下$n去','这场$n仗','风月林$n']:
                self.assertNotIn(bad,target)
        self.assertIn('莫莉',self.row(6436,2)['target'])
        self.assertIn('十五年',self.row(6435,0)['target'])



    def test_thirty_one_birthday_memoir_and_late_story_groups_reviewed(self):
        counts={6733:42,6748:10,6814:1,6815:5,6827:1,6828:2,6829:5,6832:7,
                6834:3,6837:1,6887:4,6992:12,6996:7,7039:4,7096:4,7152:7,
                7296:15,7323:4,7355:17,7358:6,7360:26,7362:6,7364:4,7390:1,
                7443:3,7453:9,7454:11,7455:7,7456:6,7466:3,7508:10}
        self.assertEqual(243,sum(counts.values()))
        for resource,count in counts.items():
            rows=[v for k,v in self.rows.items() if k.startswith(f'SHIP/{resource:08d}.fpb/seq/')]
            self.assertEqual(count,len(rows))
            self.assertTrue(all(v['status']=='reviewed' for v in rows))

    def test_rehas_birthday_gift_and_war_memories_are_not_price_claim(self):
        self.assertIn('月之魔法师',self.row(6733,5)['target'])
        self.assertIn('恶灵',self.row(6733,19)['target'])
        self.assertIn('战争的事',self.row(6733,24)['target'])
        self.assertNotIn('贵重',self.row(6733,17)['target'])
        self.assertIn('黏土',self.row(6733,6)['target'])
        self.assertIn('杰古拉之骨',self.row(6733,6)['target'])

    def test_memoir_deductions_keep_river_mountain_and_times_distinct(self):
        self.assertIn('七八年后',self.row(6733,31)['target'])
        self.assertIn('山之碎片',self.row(6733,34)['target'])
        self.assertIn('江之碎片',self.row(6733,36)['target'])
        self.assertIn('推知',self.row(6733,35)['target'])
        self.assertIn('她',self.row(6733,34)['target'])
        self.assertIn('大巫师',self.row(6733,36)['target'])

    def test_neikan_male_third_man_and_queen_disagreement_remain(self):
        self.assertIn('第三个男人',self.row(6748,7)['target'])
        self.assertIn('内坎',self.row(6748,7)['target'])
        self.assertIn('小心他',self.row(6748,7)['target'])
        self.assertIn('傀儡',self.row(6992,4)['target'])
        self.assertIn('那两位臣子比你忠诚得多',self.row(6992,7)['target'])
        self.assertIn('凯莉安与阿萨德',self.row(6992,5)['target'])

    def test_lise_amila_radlinne_and_female_master_pronouns_retained(self):
        self.assertIn('他绝不是坏人',self.row(7096,2)['target'])
        self.assertIn('另外两位姑娘',self.row(7096,3)['target'])
        self.assertIn('那个女人',self.row(7454,9)['target'])
        self.assertIn('饶她一命',self.row(7454,9)['target'])
        self.assertIn('莉丝死了',self.row(7508,4)['target'])
        self.assertIn('阿米拉',self.row(7508,5)['target'])
        self.assertIn('她需要你',self.row(7508,6)['target'])

    def test_late_story_whole_clauses_controls_and_aircraft_number(self):
        for resource,seq,count in [(6733,31,4),(6733,33,4),(6733,35,5),
                                  (6733,36,9),(6834,1,1),(6992,0,4),
                                  (7360,22,3),(7360,30,2),(7360,33,3),(7362,2,2),(7508,6,1)]:
            target=self.row(resource,seq)['target']
            self.assertEqual(count,target.count('$n'))
            for bad in ['迅速$n开始','尚$n不清楚','心$n封闭','罗斯蒂28号，$n了']:
                self.assertNotIn(bad,target)
        self.assertIn('罗斯蒂28号',self.row(7362,2)['target'])
        self.assertIn('五十年前',self.row(7355,11)['target'])
        self.assertIn('木魔像',self.row(7355,11)['target'])



    def test_fifty_five_hostage_identity_and_memories_groups_reviewed(self):
        counts={7536:18,7542:3,7554:15,7555:16,7581:6,7593:12,7597:2,
                7642:9,7653:2,7657:1,7675:5,7682:5,7684:6,7685:13,
                8057:13,8065:8,8068:4,8085:5,8086:4,8087:7,8088:5,
                8210:17,8213:20,8214:11,8215:11,8216:4,8230:21,8249:3,
                8270:11,8272:7,8273:3,8299:5,8306:18,8332:2,9933:9,
                9934:6,9954:3,9965:7,9968:7,9971:5,9972:4,9975:8,
                9980:15,9984:5,9985:13,9988:1,9989:2,9992:8,9993:12,
                10278:12,10824:25,10869:7,10870:9,10892:12,10913:9}
        self.assertEqual(471,sum(counts.values()))
        for resource,count in counts.items():
            rows=[v for k,v in self.rows.items() if k.startswith(f'SHIP/{resource:08d}.fpb/seq/')]
            self.assertEqual(count,len(rows))
            self.assertTrue(all(v['status']=='reviewed' for v in rows))

    def test_pnosen_library_ghost_and_widowhood_not_lifespan_invention(self):
        self.assertIn('夫人去世',self.row(7536,4)['target'])
        self.assertIn('他没有继续活下去',self.row(7536,5)['target'])
        self.assertIn('三百年前',self.row(7536,7)['target'])
        self.assertIn('死后',self.row(7536,16)['target'])
        self.assertIn('吓死我了',self.row(7642,0)['target'])
        self.assertNotIn('十年寿命',self.row(7642,0)['target'])

    def test_orha_gender_not_invented_but_explicit_man_is_kept(self):
        self.assertIn('那个男人',self.row(7554,12)['target'])
        self.assertIn('保护他',self.row(7554,12)['target'])
        self.assertIn('对方说',self.row(8306,5)['target'])
        self.assertNotIn('他说',self.row(8306,5)['target'])
        self.assertIn('有人正趁着混乱',self.row(7555,6)['target'])
        self.assertIn('活不成',self.row(7555,11)['target'])

    def test_hostage_threats_and_party_surrender_keep_source_roles(self):
        self.assertIn('一次杀一个人',self.row(8213,12)['target'])
        self.assertIn('一次杀一个人',self.row(8213,16)['target'])
        self.assertIn('我投降',self.row(8213,13)['target'])
        self.assertIn('信不信',self.row(8213,23)['target'])
        self.assertIn('出卖你',self.row(8306,10)['target'])
        self.assertIn('我们的人质',self.row(10913,4)['target'])
        self.assertIn('暗杀拉德琳娜的罪名',self.row(10913,6)['target'])

    def test_lise_party_neutral_and_lianna_husband_information_direction(self):
        for resource,seq in [(8270,5),(8270,6),(9975,4)]:
            self.assertIn('莉丝一行人',self.row(resource,seq)['target'])
            self.assertNotIn('她们',self.row(resource,seq)['target'])
        self.assertIn('研究神器的丈夫',self.row(9985,5)['target'])
        self.assertIn('没有对我说过',self.row(9985,5)['target'])
        self.assertIn('他的踪迹',self.row(9985,10)['target'])
        self.assertIn('莉安娜丈夫',self.row(9972,2)['target'])

    def test_vision_self_blame_and_childhood_names_not_merged(self):
        self.assertIn('不是你的错',self.row(8087,3)['target'])
        self.assertIn('一切都是因为我',self.row(8088,3)['target'])
        self.assertIn('玛诺',self.row(8087,5)['target'])
        self.assertIn('休戈',self.row(8210,15)['target'])
        self.assertIn('劳尔会代替我牺牲',self.row(8210,15)['target'])
        self.assertIn('不完整的我',self.row(8214,5)['target'])
        self.assertIn('莉丝',self.row(8214,5)['target'])
        self.assertIn('为了自己而存在',self.row(8215,6)['target'])

    def test_bracelet_impersonation_and_river_water_fragments_separate(self):
        self.assertIn('让我成了“阿格雷安”',self.row(9980,4)['target'])
        self.assertIn('大巫女之子身份',self.row(9980,4)['target'])
        self.assertIn('手镯本来就是我的',self.row(9980,9)['target'])
        self.assertIn('天之碎片',self.row(9980,16)['target'])
        self.assertIn('大地之碎片',self.row(9980,16)['target'])
        self.assertIn('江之碎片',self.row(10913,8)['target'])
        self.assertIn('水之碎片',self.row(7581,1)['target'])
        self.assertIn('三千希德币',self.row(7685,5)['target'])
        self.assertIn('罗斯蒂28号',self.row(7675,3)['target'])

    def test_hostage_and_route_phrase_boundaries_controls_preserved(self):
        for resource,seq,count in [(7536,8,1),(7555,6,2),(7675,3,2),
                                  (7685,2,1),(8065,7,1),(8213,12,3),
                                  (8213,16,2),(8213,17,1),(8270,5,2),
                                  (8306,11,1),(9954,2,2),(9980,1,2),
                                  (9985,5,1),(10913,8,2)]:
            target=self.row(resource,seq)['target']
            self.assertEqual(count,target.count('$n'))
            for bad in ['恩特雷斯，$n沙漠','离$n开','杀一$n人','江之$n碎片','白费，$n了']:
                self.assertNotIn(bad,target)



    def test_sixty_four_rehas_hero_diary_and_queen_groups_reviewed(self):
        counts={10924: 17, 10988: 1, 10996: 3, 11018: 2, 11066: 4, 11068: 2, 11081: 3, 11091: 6, 11092: 2, 11099: 5, 11133: 12, 11134: 9, 11135: 2, 11163: 1, 11165: 3, 11216: 8, 11217: 33, 11218: 10, 11252: 18, 11253: 24, 11306: 6, 11347: 8, 11409: 3, 11410: 7, 11411: 2, 11412: 6, 11413: 17, 11414: 13, 11415: 5, 11416: 11, 11417: 18, 11418: 7, 11419: 18, 11420: 5, 11421: 12, 11422: 21, 11423: 24, 11424: 7, 11425: 10, 11430: 22, 11431: 6, 7658: 6, 11094: 6, 11432: 8, 11433: 8, 11434: 7, 11449: 15, 11463: 22, 11500: 13, 11630: 21, 11737: 1, 11740: 15, 11745: 7, 11739: 13, 11747: 5, 11748: 1, 11749: 1, 11758: 24, 11833: 11, 11837: 1, 11839: 1, 11841: 2, 11844: 2, 11865: 15}
        self.assertEqual(598,sum(counts.values()))
        for resource,count in counts.items():
            rows=[v for k,v in self.rows.items() if k.startswith(f'SHIP/{resource:08d}.fpb/seq/')]
            self.assertEqual(count,len(rows))
            self.assertTrue(all(v['status']=='reviewed' for v in rows))

    def test_twenty_five_strict_japanese_reference_readings_hash_roundtrip(self):
        import hashlib
        fixtures=[('SHIP/00007658.fpb/seq/0', '랦됞돫', 'c72dc83e99581bf0f8bb7373feeedb72878196b67255bae1cc780e408a325f06', '雑貨屋'), ('SHIP/00007658.fpb/seq/1', '벞뗰돫', 'cfb59645815e8437c50fd2599fa976c3007f8e160c66d3e35d92667a7c8875eb', '道具屋'), ('SHIP/00007658.fpb/seq/2', '궋귞궯궢귗궋귏궧갏', 'dd890f0d1f9fac20c6c4a6482ac3d31d3e3979ac61738fbfd1a46b9a55ea8262', 'いらっしゃいませ！'), ('SHIP/00007658.fpb/seq/3', '궇귟궕궴궎궟궡궋귏궢궫', '790aabaa6d20b9bdd2058e00729ebe759f441e6fbb1f4151a67942fd79793d55', 'ありがとうございました'), ('SHIP/00007658.fpb/seq/6', '먫궋돫', '477ba01385c09389dbdb45707080d6532ca1a32e786cb42537bcf1004e47dbbf', '占い屋'), ('SHIP/00007658.fpb/seq/7', '룮릐', 'e744f982b6a83f90ee1fdcf4a0624af4e766a0901f3d3c1be7bc5327375376f1', '商人'), ('SHIP/00011094.fpb/seq/0', '랦됞돫', 'c72dc83e99581bf0f8bb7373feeedb72878196b67255bae1cc780e408a325f06', '雑貨屋'), ('SHIP/00011094.fpb/seq/1', '벞뗰돫', 'cfb59645815e8437c50fd2599fa976c3007f8e160c66d3e35d92667a7c8875eb', '道具屋'), ('SHIP/00011094.fpb/seq/2', '궋귞궯궢귗궋귏궧갏', 'dd890f0d1f9fac20c6c4a6482ac3d31d3e3979ac61738fbfd1a46b9a55ea8262', 'いらっしゃいませ！'), ('SHIP/00011094.fpb/seq/3', '궇귟궕궴궎궟궡궋귏궢궫갃', '04a056951169f1753a48bf0fa454e25b54c59b39448c7ed3eeedc5d57d6eac76', 'ありがとうございました。'), ('SHIP/00011094.fpb/seq/6', '먫궋돫', '477ba01385c09389dbdb45707080d6532ca1a32e786cb42537bcf1004e47dbbf', '占い屋'), ('SHIP/00011094.fpb/seq/7', '룮릐', 'e744f982b6a83f90ee1fdcf4a0624af4e766a0901f3d3c1be7bc5327375376f1', '商人'), ('SHIP/00011739.fpb/seq/2', '몓궘갂묂뮮귩룙궚궸궋궖귏궢귛궎갏', '262052d3c28c34b95df5ed9083c3fe211bbd259470ff9b56a30c73f69de4e3cd', '早く、隊長を助けにいきましょう！'), ('SHIP/00011739.fpb/seq/5', '궋궯궩갂귺긐깒귽귺깛궸뿂귔궯궲궻궼궵궎궬궋갎', 'eb932174d381fb95ef11cd63704ab0ef67a87a98009dbadeb0a4a2d9b23ac4dd', 'いっそ、アグレイアンに頼むってのはどうだい？'), ('SHIP/00011739.fpb/seq/7', '궩귢궼궋궋뛩궑궬궶갃', 'd9778a61bc8f7adbb633e0e37837a736c82d528100beaa5fa633d9165c346d76', 'それはいい考えだな。'), ('SHIP/00011739.fpb/seq/8', '궑궯갎', '1f97643721411404f2dadf5eef87b008cd25f8aecf0e0d392bd947194e397b48', 'えっ？'), ('SHIP/00011739.fpb/seq/10', '긏깏긚갷', 'c3dd9a756a919c4fe6e97294e6a70bad1e30253c09deabf3f92232d813796776', 'クリス…'), ('SHIP/00011739.fpb/seq/11', '궶귪궳돱갎', 'a4c8689bdb2420fce6b976123492cb0832674d588c49e198db3946fa445f52f8', 'なんで俺？'), ('SHIP/00011739.fpb/seq/15', '묿궕먰뤾귩돘먛귡궴뙻궯궫갎$n긐깒귽긣깛랹뼩귩뎭궑귡귪궬갃$n돺봏궔멟궸뛱궯궫렄궸궼갂둴궔궸벞궕궇궯궫갃', 'de033afd8c9b0b1e981c0c540d2e3429c9b21c1ad5b356d4a4f81d8ec426bb87', '誰が戦場を横切ると言った？$nグレイトン山脈を越えるんだ。$n何年か前に行った時には、確かに道があった。'), ('SHIP/00011739.fpb/seq/21', '귦궫궢갷뛱궘귦갃', 'cb8b920239f2687632c6e63b3f3e06f316b417e4a01b9ea8fb5e5500ab72b0ff', 'わたし…行くわ。'), ('SHIP/00011739.fpb/seq/22', '궋궰귖긇깏깛긟궸룙궚귞귢궲궽궔귟궬궯궫귪궬귖궻갃$n뜞뱗궼귦궫궢궕룙궚귡귦갃', 'ad4b85f448fb00ffaf53cfe9877553d59118e4a4089264b9663daa1147e38995', 'いつもカリンツに助けられてばかりだったんだもの。$n今度はわたしが助けるわ。'), ('SHIP/00011739.fpb/seq/24', '궩귪궶궴궞귣궬궔귞갂먻볺궳궖궫궻궠갃$n궩귟귗궇갂궭귛궯궴궼궖궰궔궯궫궚궵궶갃', 'ec9d2c860bd3f4de5df1d1740a0b855d5a5835e9b174fafe80a57d85cc4bfb2d', 'そんなところだから、潜入できたのさ。$nそりゃあ、ちょっとはきつかったけどな。'), ('SHIP/00011739.fpb/seq/25', '귦궫궢궼뛱궘갃', 'ef0d406dbb26eff88e939950458cc1074dc03b69785d8efd7767984a330c264c', 'わたしは行く。'), ('SHIP/00011739.fpb/seq/29', '궩귢궳귖갂귦궫궢궼긇깏깛긟궻궴궞귣궸뛱궖귏궥갃', '8f3259a8edbf0241d4d924ed2971b059e26c775bcb0b796ca1988da293931b71', 'それでも、わたしはカリンツのところに行きます。'), ('SHIP/00011739.fpb/seq/30', '뱙궻럷궬궔귞갂$n룙궚궶귪궪뫲궯궲궶궋궴럙궎궚궵궶갃$n궳귖갂덇뱗궘귞궋딖뫲귩뿞먛궯궲귘귡궔갃', '92e169aa30c27fc9f0e5d38446b21c60f1e8fd2229785c7f3ac2205c6be059cc', '奴の事だから、$n助けなんぞ待ってないと思うけどな。$nでも、一度くらい期待を裏切ってやるか。')]
        self.assertEqual(25,len(fixtures))
        for key,reference,sha,japanese in fixtures:
            raw=reference.encode('cp949')
            self.assertEqual(japanese,raw.decode('cp932'))
            self.assertEqual(raw,japanese.encode('cp932'))
            self.assertEqual(sha,hashlib.sha256(raw).hexdigest())
            self.assertEqual(sha,self.rows[key]['source_sha256'])
        self.assertEqual('占卜屋',self.row(7658,6)['target'])
        self.assertIn('格雷顿山脉',self.row(11739,15)['target'])

    def test_hero_identity_and_twin_brothers_source_bound(self):
        self.assertIn('兰索尼·阿贝尔',self.row(11217,15)['target'])
        self.assertIn('天之英雄',self.row(11217,17)['target'])
        self.assertIn('年过六十',self.row(11217,12)['target'])
        self.assertIn('布兰的哥哥阿伦',self.row(11410,2)['target'])
        self.assertIn('双胞胎',self.row(11410,4)['target'])
        self.assertIn('巫女朱斯蒂娜',self.row(11410,5)['target'])

    def test_neikan_alias_does_not_prove_gender_and_orha_not_assigned_he(self):
        target=self.row(11422,13)['target']
        self.assertIn('不能只凭别名就断定是男人',target)
        self.assertNotIn('他',target)
        self.assertIn('奥尔哈',self.row(11425,5)['target'])
        self.assertNotIn('他',self.row(11425,5)['target'])
        self.assertNotIn('他',self.row(11740,12)['target'])
        self.assertNotIn('他',self.row(11748,0)['target'])
        self.assertNotIn('他',self.row(11216,3)['target'])

    def test_rehas_diary_gender_haren_phyllis_and_war_blame_not_erased(self):
        self.assertIn('蕾哈丝的日记',self.row(11430,0)['target'])
        self.assertIn('席本队长',self.row(11430,0)['target'])
        self.assertIn('剜出心脏',self.row(11430,3)['target'])
        self.assertIn('菲莉丝',self.row(11430,7)['target'])
        self.assertIn('男人',self.row(11430,9)['target'])
        self.assertIn('喜欢过他',self.row(11430,18)['target'])
        self.assertIn('哈伦责备我',self.row(11430,15)['target'])
        self.assertIn('不懂战斗的女人',self.row(11430,16)['target'])

    def test_queen_sister_jealousy_and_muen_woodening_keep_source_claims(self):
        self.assertIn('姐姐的过错',self.row(11252,12)['target'])
        self.assertIn('不能得到你的爱',self.row(11252,15)['target'])
        self.assertIn('凯莉安大人',self.row(11630,18)['target'])
        self.assertIn('下一任女王',self.row(11630,18)['target'])
        self.assertIn('她已经处决',self.row(11630,18)['target'])
        self.assertIn('当姐姐的影子',self.row(11758,11)['target'])
        self.assertIn('变成树也不是死了',self.row(11758,16)['target'])
        self.assertIn('一坐，就会折断',self.row(11758,14)['target'])

    def test_source_disagreement_and_arrest_release_remain_conditional_claims(self):
        self.assertIn('莉丝又没做错',self.row(11412,3)['target'])
        self.assertIn('都是因为我',self.row(11412,4)['target'])
        self.assertIn('不是说你有错',self.row(11412,5)['target'])
        self.assertIn('洗清嫌疑',self.row(11417,12)['target'])
        self.assertIn('第三个男人',self.row(11422,11)['target'])
        self.assertIn('应该才是',self.row(11419,11)['target'])
        for resource in [11253,11423]:
            self.assertIn('风之碎片和水之碎片',self.row(resource,10)['target'])

    def test_diary_dates_whole_words_and_woodening_control_boundaries(self):
        for resource,seq,count in [(11216,7,1),(11422,17,2),(11430,0,2),
                                  (11430,1,2),(11430,21,6),(11463,19,3),
                                  (11740,14,1),(11745,5,3),(11758,16,3),
                                  (11833,2,2),(11833,5,4),(11833,8,2)]:
            target=self.row(resource,seq)['target']
            self.assertEqual(count,target.count('$n'))
            for bad in ['帮上他的$n忙','腿也不会$n痛','强大的$n样子','传授给$n你']:
                self.assertNotIn(bad,target)
        self.assertTrue(self.row(11422,17)['target'].startswith('XX月XX日$n'))
        self.assertTrue(self.row(11430,1)['target'].startswith('X月X日$n'))



    def test_thirty_eight_final_scene_and_tutorial_groups_source_reviewed(self):
        counts={11933: 11, 11943: 18, 11948: 13, 11955: 5, 12008: 15, 13142: 10, 13143: 17, 13144: 17, 13145: 5, 13146: 10, 13179: 1, 13196: 9, 13197: 22, 13223: 6, 13224: 28, 13226: 14, 13227: 11, 13229: 22, 13264: 4, 13294: 22, 13311: 22, 13349: 22, 13355: 28, 13361: 29, 13362: 5, 13398: 1, 13402: 1, 13410: 12, 13421: 14, 13422: 15, 13423: 3, 13489: 26, 13490: 62, 13491: 69, 13492: 26, 13519: 13, 13520: 8, 13567: 33}
        self.assertEqual(649,sum(counts.values()))
        for resource,count in counts.items():
            rows=[v for k,v in self.rows.items() if k.startswith(f'SHIP/{resource:08d}.fpb/seq/')]
            self.assertEqual(count,len(rows))
            self.assertTrue(all(v['status']=='reviewed' for v in rows))

    def test_surrogate_mother_and_denial_are_not_biological_identity(self):
        self.assertIn('作为儿子',self.row(11943,10)['target'])
        self.assertIn('不是你的母亲',self.row(11943,11)['target'])
        self.assertIn('如同母亲',self.row(11948,10)['target'])
        self.assertIn('作为姐姐',self.row(13224,19)['target'])

    def test_orha_and_unidentified_craftsman_do_not_acquire_male_pronouns(self):
        self.assertNotIn('他',self.row(13142,5)['target'])
        self.assertNotIn('他',self.row(13422,4)['target'])
        self.assertNotIn('他',self.row(13520,6)['target'])
        self.assertIn('奥尔哈',self.row(13421,6)['target'])

    def test_same_dojo_spelling_variant_is_target_only_unified(self):
        self.assertEqual('我是帕克朱道场菊课程的师范。',self.row(13349,14)['target'])
        glossary=(ROOT/'GLOSSARY.md').read_text('utf8')
        self.assertIn('| 박조도장 | 帕克朱道场 |',glossary)
        self.assertIn('| 박주도장 | 帕克朱道场 |',glossary)
        self.assertIn('高置信推定',glossary)

    def test_all_tutorial_terms_stay_whole_across_protected_newlines(self):
        for seq in [4,5,11,13,24,28,31,43,49,51,53,55,61,67]:
            target=self.row(13491,seq)['target']
            for bad in ['三位一体$n驱动','罗刹$n模式','身体$n里','自行$n切换','敌人的$n攻击力']:
                self.assertNotIn(bad,target)
        self.assertIn('三位一体驱动',self.row(13491,31)['target'])
        self.assertIn('罗刹模式',self.row(13491,55)['target'])

    def test_tutorial_numbers_modes_and_buttons_retain_source_instructions(self):
        self.assertIn('×键',self.row(13491,5)['target'])
        self.assertIn('○键',self.row(13491,5)['target'])
        self.assertIn('△键',self.row(13491,47)['target'])
        self.assertIn('最多五个护盾',self.row(13491,53)['target'])
        self.assertIn('三次没有全部得到 GREAT',self.row(13491,43)['target'])
        self.assertIn('Miss',self.row(13491,57)['target'])
        self.assertIn('按上或下方向键',self.row(13491,55)['target'])
        self.assertIn('按左或右方向键',self.row(13491,51)['target'])
        for seq,number in [(22,'七次'),(23,'六次'),(24,'五次'),(25,'四次'),(26,'三次'),(27,'两次'),(28,'最后一次')]:
            self.assertIn(number,self.row(13361,seq)['target'])

    def test_character_claims_on_evolution_and_source_circulation_kept_distinct(self):
        self.assertIn('阵痛而已',self.row(13224,14)['target'])
        self.assertIn('自己能够感受到循环的流动',self.row(13294,19)['target'])
        self.assertNotIn('自身循环',self.row(13294,19)['target'])
        self.assertIn('恐怕还打算',self.row(13143,9)['target'])
        self.assertIn('首都埃彭塔德',self.row(13490,25)['target'])

    def test_final_scene_control_counts_and_whole_phrase_boundaries(self):
        for resource,seq,count in [(13294,19,7),(13311,19,4),(13349,19,5),(13355,19,4),(13361,19,5),(13490,25,8),(13491,55,7),(13492,10,3)]:
            self.assertEqual(count,self.row(resource,seq)['target'].count('$n'))
        for bad in ['最$n基本','这门$n技艺','伟大之人$n的踏脚石']:
            for resource in [13311,13355]:self.assertNotIn(bad,self.row(resource,19)['target'])


    def test_eighty_two_final_scenes_and_opening_groups_are_source_reviewed(self):
        counts={13578: 2, 13579: 7, 13583: 7, 13585: 16, 13587: 5, 13588: 4, 13590: 5, 13592: 2, 13593: 3, 13594: 13, 13595: 8, 13600: 19, 13602: 22, 13603: 9, 13604: 7, 13605: 11, 13606: 15, 13607: 2, 13608: 13, 13711: 3, 13727: 13, 13785: 13, 13786: 10, 13787: 9, 13788: 4, 13790: 9, 13792: 15, 13794: 7, 13797: 11, 13826: 4, 13830: 1, 13838: 13, 13840: 1, 13888: 1, 13892: 8, 13894: 10, 14007: 3, 14094: 4, 14113: 7, 14130: 7, 14147: 2, 14148: 1, 14149: 1, 14259: 20, 14288: 6, 14291: 14, 14293: 1, 14295: 2, 14325: 9, 14335: 12, 14360: 1, 14370: 5, 14371: 6, 14372: 5, 14373: 5, 14374: 8, 14375: 6, 14376: 5, 14377: 10, 14378: 4, 14379: 8, 14380: 6, 14381: 15, 14382: 3, 14386: 6, 14388: 6, 14390: 4, 14391: 2, 14392: 4, 356: 16, 358: 12, 443: 1, 357: 20, 432: 12, 453: 13, 1607: 4, 1608: 10, 1609: 16, 1617: 11, 1618: 7, 1619: 5, 1620: 14}
        self.assertEqual(82,len(counts))
        for resource,count in counts.items():
            rows=[v for k,v in self.rows.items() if k.startswith(f'SHIP/{resource:08d}.fpb/seq/')]
            self.assertEqual(count,len(rows))
            self.assertTrue(all(v['status']=='reviewed' for v in rows))

    def test_forty_five_opening_japanese_fields_strict_hash_roundtrip(self):
        import hashlib
        fixtures=[('SHIP/00000357.fpb/seq/0', '궬귢궬갎', '33426ba4774cb5fd754ccfc7970a2edc73014257fb6c92e634b4b3d002b36adc', 'だれだ？'), ('SHIP/00000357.fpb/seq/1', '(귦궫궢궼갋갋갋궬귢갎)', '9b500402d4b7f35186a73ed3ff3f7e1966d8ec9948e11905775135e8115d6a6e', '(わたしは・・・だれ？)'), ('SHIP/00000357.fpb/seq/3', '귦궔귞궶궋', '02aec5eb38d0f6b306d430698d450d24dd820baa57976188010d8bab5e698d77', 'わからない'), ('SHIP/00000357.fpb/seq/4', '릐듩궔갎', '9507f62e8d6486acf8073af62cc25bce81f2eda453611336823d3e2389137a67', '人間か？'), ('SHIP/00000357.fpb/seq/5', '궳궼갂궓멟궼궋궯궫궋묿궬갎', 'd816f3fed51fd9d6a17412162d173ddb1b247528cf9422323d2e2eb353e39d9d', 'では、お前はいったい誰だ？'), ('SHIP/00000357.fpb/seq/6', '뤹뭟궔갎', 'e4d977188104d34cad42a1ade9082674a5c6a245417ea854447b82ccd3e9c035', '冗談か？'), ('SHIP/00000357.fpb/seq/7', '갋갋갋궶궸귖럙궋뢯궧궶궋갋갋갋', '60fefbfbf33e5f5adda092bcda299e6424abf9df18d2f89b29c80f6b0496a83e', '・・・なにも思い出せない・・・'), ('SHIP/00000357.fpb/seq/8', '궣귗궇갂딯돬귩궫궵궯궲쁞궢궲귒궶', 'e325b0fb24ddb42b8aade52da8d7a9f22b3e9491978f4ff8e4fa0807bbbb51e1', 'じゃあ、記憶をたどって話してみな'), ('SHIP/00000357.fpb/seq/9', '궩귢궕갋갋갋딠궕궰궋궫궴궖궸궼', 'b39bb037707450aaf8fc423c78dc51b164fcae97c39548d408d71046f5772839', 'それが・・・気がついたときには'), ('SHIP/00000357.fpb/seq/10', '궞궞궸궋궫갃$n궩귢궔귞갋갋갋', '6e2527e1f14d684351a09c3615597c326ce8e46ca992b8c2993ee04a2c49a752', 'ここにいた。$nそれから・・・'), ('SHIP/00000357.fpb/seq/11', '궇궶궫궕궩궽궸궋궫갃$n궓궞궩궎궴궢궲귖갂뽞귩둶귏궠궶궘궲', '6d2c36596380b5890cd4cbbde9fd4599c9f2693c8fe7041beb23bd02b10e3e65', 'あなたがそばにいた。$nおこそうとしても、目を覚まさなくて'), ('SHIP/00000357.fpb/seq/13', '렊궢궲궘귢궫궻궔갎$n갋갋갋궇궻뚹궼됷븳뢱궬궯궫궻궔갎', 'd8b38d54eb0d216dbed53cdaa2876264f0261ea2311454d10e0c08a809f3eb74', '治してくれたのか？$n・・・あの光は回復術だったのか？'), ('SHIP/00000357.fpb/seq/14', '됷븳뢱갋갋갋', 'ad7b2122c5d735f58791f30900e030bb9c3893522a80498bb6a370c19636b1d8', '回復術・・・'), ('SHIP/00000357.fpb/seq/24', '궩궎갂궓멟궻뼹멟궬귝갃$n딯돬귩롦귟귖궵궥귏궳궼갂뼹멟궕궶궋궴뜟귡궬귣궎갎', 'e9bc029e77ac73eef5ffce502c8e9d9ce5fbf6e520e8592adeb2a4ca6316b9bd', 'そう、お前の名前だよ。$n記憶を取りもどすまでは、名前がないと困るだろう？'), ('SHIP/00000357.fpb/seq/26', '$D06궎귪갃궇궻궒갂$D52 $D03궇궶궫궼갎', 'ffc3fb72797b9e5437cfa16d7fd3d02b0df9a1527d386c3ae345d623bf8564dd', '$D06うん。あのぉ、$D52 $D03あなたは？'), ('SHIP/00000357.fpb/seq/27', '긇깏깛긟궬갃', 'd8a9ee1c111a4f2dcd5632d1c78b7aa9e5153d613ee2bd3755c86fd699cfc444', 'カリンツだ。'), ('SHIP/00000357.fpb/seq/28', '궠궆갂돱궻롨귩궴궯궲갏', '2494ef65276e632afe80a64c0338e07f5efa67efbd2b21e18365ffc74abc5504', 'さぁ、俺の手をとって！'), ('SHIP/00000357.fpb/seq/29', '궎귪갂긇깏깛긟', '6d9a2d9292d0d23c9540bd09f77362df66a19f0acacbf88951e99b45f61b4f61', 'うん、カリンツ'), ('SHIP/00000357.fpb/seq/30', '뛱궞궎갏', '2bb8c62b04a4b49503a01836addde5b732f682ed5ca29934e2f4f27d0a36a1ba', '行こう！'), ('SHIP/00000357.fpb/seq/31', '(뢯뚿궼귔궞궎궬궶)', '9766228789e033eccbb593f69acc57cdaa2649055d17fc45702f47fcfe1ebad5', '(出口はむこうだな)'), ('SHIP/00000432.fpb/seq/6', '돱궻룤귩렊궢궲궘귢궫귝궎궬궶갃', '10992b8f5c040f3496c74cc4e874c872e3df7e09f2335441ba001ccbb8852b1f', '俺の傷を治してくれたようだな。'), ('SHIP/00000432.fpb/seq/7', '떶궔궢궫궶귞롍귡갃뼰댰렞뭷궸뙐귩$n뵴궘빯궕궇궯궲궰궋갃', '62263a9060328ce1fc8dc2b8365a3e8d03449f559a79f1bbcb4437ae36d9e836', '驚かしたなら謝る。無意識中に剣を$n抜く癖があってつい。'), ('SHIP/00000432.fpb/seq/9', '궇귞갎', '1fdadf485bc23f2baccb1c3909ccd2176c3d583fc67afa877e7c794c8ef2697e', 'あら？'), ('SHIP/00000432.fpb/seq/10', '쎷룛궣귗궶궋궻궔갎', 'fb584f2e505d220a02c07a143f2a71ba0eb6117abfca4ce772e39ce7886e5b8f', '巫女じゃないのか？'), ('SHIP/00000432.fpb/seq/11', '갋갋갋궟귕귪갃럡갂돺귖럙궋뢯궧궶궋궻갃', 'd92e7f8d761147033110785fa38b03395e16dfe98a4563f86c83074744c7663b', '・・・ごめん。私、何も思い出せないの。'), ('SHIP/00000432.fpb/seq/12', '궓궋갋갋갋', '1140c76b99a8f7f5f9171a3fbd77b3fb368c79254298d96b1f1562e1cb86806d', 'おい・・・'), ('SHIP/00000432.fpb/seq/17', '뼹멟궼둶궑궲궋귡궔갎', '01d96b19f0275f43e1649ea6a10aa404c4439fddcad042d0c07b226d0938cbd3', '名前は覚えているか？'), ('SHIP/00000432.fpb/seq/18', '귟갋갋갋긚갎', '50e05c0225aecfb1dbab9b87492fa3dd342213ce8ed5022d38ca71577cc9c5f0', 'り・・・ス？'), ('SHIP/00000432.fpb/seq/19', '궩궎궔갂궞귢궔귞궼깏긚궴뚁귍궎갃', 'e41c570ed56f75fe3713494ea71a6d6dd5d874a46704b23c38bc839c327f23f5', 'そうか、これからはリスと呼ぼう。'), ('SHIP/00000432.fpb/seq/21', '궎귪갋갋갋궇궻갋갋갋', '74794bbe458ef5d7b0c0565f132a9486f6b7f96dbcf1b8accf612443a36a84ed', 'うん・・・あの・・・'), ('SHIP/00000432.fpb/seq/22', '긇깏깛긟갃', '5f650ec88a53f2f83fe30b27d159b2f5236dcc2d881d9734bc5692fe231e7733', 'カリンツ。'), ('SHIP/00000432.fpb/seq/23', '궎귪갂긇깏깛긟갃', 'fade959cc28150f963acf09e2093dceed844a1af7c9c380a5898ce5a86085cc5', 'うん、カリンツ。'), ('SHIP/00000453.fpb/seq/0', '궇갂럡갂궞궞궔귞븵귩렃궯궲궖궫귪궬', 'd5be13a031f251c84b633eafb0734e9b32f0249d760b0abee7fb7cdba2711fae', 'あ、私、ここから服を持ってきたんだ'), ('SHIP/00000453.fpb/seq/1', '궼갎', 'd0e1c4b000556c1c19e0debd4b010615b2c6ea5a63471c25862a3a91bd838ecd', 'は？'), ('SHIP/00000453.fpb/seq/2', '뭶궲궋궫븵궕귘귆귢궭귗궯궲갂궞궞궸궇궯궫븵귩뭶궫궻', '3bd22bab58649fa3b9ca082592e2a4282b247cf034c3a24b794b9837833cdd7a', '着ていた服がやぶれちゃって、ここにあった服を着たの'), ('SHIP/00000453.fpb/seq/3', 'XX뙉 XX볷$n닩궥귡귺깏귺깛귉', '6d20120c806584a101053b2f9cebf26875848298259c38cf3320a900b7fefdf9', 'XX月 XX日$n愛するアリアンへ'), ('SHIP/00000453.fpb/seq/6', '귖궢붯궕럡궸븳뢖궢궸뿀귡궶귞갂$n럡궸궼돺귖궳궖궶궋...', 'a2437edb3e4ff25637762fb70a2d62ece78136e307e3194c2cda8dd1f3633165', 'もし彼が私に復讐しに来るなら、$n私には何もできない...'), ('SHIP/00000453.fpb/seq/8', '...릐듩궴궻맯뒋궸뒿귢궶궔궯궫럡궻궫귕궸$n궞궻벖똀궳...덇룒궸$n됡궟궢궲궘귢궫궞궴귖갂륲궔귞...', '037a395029fa4cc8238bcc38d5c9dbe9ec343f86479581a584d96ffbc44d7536', '...人間との生活に慣れなかった私のために$nこの洞窟で...一緒に$n過ごしてくれたことも、心から...'), ('SHIP/00000453.fpb/seq/9', '궇궶궫궴덇룒궸됡궟궢궫...$n럡궼뫝궘궻귖궻귩똍궔귞귖귞궯궫', '799424669c9f71a047719f25fc33847f79e03cd2d4c0db25240cd55bc9922f87', 'あなたと一緒に過ごした...$n私は多くのものを君からもらった'), ('SHIP/00000453.fpb/seq/11', '렳궼...릈궔궯궫귪...$n룛맜궻궇궶궫궕갂떗궘궶귡궫귕궸...$n딠궸볺귞궶궋궔귖궢귢궶궋궕갂$n롷궚궴궯궲궘귢귡궔궶갎', '25015d9932aa84867200b45ec40fc84702b5c86f10392c85f6e126f41f0115f9', '実は...辛かったん...$n女性のあなたが、強くなるために...$n気に入らないかもしれないが、$n受けとってくれるかな？'), ('SHIP/00000453.fpb/seq/12', '돺갎돺갎', 'a0c547ad670bde95a097c5ea13062dfa63c7560daa26fdd5f63ba5abd6733902', '何？何？'), ('SHIP/00000453.fpb/seq/13', '똍궻븵궼궋귦궘궰궖귞궢궋귝', '35c7871e62f51039138b92ab513440e8dfb87319c9dd7380d5e5f37da993302d', '君の服はいわくつきらしいよ'), ('SHIP/00000453.fpb/seq/15', '묈뤶븎궬귣궎 궔궶귟묈먎궻궞궴귞궢궋궔귞', '4196bdd11b843d0942000b7cf562d131da797f27a20baceee336ba3ba2cdea9a', '大丈夫だろう かなり大昔のことらしいから'), ('SHIP/00000453.fpb/seq/16', '귝궔궯궫', 'd8dc958542cc6be7ed7563ea3ba5a10fc65b7ca229efbd5eb0a25cceb3c60c02', 'よかった'), ('SHIP/00000453.fpb/seq/17', '룺궢궬궚궓롔귟궢귏궥', '6164a539121ca037753dbc7c82a9677699b2b26d1516caa03d92325e9525e505', '少しだけお借りします')]
        self.assertEqual(45,len(fixtures))
        for key,reference,sha,japanese in fixtures:
            raw=reference.encode('cp949')
            self.assertEqual(japanese,raw.decode('cp932'))
            self.assertEqual(raw,japanese.encode('cp932'))
            self.assertEqual(sha,hashlib.sha256(raw).hexdigest())
            self.assertEqual(sha,self.rows[key]['source_sha256'])
        self.assertEqual('$D06嗯。那个，$D52 $D03你呢？',self.row(357,26)['target'])

    def test_bloodlust_and_unidentified_recipient_are_source_bound(self):
        target=self.row(14373,0)['target']
        self.assertIn('你想见血',target)
        self.assertNotIn('不想见血',target)
        self.assertEqual('不能把它交出去！',self.row(14291,14)['target'])
        self.assertIn('救命恩人',self.row(13594,4)['target'])
        self.assertIn('牺牲',self.row(13594,1)['target'])

    def test_queen_sisters_blame_and_denial_are_not_flattened(self):
        self.assertIn('姐姐逼上绝路',self.row(13603,3)['target'])
        self.assertIn('没对她做什么',self.row(13603,4)['target'])
        self.assertIn('使用了大魔法',self.row(13603,5)['target'])
        self.assertIn('莉丝的妹妹',self.row(13600,8)['target'])
        self.assertIn('唯一的妹妹',self.row(13600,8)['target'])
        self.assertIn('我对卡林兹',self.row(14259,19)['target'])

    def test_unconscious_trial_and_teacher_predictions_remain_source_claims(self):
        self.assertIn('下意识拔剑',self.row(432,7)['target'])
        self.assertIn('精神受到打击',self.row(14370,4)['target'])
        self.assertIn('潜意识',self.row(14370,4)['target'])
        self.assertIn('不会获得看见卡恩的眼睛',self.row(14335,3)['target'])
        self.assertIn('夜叉模式',self.row(13797,10)['target'])
        self.assertIn('恐怕会戒备森严',self.row(14379,7)['target'])
        self.assertIn('无形剑',self.row(14335,6)['target'])

    def test_chris_father_brother_plane_numbers_and_feather_quantity_distinct(self):
        self.assertIn('罗斯坦先生',self.row(1608,2)['target'])
        self.assertIn('安吉拉',self.row(1608,2)['target'])
        self.assertIn('埃斯蒂',self.row(1609,9)['target'])
        self.assertIn('哥哥试飞时死了',self.row(1617,8)['target'])
        self.assertIn('罗斯蒂27号',self.row(1617,9)['target'])
        self.assertIn('罗斯蒂28号',self.row(1618,0)['target'])
        self.assertIn('十根左右',self.row(1618,1)['target'])
        self.assertIn('奥马雷布',self.row(1618,1)['target'])

    def test_partial_letter_gender_and_source_date_not_completed_by_invention(self):
        self.assertIn('身为女性的你',self.row(453,11)['target'])
        self.assertTrue(self.row(453,3)['target'].startswith('XX月XX日$n'))
        self.assertIn('阿莉安',self.row(453,3)['target'])
        self.assertTrue(self.row(453,8)['target'].endswith('衷心……'))
        self.assertIn('想不起',self.row(357,7)['target'])

    def test_final_scene_phrase_boundaries_and_source_controls_remain(self):
        for resource,seq,count in [(13579,3,1),(13585,24,1),(13590,4,2),(13608,0,1),(13727,4,1),(13830,0,2),(13838,6,2),(14259,3,2),(14370,3,2),(432,7,1),(453,8,2),(1609,12,3),(1620,4,1)]:
            self.assertEqual(count,self.row(resource,seq)['target'].count('$n'))
        for bad in ['深仇$n大恨','拔剑的$n习惯','停步$n了','自行$n切换']:
            for resource,seq in [(13838,6),(432,7),(14377,7)]:self.assertNotIn(bad,self.row(resource,seq)['target'])


    def test_last_sixteen_town_story_groups_source_reviewed(self):
        counts={1644: 18, 1936: 2, 14393: 3, 14394: 5, 14522: 2, 14713: 1, 14895: 49, 14898: 38, 14899: 23, 14900: 21, 14901: 54, 14902: 41, 14903: 42, 14904: 42, 14905: 40, 14906: 48}
        self.assertEqual(16,len(counts))
        for resource,count in counts.items():
            rows=[v for k,v in self.rows.items() if k.startswith(f'SHIP/{resource:08d}.fpb/seq/')]
            self.assertEqual(count,len(rows))
            self.assertTrue(all(v['status']=='reviewed' for v in rows))
        self.assertFalse(any(v['status']=='draft' for v in self.rows.values()))

    def test_orha_and_unidentified_mixedrace_town_visitors_gender_neutral(self):
        for resource,seq in [(14895,8),(14898,1),(14899,8),(14904,5),(14906,20)]:
            self.assertNotIn('他',self.row(resource,seq)['target'])
        self.assertIn('奥尔哈',self.row(14899,8)['target'])
        self.assertIn('奥尔哈',self.row(14906,20)['target'])
        self.assertIn('手足',self.row(14902,13)['target'])
        self.assertNotIn('弟弟',self.row(14902,13)['target'])
        self.assertNotIn('弟弟',self.row(14902,14)['target'])

    def test_town_explicit_male_female_and_family_information_preserved(self):
        self.assertIn('一个男人',self.row(1644,1)['target'])
        self.assertEqual('我叫斯戴。也想知道其他几位的名字。',self.row(1644,6)['target'])
        self.assertIn('女人',self.row(14900,14)['target'])
        self.assertIn('儿子埃斯蒂',self.row(14905,1)['target'])
        self.assertIn('两个儿子',self.row(14905,14)['target'])
        self.assertIn('哥哥',self.row(14905,27)['target'])
        self.assertIn('双胞胎',self.row(14901,2)['target'])
        self.assertIn('不是双胞胎吗',self.row(14901,2)['target'])

    def test_liberation_front_and_shop_names_stay_canonical(self):
        self.assertIn('解放阵线',self.row(14901,7)['target'])
        self.assertNotIn('解放战线',self.row(14901,7)['target'])
        self.assertIn('格兰朱商会',self.row(14901,12)['target'])
        self.assertIn('红月佣兵团',self.row(14902,6)['target'])
        self.assertIn('阿泽翼',self.row(14903,37)['target'])

    def test_town_text_does_not_leave_closing_punctuation_at_line_start(self):
        import re
        ids=['SHIP/00001644.fpb/seq/0', 'SHIP/00001644.fpb/seq/1', 'SHIP/00001644.fpb/seq/2', 'SHIP/00001644.fpb/seq/3', 'SHIP/00001644.fpb/seq/4', 'SHIP/00001644.fpb/seq/5', 'SHIP/00001644.fpb/seq/6', 'SHIP/00001644.fpb/seq/7', 'SHIP/00001644.fpb/seq/8', 'SHIP/00001644.fpb/seq/9', 'SHIP/00001644.fpb/seq/10', 'SHIP/00001644.fpb/seq/11', 'SHIP/00001644.fpb/seq/12', 'SHIP/00001644.fpb/seq/13', 'SHIP/00001644.fpb/seq/14', 'SHIP/00001644.fpb/seq/15', 'SHIP/00001644.fpb/seq/16', 'SHIP/00001644.fpb/seq/17', 'SHIP/00001936.fpb/seq/0', 'SHIP/00001936.fpb/seq/1', 'SHIP/00014393.fpb/seq/0', 'SHIP/00014393.fpb/seq/1', 'SHIP/00014393.fpb/seq/2', 'SHIP/00014394.fpb/seq/0', 'SHIP/00014394.fpb/seq/1', 'SHIP/00014394.fpb/seq/2', 'SHIP/00014394.fpb/seq/3', 'SHIP/00014394.fpb/seq/4', 'SHIP/00014522.fpb/seq/0', 'SHIP/00014522.fpb/seq/1', 'SHIP/00014713.fpb/seq/0', 'SHIP/00014895.fpb/seq/0', 'SHIP/00014895.fpb/seq/1', 'SHIP/00014895.fpb/seq/2', 'SHIP/00014895.fpb/seq/3', 'SHIP/00014895.fpb/seq/4', 'SHIP/00014895.fpb/seq/5', 'SHIP/00014895.fpb/seq/6', 'SHIP/00014895.fpb/seq/7', 'SHIP/00014895.fpb/seq/8', 'SHIP/00014895.fpb/seq/9', 'SHIP/00014895.fpb/seq/10', 'SHIP/00014895.fpb/seq/11', 'SHIP/00014895.fpb/seq/12', 'SHIP/00014895.fpb/seq/13', 'SHIP/00014895.fpb/seq/14', 'SHIP/00014895.fpb/seq/15', 'SHIP/00014895.fpb/seq/16', 'SHIP/00014895.fpb/seq/17', 'SHIP/00014895.fpb/seq/18', 'SHIP/00014895.fpb/seq/19', 'SHIP/00014895.fpb/seq/20', 'SHIP/00014895.fpb/seq/21', 'SHIP/00014895.fpb/seq/22', 'SHIP/00014895.fpb/seq/23', 'SHIP/00014895.fpb/seq/24', 'SHIP/00014895.fpb/seq/25', 'SHIP/00014895.fpb/seq/27', 'SHIP/00014895.fpb/seq/28', 'SHIP/00014895.fpb/seq/29', 'SHIP/00014895.fpb/seq/30', 'SHIP/00014895.fpb/seq/31', 'SHIP/00014895.fpb/seq/32', 'SHIP/00014895.fpb/seq/33', 'SHIP/00014895.fpb/seq/34', 'SHIP/00014895.fpb/seq/35', 'SHIP/00014895.fpb/seq/36', 'SHIP/00014895.fpb/seq/37', 'SHIP/00014895.fpb/seq/38', 'SHIP/00014895.fpb/seq/39', 'SHIP/00014895.fpb/seq/40', 'SHIP/00014895.fpb/seq/41', 'SHIP/00014895.fpb/seq/42', 'SHIP/00014895.fpb/seq/43', 'SHIP/00014895.fpb/seq/44', 'SHIP/00014895.fpb/seq/45', 'SHIP/00014895.fpb/seq/46', 'SHIP/00014895.fpb/seq/47', 'SHIP/00014895.fpb/seq/48', 'SHIP/00014895.fpb/seq/49', 'SHIP/00014898.fpb/seq/0', 'SHIP/00014898.fpb/seq/1', 'SHIP/00014898.fpb/seq/2', 'SHIP/00014898.fpb/seq/3', 'SHIP/00014898.fpb/seq/4', 'SHIP/00014898.fpb/seq/5', 'SHIP/00014898.fpb/seq/6', 'SHIP/00014898.fpb/seq/7', 'SHIP/00014898.fpb/seq/8', 'SHIP/00014898.fpb/seq/9', 'SHIP/00014898.fpb/seq/10', 'SHIP/00014898.fpb/seq/11', 'SHIP/00014898.fpb/seq/12', 'SHIP/00014898.fpb/seq/13', 'SHIP/00014898.fpb/seq/14', 'SHIP/00014898.fpb/seq/15', 'SHIP/00014898.fpb/seq/16', 'SHIP/00014898.fpb/seq/17', 'SHIP/00014898.fpb/seq/18', 'SHIP/00014898.fpb/seq/19', 'SHIP/00014898.fpb/seq/20', 'SHIP/00014898.fpb/seq/21', 'SHIP/00014898.fpb/seq/24', 'SHIP/00014898.fpb/seq/25', 'SHIP/00014898.fpb/seq/26', 'SHIP/00014898.fpb/seq/27', 'SHIP/00014898.fpb/seq/28', 'SHIP/00014898.fpb/seq/29', 'SHIP/00014898.fpb/seq/30', 'SHIP/00014898.fpb/seq/31', 'SHIP/00014898.fpb/seq/32', 'SHIP/00014898.fpb/seq/33', 'SHIP/00014898.fpb/seq/34', 'SHIP/00014898.fpb/seq/35', 'SHIP/00014898.fpb/seq/36', 'SHIP/00014898.fpb/seq/37', 'SHIP/00014898.fpb/seq/38', 'SHIP/00014898.fpb/seq/39', 'SHIP/00014899.fpb/seq/0', 'SHIP/00014899.fpb/seq/1', 'SHIP/00014899.fpb/seq/2', 'SHIP/00014899.fpb/seq/3', 'SHIP/00014899.fpb/seq/4', 'SHIP/00014899.fpb/seq/5', 'SHIP/00014899.fpb/seq/6', 'SHIP/00014899.fpb/seq/7', 'SHIP/00014899.fpb/seq/8', 'SHIP/00014899.fpb/seq/9', 'SHIP/00014899.fpb/seq/10', 'SHIP/00014899.fpb/seq/11', 'SHIP/00014899.fpb/seq/12', 'SHIP/00014899.fpb/seq/13', 'SHIP/00014899.fpb/seq/14', 'SHIP/00014899.fpb/seq/15', 'SHIP/00014899.fpb/seq/16', 'SHIP/00014899.fpb/seq/17', 'SHIP/00014899.fpb/seq/18', 'SHIP/00014899.fpb/seq/19', 'SHIP/00014899.fpb/seq/20', 'SHIP/00014899.fpb/seq/22', 'SHIP/00014899.fpb/seq/23', 'SHIP/00014900.fpb/seq/0', 'SHIP/00014900.fpb/seq/1', 'SHIP/00014900.fpb/seq/2', 'SHIP/00014900.fpb/seq/3', 'SHIP/00014900.fpb/seq/4', 'SHIP/00014900.fpb/seq/5', 'SHIP/00014900.fpb/seq/6', 'SHIP/00014900.fpb/seq/7', 'SHIP/00014900.fpb/seq/8', 'SHIP/00014900.fpb/seq/9', 'SHIP/00014900.fpb/seq/10', 'SHIP/00014900.fpb/seq/11', 'SHIP/00014900.fpb/seq/12', 'SHIP/00014900.fpb/seq/13', 'SHIP/00014900.fpb/seq/14', 'SHIP/00014900.fpb/seq/15', 'SHIP/00014900.fpb/seq/16', 'SHIP/00014900.fpb/seq/17', 'SHIP/00014900.fpb/seq/18', 'SHIP/00014900.fpb/seq/19', 'SHIP/00014900.fpb/seq/20', 'SHIP/00014901.fpb/seq/0', 'SHIP/00014901.fpb/seq/1', 'SHIP/00014901.fpb/seq/2', 'SHIP/00014901.fpb/seq/3', 'SHIP/00014901.fpb/seq/4', 'SHIP/00014901.fpb/seq/5', 'SHIP/00014901.fpb/seq/6', 'SHIP/00014901.fpb/seq/7', 'SHIP/00014901.fpb/seq/8', 'SHIP/00014901.fpb/seq/9', 'SHIP/00014901.fpb/seq/10', 'SHIP/00014901.fpb/seq/11', 'SHIP/00014901.fpb/seq/12', 'SHIP/00014901.fpb/seq/13', 'SHIP/00014901.fpb/seq/14', 'SHIP/00014901.fpb/seq/15', 'SHIP/00014901.fpb/seq/16', 'SHIP/00014901.fpb/seq/17', 'SHIP/00014901.fpb/seq/18', 'SHIP/00014901.fpb/seq/19', 'SHIP/00014901.fpb/seq/20', 'SHIP/00014901.fpb/seq/21', 'SHIP/00014901.fpb/seq/22', 'SHIP/00014901.fpb/seq/23', 'SHIP/00014901.fpb/seq/24', 'SHIP/00014901.fpb/seq/26', 'SHIP/00014901.fpb/seq/27', 'SHIP/00014901.fpb/seq/28', 'SHIP/00014901.fpb/seq/29', 'SHIP/00014901.fpb/seq/30', 'SHIP/00014901.fpb/seq/31', 'SHIP/00014901.fpb/seq/32', 'SHIP/00014901.fpb/seq/33', 'SHIP/00014901.fpb/seq/34', 'SHIP/00014901.fpb/seq/35', 'SHIP/00014901.fpb/seq/36', 'SHIP/00014901.fpb/seq/37', 'SHIP/00014901.fpb/seq/38', 'SHIP/00014901.fpb/seq/39', 'SHIP/00014901.fpb/seq/40', 'SHIP/00014901.fpb/seq/41', 'SHIP/00014901.fpb/seq/44', 'SHIP/00014901.fpb/seq/45', 'SHIP/00014901.fpb/seq/46', 'SHIP/00014901.fpb/seq/47', 'SHIP/00014901.fpb/seq/50', 'SHIP/00014901.fpb/seq/51', 'SHIP/00014901.fpb/seq/52', 'SHIP/00014901.fpb/seq/53', 'SHIP/00014901.fpb/seq/54', 'SHIP/00014901.fpb/seq/55', 'SHIP/00014901.fpb/seq/56', 'SHIP/00014901.fpb/seq/57', 'SHIP/00014901.fpb/seq/58', 'SHIP/00014902.fpb/seq/0', 'SHIP/00014902.fpb/seq/1', 'SHIP/00014902.fpb/seq/2', 'SHIP/00014902.fpb/seq/3', 'SHIP/00014902.fpb/seq/4', 'SHIP/00014902.fpb/seq/6', 'SHIP/00014902.fpb/seq/7', 'SHIP/00014902.fpb/seq/8', 'SHIP/00014902.fpb/seq/9', 'SHIP/00014902.fpb/seq/10', 'SHIP/00014902.fpb/seq/11', 'SHIP/00014902.fpb/seq/12', 'SHIP/00014902.fpb/seq/13', 'SHIP/00014902.fpb/seq/14', 'SHIP/00014902.fpb/seq/15', 'SHIP/00014902.fpb/seq/16', 'SHIP/00014902.fpb/seq/17', 'SHIP/00014902.fpb/seq/18', 'SHIP/00014902.fpb/seq/19', 'SHIP/00014902.fpb/seq/20', 'SHIP/00014902.fpb/seq/21', 'SHIP/00014902.fpb/seq/22', 'SHIP/00014902.fpb/seq/23', 'SHIP/00014902.fpb/seq/24', 'SHIP/00014902.fpb/seq/25', 'SHIP/00014902.fpb/seq/26', 'SHIP/00014902.fpb/seq/27', 'SHIP/00014902.fpb/seq/28', 'SHIP/00014902.fpb/seq/29', 'SHIP/00014902.fpb/seq/30', 'SHIP/00014902.fpb/seq/31', 'SHIP/00014902.fpb/seq/32', 'SHIP/00014902.fpb/seq/33', 'SHIP/00014902.fpb/seq/34', 'SHIP/00014902.fpb/seq/35', 'SHIP/00014902.fpb/seq/36', 'SHIP/00014902.fpb/seq/37', 'SHIP/00014902.fpb/seq/38', 'SHIP/00014902.fpb/seq/39', 'SHIP/00014902.fpb/seq/40', 'SHIP/00014902.fpb/seq/41', 'SHIP/00014903.fpb/seq/0', 'SHIP/00014903.fpb/seq/1', 'SHIP/00014903.fpb/seq/2', 'SHIP/00014903.fpb/seq/3', 'SHIP/00014903.fpb/seq/4', 'SHIP/00014903.fpb/seq/5', 'SHIP/00014903.fpb/seq/6', 'SHIP/00014903.fpb/seq/7', 'SHIP/00014903.fpb/seq/8', 'SHIP/00014903.fpb/seq/9', 'SHIP/00014903.fpb/seq/10', 'SHIP/00014903.fpb/seq/11', 'SHIP/00014903.fpb/seq/12', 'SHIP/00014903.fpb/seq/13', 'SHIP/00014903.fpb/seq/14', 'SHIP/00014903.fpb/seq/15', 'SHIP/00014903.fpb/seq/16', 'SHIP/00014903.fpb/seq/17', 'SHIP/00014903.fpb/seq/18', 'SHIP/00014903.fpb/seq/19', 'SHIP/00014903.fpb/seq/20', 'SHIP/00014903.fpb/seq/21', 'SHIP/00014903.fpb/seq/22', 'SHIP/00014903.fpb/seq/23', 'SHIP/00014903.fpb/seq/24', 'SHIP/00014903.fpb/seq/25', 'SHIP/00014903.fpb/seq/26', 'SHIP/00014903.fpb/seq/27', 'SHIP/00014903.fpb/seq/28', 'SHIP/00014903.fpb/seq/29', 'SHIP/00014903.fpb/seq/30', 'SHIP/00014903.fpb/seq/31', 'SHIP/00014903.fpb/seq/32', 'SHIP/00014903.fpb/seq/33', 'SHIP/00014903.fpb/seq/34', 'SHIP/00014903.fpb/seq/35', 'SHIP/00014903.fpb/seq/36', 'SHIP/00014903.fpb/seq/37', 'SHIP/00014903.fpb/seq/38', 'SHIP/00014903.fpb/seq/39', 'SHIP/00014903.fpb/seq/40', 'SHIP/00014903.fpb/seq/41', 'SHIP/00014904.fpb/seq/0', 'SHIP/00014904.fpb/seq/1', 'SHIP/00014904.fpb/seq/2', 'SHIP/00014904.fpb/seq/3', 'SHIP/00014904.fpb/seq/4', 'SHIP/00014904.fpb/seq/5', 'SHIP/00014904.fpb/seq/6', 'SHIP/00014904.fpb/seq/7', 'SHIP/00014904.fpb/seq/8', 'SHIP/00014904.fpb/seq/9', 'SHIP/00014904.fpb/seq/10', 'SHIP/00014904.fpb/seq/11', 'SHIP/00014904.fpb/seq/12', 'SHIP/00014904.fpb/seq/13', 'SHIP/00014904.fpb/seq/14', 'SHIP/00014904.fpb/seq/15', 'SHIP/00014904.fpb/seq/16', 'SHIP/00014904.fpb/seq/17', 'SHIP/00014904.fpb/seq/18', 'SHIP/00014904.fpb/seq/19', 'SHIP/00014904.fpb/seq/20', 'SHIP/00014904.fpb/seq/21', 'SHIP/00014904.fpb/seq/22', 'SHIP/00014904.fpb/seq/23', 'SHIP/00014904.fpb/seq/24', 'SHIP/00014904.fpb/seq/25', 'SHIP/00014904.fpb/seq/26', 'SHIP/00014904.fpb/seq/27', 'SHIP/00014904.fpb/seq/28', 'SHIP/00014904.fpb/seq/29', 'SHIP/00014904.fpb/seq/30', 'SHIP/00014904.fpb/seq/31', 'SHIP/00014904.fpb/seq/32', 'SHIP/00014904.fpb/seq/33', 'SHIP/00014904.fpb/seq/34', 'SHIP/00014904.fpb/seq/35', 'SHIP/00014904.fpb/seq/36', 'SHIP/00014904.fpb/seq/37', 'SHIP/00014904.fpb/seq/38', 'SHIP/00014904.fpb/seq/39', 'SHIP/00014904.fpb/seq/40', 'SHIP/00014904.fpb/seq/41', 'SHIP/00014905.fpb/seq/0', 'SHIP/00014905.fpb/seq/1', 'SHIP/00014905.fpb/seq/2', 'SHIP/00014905.fpb/seq/3', 'SHIP/00014905.fpb/seq/4', 'SHIP/00014905.fpb/seq/5', 'SHIP/00014905.fpb/seq/6', 'SHIP/00014905.fpb/seq/7', 'SHIP/00014905.fpb/seq/8', 'SHIP/00014905.fpb/seq/9', 'SHIP/00014905.fpb/seq/10', 'SHIP/00014905.fpb/seq/11', 'SHIP/00014905.fpb/seq/12', 'SHIP/00014905.fpb/seq/13', 'SHIP/00014905.fpb/seq/14', 'SHIP/00014905.fpb/seq/15', 'SHIP/00014905.fpb/seq/16', 'SHIP/00014905.fpb/seq/17', 'SHIP/00014905.fpb/seq/18', 'SHIP/00014905.fpb/seq/19', 'SHIP/00014905.fpb/seq/20', 'SHIP/00014905.fpb/seq/21', 'SHIP/00014905.fpb/seq/22', 'SHIP/00014905.fpb/seq/23', 'SHIP/00014905.fpb/seq/24', 'SHIP/00014905.fpb/seq/25', 'SHIP/00014905.fpb/seq/26', 'SHIP/00014905.fpb/seq/27', 'SHIP/00014905.fpb/seq/28', 'SHIP/00014905.fpb/seq/29', 'SHIP/00014905.fpb/seq/30', 'SHIP/00014905.fpb/seq/31', 'SHIP/00014905.fpb/seq/33', 'SHIP/00014905.fpb/seq/34', 'SHIP/00014905.fpb/seq/35', 'SHIP/00014905.fpb/seq/36', 'SHIP/00014905.fpb/seq/37', 'SHIP/00014905.fpb/seq/38', 'SHIP/00014905.fpb/seq/39', 'SHIP/00014905.fpb/seq/40', 'SHIP/00014906.fpb/seq/0', 'SHIP/00014906.fpb/seq/1', 'SHIP/00014906.fpb/seq/2', 'SHIP/00014906.fpb/seq/3', 'SHIP/00014906.fpb/seq/4', 'SHIP/00014906.fpb/seq/5', 'SHIP/00014906.fpb/seq/6', 'SHIP/00014906.fpb/seq/7', 'SHIP/00014906.fpb/seq/8', 'SHIP/00014906.fpb/seq/9', 'SHIP/00014906.fpb/seq/10', 'SHIP/00014906.fpb/seq/11', 'SHIP/00014906.fpb/seq/12', 'SHIP/00014906.fpb/seq/13', 'SHIP/00014906.fpb/seq/14', 'SHIP/00014906.fpb/seq/15', 'SHIP/00014906.fpb/seq/16', 'SHIP/00014906.fpb/seq/17', 'SHIP/00014906.fpb/seq/18', 'SHIP/00014906.fpb/seq/19', 'SHIP/00014906.fpb/seq/20', 'SHIP/00014906.fpb/seq/21', 'SHIP/00014906.fpb/seq/22', 'SHIP/00014906.fpb/seq/23', 'SHIP/00014906.fpb/seq/24', 'SHIP/00014906.fpb/seq/25', 'SHIP/00014906.fpb/seq/26', 'SHIP/00014906.fpb/seq/27', 'SHIP/00014906.fpb/seq/28', 'SHIP/00014906.fpb/seq/29', 'SHIP/00014906.fpb/seq/30', 'SHIP/00014906.fpb/seq/31', 'SHIP/00014906.fpb/seq/32', 'SHIP/00014906.fpb/seq/33', 'SHIP/00014906.fpb/seq/34', 'SHIP/00014906.fpb/seq/35', 'SHIP/00014906.fpb/seq/36', 'SHIP/00014906.fpb/seq/37', 'SHIP/00014906.fpb/seq/38', 'SHIP/00014906.fpb/seq/39', 'SHIP/00014906.fpb/seq/40', 'SHIP/00014906.fpb/seq/41', 'SHIP/00014906.fpb/seq/42', 'SHIP/00014906.fpb/seq/43', 'SHIP/00014906.fpb/seq/44', 'SHIP/00014906.fpb/seq/45', 'SHIP/00014906.fpb/seq/46', 'SHIP/00014906.fpb/seq/47']
        self.assertEqual(429,len(ids))
        for key in ids:self.assertIsNone(re.search(r'\$n[。！？！，、：；）》」』]',self.rows[key]['target']),key)
        self.assertEqual('这扇门，$n好像从来没打开过。',self.row(14898,26)['target'])

    def test_town_whole_words_do_not_break_at_source_newlines(self):
        for resource,seq in [(1644,16),(14901,12),(14902,16),(14902,39),(14903,37),(14904,11)]:
            target=self.row(resource,seq)['target']
            for bad in ['一路$n顺风','饰品$n店','打$n断','占一次$n卜','当行$n商','阿泽翼$n。']:
                self.assertNotIn(bad,target)
        self.assertIn('占一次卜',self.row(14902,39)['target'])
        self.assertIn('当行商',self.row(14904,11)['target'])

    def test_town_control_count_and_great_magic_word_boundaries(self):
        for resource,seq,count in [(14394,0,2),(14895,5,2),(14895,17,2),(14898,16,2),(14901,12,2),(14902,13,3),(14903,13,2),(14904,11,2),(14906,13,2)]:
            self.assertEqual(count,self.row(resource,seq)['target'].count('$n'))
        self.assertIn('大魔法阵的攻击',self.row(14895,5)['target'])
        self.assertIn('身体一点点融化',self.row(14895,17)['target'])

    def test_town_rumors_and_opposing_views_remain_attributed(self):
        self.assertIn('这个假说',self.row(14900,3)['target'])
        self.assertIn('爷爷说是真的',self.row(14903,33)['target'])
        self.assertIn('听说',self.row(14906,32)['target'])
        self.assertIn('亚逊，并不都是坏',self.row(14903,20)['target'])
        self.assertIn('都是恶魔',self.row(14895,25)['target'])
        self.assertIn('共存',self.row(14906,26)['target'])

if __name__ == '__main__':
    unittest.main()
