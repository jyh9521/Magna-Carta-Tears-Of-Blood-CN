"""Source-bound story additions and bilingual map naming decisions."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from validate_translation_batch import glossary_terms
from localization.text import protected_tokens


class StoryGapContextTests(unittest.TestCase):
    def batch(self, name='story-gap-review-01'):
        return json.loads((ROOT / f'locales/zh-CN/{name}.json').read_text('utf8'))['entries']

    def test_independent_reviewed_fields_and_policy(self):
        rows = self.batch()
        self.assertEqual(len(rows), 1678)
        self.assertEqual(len({e['id'] for e in rows}), 1678)
        self.assertTrue(all(e['status'] == 'reviewed' and len(e['source_sha256']) == 64 for e in rows))
        self.assertEqual(sum(e.get('reinsertion_policy') == 'pending-role-review' for e in rows), 0)
        profile=json.loads((ROOT/'locales/zh-CN/proofreading/fpb-chat-consumers.json').read_text('utf8'))
        self.assertEqual(len(profile['bindings']),105)
        by={e['id']:e for e in rows}
        for b in profile['bindings']:
            self.assertEqual((by[b['id']]['source_sha256'],by[b['id']]['target'],by[b['id']]['reinsertion_policy']),(b['source_sha256'],b['target'],'translate'))

    def test_country_and_faction_aliases(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['ガル?ト'], '吉拉特')
        self.assertEqual(terms['紅の旋風'], '血泪')
        rows = {e['id']: e['target'] for e in self.batch('world-map-review-01')}
        for i in (26, 50, 51):
            self.assertIn('吉拉特', rows[f'SHIP/00001643.nod/record-index/{i}/field/1'])
        self.assertIn('血泪', rows['SHIP/00001643.nod/record-index/38/field/1'])

    def test_old_story_faction_keeps_control(self):
        e = next(e for e in self.batch('story-review-01') if e['id'] == 'SHIP/00005182.fpb/seq/15')
        self.assertEqual(e['target'], '血泪啊，$n真是一群难以相处的麻烦家伙。')

    def test_war_question_retains_line_control(self):
        e = next(e for e in self.batch() if e['id'] == 'SHIP/00001939.fpb/seq/15')
        self.assertEqual(e['target'], '赢得这场战争以后，$n我们梦想中的世界就会到来吗？')

    def test_letter_and_numbered_reference_labels(self):
        targets = [e['target'] for e in self.batch()]
        # Editorial date spacing normalized against the identical letter header.
        self.assertIn('XX月XX日$n致亲爱的阿莉安', targets)
        self.assertIn('N约书亚回忆录2', targets)
        self.assertFalse(any('—' in t for t in targets))

    def test_strict_alternative_reading_keeps_source_and_control(self):
        text = '隊長！$n'
        raw = text.encode('cp932')
        primary = raw.decode('cp949')
        self.assertEqual(primary.encode('cp949'), raw)
        self.assertEqual(raw.decode('cp932'), text)
        self.assertEqual(protected_tokens(primary), protected_tokens(text))

    def test_northern_creature_project_choice(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['ブラストワ?ム'], '霜龙')
        e = next(e for e in self.batch() if e['id'] == 'SHIP/00005065.fpb/seq/16')
        self.assertEqual(e['target'], '所以霜龙又开始$n向北进攻了。')

    def test_discount_means_reduction_not_price_fraction(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertEqual(rows['SHIP/00005182.fpb/seq/23'], '全部商品优惠25％。')
        self.assertEqual(rows['SHIP/00005182.fpb/seq/24'], '全部商品优惠10％。')

    def test_mother_son_and_ancestor_alias(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('拉德琳娜大巫女', rows['SHIP/00015211.fpb/seq/0'])
        self.assertEqual(rows['SHIP/00015211.fpb/seq/1'], '那个儿子就是阿格雷安将军。')
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['시도 에스타로트'], terms['시드 에스타로트'])
        self.assertEqual(terms['시도 에스타로트'], terms['シ?ド?エスタロット'])

    def test_development_and_incantation_requires_native_text_profile(self):
        rows = {e['id']: e for e in self.batch()}
        profile=json.loads((ROOT/'locales/zh-CN/proofreading/fpb-chat-consumers.json').read_text('utf8'))
        bindings={b['id']:b for b in profile['bindings']}
        self.assertTrue(profile['static_protocol_verified'])
        self.assertFalse(profile['specific_event_execution_verified'])
        for id in ['SHIP/00005666.fpb/seq/7', 'SHIP/00005686.fpb/seq/8',
                   'SHIP/00007360.fpb/seq/19', 'SHIP/00007682.fpb/seq/1',
                   'SHIP/00008210.fpb/seq/18', 'SHIP/00011943.fpb/seq/18']:
            self.assertEqual(rows[id]['reinsertion_policy'], 'translate')
            self.assertEqual((rows[id]['source_sha256'],rows[id]['target']),(bindings[id]['source_sha256'],bindings[id]['target']))

    def test_emma_and_player_world_claims_preserved(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertEqual(rows['SHIP/00015213.fpb/seq/28'], '然后和艾玛结婚。')
        self.assertIn('4条胳膊', rows['SHIP/00015214.fpb/seq/32'])
        self.assertIn('声称', rows['SHIP/00015214.fpb/seq/25'])
        self.assertIn('没有得到证实', rows['SHIP/00015208.fpb/seq/9'])

    def test_geographical_road_alias_project_choice(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['レスタ?'], terms['레스티'])
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('米雷娜大道', rows['SHIP/00005182.fpb/seq/33'])
        self.assertIn('米雷娜大道', rows['SHIP/00015099.fpb/seq/2'])
        self.assertEqual(terms['ミルナ'], terms['미레나'])
        # Geography supports naming; no runtime cache/ID merge is asserted.

    def test_lehas_loss_referent_is_female(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('蕾哈丝', rows['SHIP/00015219.fpb/seq/12'])
        self.assertIn('她', rows['SHIP/00015219.fpb/seq/13'])
        self.assertIn('她', rows['SHIP/00015219.fpb/seq/14'])
        self.assertNotIn('他', rows['SHIP/00015219.fpb/seq/14'])

    def test_agreian_rescue_and_mother_question_are_distinct(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('他带着', rows['SHIP/00015219.fpb/seq/4'])
        self.assertIn('真的是母子吗', rows['SHIP/00015215.fpb/seq/27'])
        self.assertIn('没有天生的神力', rows['SHIP/00015217.fpb/seq/6'])

    def test_shaman_and_artifact_adjective_disambiguation(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['무자비'], '残忍')
        self.assertEqual(terms['신기해서'], '稀奇')
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('亚逊残忍', rows['SHIP/00015220.fpb/seq/1'])
        self.assertIn('稀奇', rows['SHIP/00015216.fpb/seq/22'])

    def test_magic_origin_theory_stays_unverified(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('还不是经过证实', rows['SHIP/00015217.fpb/seq/11'])
        self.assertEqual(protected_tokens(rows['SHIP/00015217.fpb/seq/10']), ['$n', '$n'])

    def test_familiar_strategy_remains_a_question(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertTrue(rows['SHIP/00015218.fpb/seq/17'].endswith('？'))
        self.assertIn('四天王', rows['SHIP/00015218.fpb/seq/17'])
        self.assertIn('100个', rows['SHIP/00015222.fpb/seq/1'])

    def test_emon_coexistence_viewpoints_do_not_collapse(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('完全可以共存', rows['SHIP/00015226.fpb/seq/0'])
        self.assertIn('并不是', rows['SHIP/00015226.fpb/seq/16'])
        self.assertIn('被抛弃', rows['SHIP/00015226.fpb/seq/17'])
        self.assertEqual(dict(glossary_terms(ROOT / 'GLOSSARY.md'))['애문 공방 주인'], '埃蒙工坊老板')

    def test_frontline_reports_preserve_contradiction(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('不再出现', rows['SHIP/00015227.fpb/seq/21'])
        self.assertIn('最前方', rows['SHIP/00015227.fpb/seq/22'])
        self.assertEqual(rows['SHIP/00015227.fpb/seq/23'], '到底哪一边才是真的？')

    def test_praise_does_not_assert_general_nonhuman_species(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertEqual(rows['SHIP/00015227.fpb/seq/27'], '阿格雷安将军简直超越了凡人。')
        self.assertIn('超越人类的英雄', rows['SHIP/00015227.fpb/seq/28'])
        self.assertIn('国王', rows['SHIP/00015228.fpb/seq/1'])

    def test_stone_disease_and_wanted_child_numbers(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('石化', rows['SHIP/00015222.fpb/seq/23'])
        self.assertIn('没有证实', rows['SHIP/00015222.fpb/seq/23'])
        self.assertIn('5岁男孩', rows['SHIP/00015222.fpb/seq/29'])
        self.assertEqual(dict(glossary_terms(ROOT / 'GLOSSARY.md'))['5살짜리 소년'], '5岁男孩')

    def test_husband_reference_and_queen_health_are_not_swapped(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('丈夫', rows['SHIP/00015228.fpb/seq/12'])
        self.assertIn('阿米拉女王的健康', rows['SHIP/00015223.fpb/seq/26'])
        self.assertTrue(rows['SHIP/00015223.fpb/seq/26'].endswith('？'))

    def test_dream_man_and_queen_sister_referents(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('男人', rows['SHIP/00015228.fpb/seq/30'])
        self.assertIn('他', rows['SHIP/00015228.fpb/seq/31'])
        self.assertIn('阿米拉女王', rows['SHIP/00015232.fpb/seq/25'])
        self.assertIn('妹妹', rows['SHIP/00015232.fpb/seq/25'])
        self.assertEqual(rows['SHIP/00015232.fpb/seq/28'], '她不只是一位大巫女。')

    def test_wood_and_petrification_disease_descriptions_are_distinct(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('树皮', rows['SHIP/00015232.fpb/seq/7'])
        self.assertIn('石化病', rows['SHIP/00015232.fpb/seq/8'])
        self.assertIn('虽然只是传说', rows['SHIP/00015232.fpb/seq/6'])

    def test_queen_death_is_rumour_and_female_reference(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertTrue(rows['SHIP/00015235.fpb/seq/3'].endswith('？'))
        self.assertIn('她真的死了', rows['SHIP/00015235.fpb/seq/5'])
        self.assertIn('没有神力', rows['SHIP/00015217.fpb/seq/6'].replace('天生的', ''))

    def test_only_son_and_romantic_child_pronouns(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('唯一的儿子', rows['SHIP/00015233.fpb/seq/24'])
        self.assertIn('她', rows['SHIP/00015233.fpb/seq/30'])
        self.assertEqual(rows['SHIP/00015234.fpb/seq/35'], '我就是要跟他结婚！')

    def test_general_retreat_criticism_and_casualty_defence_both_kept(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('后退', rows['SHIP/00015235.fpb/seq/25'])
        self.assertIn('阵亡人数', rows['SHIP/00015235.fpb/seq/28'])
        self.assertEqual(protected_tokens(rows['SHIP/00015235.fpb/seq/29']), ['$n'])

    def test_library_lovers_and_homeland_names(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['트리카스'], '特里卡斯')
        self.assertEqual(terms['유스틴'], '尤丝汀')
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('亚逊之女', rows['SHIP/00015890.fpb/seq/3'])
        self.assertIn('卡尔提安克罗斯', rows['SHIP/00015891.fpb/seq/0'])

    def test_unfinished_book_fragments_are_not_completed_by_invention(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertTrue(rows['SHIP/00015886.fpb/seq/1'].endswith('……'))
        self.assertTrue(rows['SHIP/00015893.fpb/seq/2'].endswith('……'))
        self.assertTrue(rows['SHIP/00015890.fpb/seq/4'].endswith('……'))

    def test_blood_of_each_side_and_return_husband_translation(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertEqual(rows['SHIP/00015240.fpb/seq/27'], '把丈夫还给我！')
        self.assertIn('自己流过', rows['SHIP/00015240.fpb/seq/18'])
        self.assertIn('对方流过', rows['SHIP/00015240.fpb/seq/19'])

    def test_long_book_controls_and_technical_counts_preserved(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertEqual(protected_tokens(rows['SHIP/00015890.fpb/seq/1']), ['$n'] * 6)
        self.assertIn('万人', rows['SHIP/00015893.fpb/seq/1'])
        self.assertIn('数十倍乃至数百倍', rows['SHIP/00015893.fpb/seq/1'])
        self.assertIn('30年', rows['SHIP/00015236.fpb/seq/19'])

    def test_fragment_and_salvation_light_kept_canonical(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('天之碎片', rows['SHIP/00015801.fpb/seq/0'])
        self.assertIn('救赎之光', rows['SHIP/00015801.fpb/seq/0'])
        self.assertFalse(any('—' in e['target'] for e in self.batch()))

    def test_migration_ship_counts_and_names_remain_explicit(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('120多艘', rows['SHIP/00015903.fpb/seq/5'])
        self.assertIn('只有4艘', rows['SHIP/00015903.fpb/seq/5'])
        for name in ('拜耶尔号', '马拉卡特号', '阿玛巴德号', '吉拉特号'):
            self.assertIn(name, rows['SHIP/00015903.fpb/seq/6'])

    def test_trailer_references_are_not_approved_for_import(self):
        rows = {e['id']: e for e in self.batch()}
        for i in (0, 1, 2):
            self.assertEqual(rows[f'SHIP/00016143.fpb/seq/{i}']['reinsertion_policy'], 'translate')

    def test_tutorial_element_polarities_preserved(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        for i, pattern in ((0, '雷之卡恩（阳阴阴）'), (2, '地之卡恩（阴阴阴）'),
                           (3, '江之卡恩（阳阳阴）'), (5, '天（阳阳阳）'), (6, '山之卡恩（阴阴阳）')):
            self.assertIn(pattern, rows[f'SHIP/00016573.fpb/seq/{i}'])

    def test_style_number_statement_not_silently_corrected(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('3个或更多', rows['SHIP/00016587.fpb/seq/7'])
        self.assertIn('只有2个', rows['SHIP/00016587.fpb/seq/9'])
        self.assertEqual(dict(glossary_terms(ROOT / 'GLOSSARY.md'))['난화상렬류'], '乱火翔烈掌流')

    def test_maze_controls_and_aircraft_number(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('右摇杆', rows['SHIP/00016697.fpb/seq/10'])
        self.assertIn('360度', rows['SHIP/00016697.fpb/seq/10'])
        self.assertIn('29号', rows['SHIP/00016642.fpb/seq/3'])

    def test_memory_vision_is_female_lise_not_unknown_male(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('小时候的自己', rows['SHIP/00016693.fpb/seq/1'])
        self.assertIn('她就像烟', rows['SHIP/00016693.fpb/seq/3'])
        self.assertIn('抓住对方', rows['SHIP/00016040.fpb/seq/0'])

    def test_crimson_stigma_halves_physical_and_magical_damage(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        text = rows['SHIP/00016831.fpb/seq/0']
        self.assertIn('真红的圣痕', text)
        self.assertIn('菲尼克斯', text)
        self.assertIn('伤害减半', text)
        self.assertIn('物理攻击', text)
        self.assertIn('魔法攻击', text)

    def test_muen_and_rosteyn_family_context(self):
        rows = {e['id']: e['target'] for e in self.batch()}
        self.assertIn('莉丝大人唯一的血亲', rows['SHIP/00015943.fpb/seq/4'])
        self.assertIn('缪恩大人', rows['SHIP/00015943.fpb/seq/13'])
        self.assertIn('我儿子克里斯', rows['SHIP/00016642.fpb/seq/0'])
