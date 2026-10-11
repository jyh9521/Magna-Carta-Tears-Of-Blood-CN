"""Camp language review and explicit source-variant decisions."""
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from validate_translation_batch import glossary_terms
from localization.text import protected_tokens


class CampNameContextTests(unittest.TestCase):
    def test_new_camp_batch_keeps_independent_reviewed_fields(self):
        batch = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        self.assertGreaterEqual(len(batch['entries']), 160)
        self.assertEqual(len({r['id'] for r in batch['entries']}), len(batch['entries']))
        self.assertTrue(all(r['status'] == 'reviewed' for r in batch['entries']))
        self.assertTrue(all('source_sha256' in r for r in batch['entries']))

    def test_canonical_azel_source_variants_and_male_profile(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['아세스'], terms['아젤'])
        self.assertEqual(terms['아세스'], '阿泽尔')
        profile = json.loads((ROOT / 'locales/zh-CN/character-reference.json').read_text('utf8'))
        row = next(r for r in profile['characters'] if r['canonical_source'] == '아젤')
        self.assertIn('아세스', row['source_aliases'])
        self.assertEqual(row['default_pronoun'], '他')
        self.assertFalse(row['alias_decision']['runtime_cache_linking_verified'])

    def test_alternative_encoding_does_not_rewrite_source_control_sequence(self):
        reference = '四天王とは？$n$n'
        raw = reference.encode('cp932')
        primary = raw.decode('cp949')
        self.assertEqual(primary.encode('cp949'), raw)
        self.assertEqual(raw.decode('cp932'), reference)
        self.assertEqual(protected_tokens(primary), protected_tokens(reference))

    def test_light_name_and_new_camp_pronouns_are_consistent(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['救援の光'], terms['구원의 빛'])
        batch = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in batch['entries']}
        self.assertEqual(rows['SHIP/00003609.cht/slot/1'], '她救过我的命。')
        self.assertIn('他当佣人', rows['SHIP/00005176.cht/slot/4'])
        self.assertTrue(all('阿塞斯' not in t for t in rows.values()))

    def test_camp_family_reply_keeps_source_slot_alignment(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertEqual(rows['SHIP/00005178.cht/slot/1'], '看起来挺像的。')
        self.assertIn('哪里像', rows['SHIP/00005178.cht/slot/2'])
        self.assertIn('纯真', rows['SHIP/00005178.cht/slot/17'])

    def test_lehas_and_reith_actual_female_referents(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertEqual(rows['SHIP/00005177.cht/slot/9'], '她很坚强……不会有事的。')
        self.assertEqual(rows['SHIP/00005177.cht/slot/16'], '我相信她……不会有事的。')
        self.assertIn('她应该会回到', rows['SHIP/00005176.cht/slot/85'])
        self.assertIn('一行人', rows['SHIP/00005177.cht/slot/0'])

    def test_three_letter_correspondents_have_canonical_names(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['칼라'], '卡拉')
        self.assertEqual(terms['엔쥬'], '恩茱')
        self.assertEqual(terms['로웨'], '罗薇')

    def test_alternate_rescue_location_replies_remain_distinct(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('阿玛巴德大道', rows['SHIP/00005180.cht/slot/35'])
        self.assertIn('拉埃杜山', rows['SHIP/00005180.cht/slot/40'])
        self.assertIn('不是啊，是阿玛巴德大道', rows['SHIP/00005180.cht/slot/41'])

    def test_rescued_girl_and_critique_keep_context_and_controls(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('她是阿玛巴德的巫女', rows['SHIP/00007533.cht/slot/9'])
        self.assertIn('替阿泽尔治疗', rows['SHIP/00007533.cht/slot/22'])
        critique = rows['SHIP/00008125.cht/slot/12']
        self.assertEqual(critique.count('$n'), 3)
        self.assertIn('斩断解不开的结', critique)
        self.assertIn('缎带', critique)

    def test_gendered_clergy_titles_and_idiom_disambiguation(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['대무자'], '大巫师')
        self.assertEqual(terms['독수공방'], '独守空房')
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('大巫师', rows['SHIP/00008127.cht/slot/1'])
        self.assertIn('巫女和巫师', rows['SHIP/00008127.cht/slot/67'])
        self.assertIn('独守空房', rows['SHIP/00008126.cht/slot/24'])

    def test_rianna_household_roles_and_ladrinne_female_reference(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertEqual(rows['SHIP/00008145.cht/slot/33'], '那种事当然是丈夫做啊！')
        self.assertIn('她就像母亲', rows['SHIP/00008145.cht/slot/2'])
        self.assertIn('保护她', rows['SHIP/00008145.cht/slot/13'])

    def test_justina_survivor_account_and_light_memories_controls(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertEqual(rows['SHIP/00008145.cht/slot/4'].count('$n'), 2)
        self.assertIn('神力', rows['SHIP/00008145.cht/slot/4'])
        self.assertIn('精神失常前', rows['SHIP/00008127.cht/slot/4'])
        self.assertIn('救赎之光', rows['SHIP/00012031.cht/slot/0'])

    def test_raul_trust_and_lehas_bereavement_keep_referents(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('劳尔先生', rows['SHIP/00012035.cht/slot/58'])
        self.assertIn('相信他', rows['SHIP/00012035.cht/slot/58'])
        self.assertIn('最后一次见面', rows['SHIP/00012037.cht/slot/0'])
        self.assertIn('为她做过', rows['SHIP/00012037.cht/slot/0'])

    def test_bayer_opposing_reply_and_apple_analogy_remain_literal(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('开放', rows['SHIP/00012031.cht/slot/20'])
        self.assertIn('封闭', rows['SHIP/00012031.cht/slot/21'])
        self.assertIn('苹果', rows['SHIP/00012036.cht/slot/17'])
        self.assertNotIn('道歉', rows['SHIP/00012036.cht/slot/17'])
        self.assertIn('不是你自己想要的结果', rows['SHIP/00012036.cht/slot/19'])

    def test_chris_parents_and_ladrinne_female_trust_referents(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('她一定很爱他', rows['SHIP/00012038.cht/slot/49'])
        self.assertIn('她被人误会', rows['SHIP/00012039.cht/slot/18'])
        self.assertIn('卡林兹', rows['SHIP/00012039.cht/slot/19'])
        self.assertIn('信任他', rows['SHIP/00012039.cht/slot/19'])

    def test_rianna_letter_and_calintz_response_controls(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('莉安娜', rows['SHIP/00012041.cht/slot/10'])
        self.assertIn('埃琉内德', rows['SHIP/00012041.cht/slot/11'])
        self.assertEqual(rows['SHIP/00012038.cht/slot/16'].count('$n'), 1)
        self.assertIn('真正要说的事', rows['SHIP/00012041.cht/slot/19'])

    def test_camp_source_gap_batch_covers_all_1504_independent_fields(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        self.assertEqual(len(b['entries']), 1504)
        self.assertEqual(len({r['id'] for r in b['entries']}), 1504)
        self.assertTrue(all(r['status'] == 'reviewed' and r['source_sha256'] for r in b['entries']))

    def test_eonis_female_speaker_does_not_become_her_male_love_interest(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        target = rows['SHIP/00012047.cht/slot/32']
        self.assertIn('那个男人', target)
        self.assertIn('让他看向我', target)
        self.assertNotIn('我是男人', target)
        self.assertIn('父子', rows['SHIP/00016764.cht/slot/14'])

    def test_trinity_buttons_eight_kan_and_bonus_example_preserved(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('×按钮', rows['SHIP/00016655.cht/slot/1'])
        self.assertIn('○按钮', rows['SHIP/00016655.cht/slot/1'])
        self.assertIn('△按钮', rows['SHIP/00016655.cht/slot/24'])
        for element in ['天', '山', '江', '火', '水', '雷', '地', '风']:
            self.assertIn(element, rows['SHIP/00016655.cht/slot/8'])
        for number in ['1000', '1010', '1510', '+2', '+5']:
            self.assertIn(number, rows['SHIP/00016655.cht/slot/42'])

    def test_kan_modes_and_zero_to_five_shields_keep_source_limits(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('零到五个', rows['SHIP/00016655.cht/slot/34'])
        self.assertIn('三个到七个', rows['SHIP/00016655.cht/slot/20'])
        self.assertIn('罗刹模式无法使用护盾', rows['SHIP/00016655.cht/slot/30'])
        self.assertIn('恢复', rows['SHIP/00016655.cht/slot/3'])

    def test_common_verbs_do_not_match_molly_name(self):
        terms = dict(glossary_terms(ROOT / 'GLOSSARY.md'))
        self.assertEqual(terms['몰리'], '莫莉')
        self.assertEqual(terms['위기에 몰리'], '陷入')
        self.assertEqual(terms['죄인으로 몰리'], '被当成罪犯')

    def test_turbo_source_bound_style_labels_use_canonical_name(self):
        b = json.loads((ROOT / 'locales/zh-CN/style-description-review-01.json').read_text('utf8'))
        rows = [r for r in b['entries'] if r['target'].startswith('图尔博_物理攻击_')]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r['reinsertion_policy'] == 'translate' for r in rows))
        self.assertTrue(all(r['status'] == 'reviewed' for r in rows))

    def test_reith_sacrifice_and_amila_queen_referents(self):
        b = json.loads((ROOT / 'locales/zh-CN/camp-conversation-gap-review-01.json').read_text('utf8'))
        rows = {r['id']: r['target'] for r in b['entries']}
        self.assertIn('她是亚逊', rows['SHIP/00012050.cht/slot/21'])
        self.assertIn('她也还是救了我', rows['SHIP/00012050.cht/slot/28'])
        self.assertIn('女王', rows['SHIP/00016762.cht/slot/16'])
        self.assertIn('恢复术', rows['SHIP/00016768.cht/slot/11'])


if __name__ == '__main__':
    unittest.main()
