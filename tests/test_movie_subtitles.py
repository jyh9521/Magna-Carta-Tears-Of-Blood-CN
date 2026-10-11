import unittest
from pathlib import Path
import sys
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_movie_subtitles import centiseconds,stamp,reference_events,translated_events,wrap_pixels,wrap_units,render_ass


class Font:
    def getmetrics(self): return (28,7)
    def getlength(self,text): return len(text)*10
    def getname(self): return ('Fixture Font','Regular')


class MovieSubtitlesTests(unittest.TestCase):
    def test_timestamp_roundtrip(self):
        for n in (0,1,59,100,5999,6000,360001,999999):self.assertEqual(centiseconds(stamp(n)),n)
    def test_invalid_timestamps(self):
        for s in ('0:99:01.00','0:00:61.00','0:00:01.000','-1:00:00.00'):
            with self.assertRaises(ValueError):centiseconds(s)
    def test_event_parse_commas(self):
        self.assertEqual(reference_events('Dialogue: 0,0:00:01.00,0:00:02.00,T,,0,0,0,,a,b')[0]['original'],'a,b')
    def test_nonpositive(self):
        with self.assertRaises(ValueError):reference_events('Dialogue: 0,0:00:02.00,0:00:01.00,T,,0,0,0,,a')
    def test_group_near_times(self):
        r=[dict(start=100,end=200,drawing=False),dict(start=99,end=200,drawing=False)]
        e=translated_events(r,['甲','乙']);self.assertEqual(len(e),1);self.assertEqual(e[0]['target'],'甲乙');self.assertEqual(e[0]['start'],99)
    def test_merge_duplicate_contiguous(self):
        r=[dict(start=100,end=200,drawing=False),dict(start=200,end=220,drawing=False)]
        self.assertEqual(translated_events(r,['甲','甲'])[0]['end'],220)
    def test_no_merge_distinct_cues(self):
        r=[dict(start=100,end=200,drawing=False),dict(start=250,end=300,drawing=False)]
        self.assertEqual(len(translated_events(r,['甲','甲'])),2)
    def test_drawings_only_null(self):
        self.assertEqual(translated_events([dict(start=1,end=2,drawing=True)],[None]),[])
        with self.assertRaises(ValueError):translated_events([dict(start=1,end=2,drawing=False)],[None])
    def test_reject_control_injection(self):
        for target in ('{x}','a\\b','a\nb','a\x00b'):
            with self.assertRaises(ValueError):translated_events([dict(start=1,end=2,drawing=False)],[target])
    def test_count_mismatch(self):
        with self.assertRaises(ValueError):translated_events([],['甲'])
    def test_blank_not_subtitle(self):
        self.assertEqual(translated_events([dict(start=1,end=2,drawing=False)],['']),[])
    def test_wrap_exact_pixels(self):
        self.assertEqual(wrap_pixels('甲乙丙丁',Font(),20),['甲乙','丙丁'])
    def test_punctuation_not_at_start(self):
        self.assertEqual(wrap_pixels('甲乙，丙',Font(),20),['甲','乙，','丙'])
    def test_wrap_overflow(self):
        with self.assertRaises(ValueError):wrap_pixels('甲乙丙丁',Font(),10,max_lines=3)
    def test_glyph_overflow(self):
        with self.assertRaises(ValueError):wrap_pixels('甲',Font(),5)
    def test_protected_name_not_split(self):
        self.assertEqual(wrap_pixels('甲埃彭塔德乙',Font(),40,protected=['埃彭塔德']),['甲','埃彭塔德','乙'])
    def test_protected_name_overflow(self):
        with self.assertRaises(ValueError):wrap_pixels('埃彭塔德',Font(),30,protected=['埃彭塔德'])
    def render(self,rows,**kw):
        pil=SimpleNamespace(ImageFont=SimpleNamespace(truetype=lambda *args:Font()))
        with patch.dict(sys.modules,{'PIL':pil}):return render_ass(rows,'FONT',640,352,**kw)
    def test_no_background_or_drawing(self):
        ass,rows=self.render([dict(start=100,end=200,target='测试')])
        self.assertNotIn('Style: Mask',ass);self.assertNotIn('\\p1',ass)
        self.assertIn('BorderStyle, Outline',ass);self.assertIn('\\pos(320,242)',ass)
        self.assertFalse(rows[0]['opaque_background'])
    def test_story_also_no_background(self):
        ass,rows=self.render([dict(start=100,end=200,target='故事文字')],story_panel=True)
        self.assertNotIn('Mask',ass);self.assertIn('\\an2',ass)
        self.assertFalse(rows[0]['opaque_background'])
    def test_opaque_mask_rejected(self):
        with self.assertRaises(ValueError):self.render([],mask=True)
    def test_invalid_position_rejected(self):
        for ratio in (0.1,1.0,float('nan')):
            with self.assertRaises(ValueError):self.render([],bottom_ratio=ratio)
    def test_long_text_paginated_by_area_not_two_lines(self):
        text='甲'*180
        _,rows=self.render([dict(start=100,end=1000,target=text)])
        self.assertEqual(''.join(r['target'] for r in rows),text)
        self.assertTrue(any(len(r['lines'])>2 for r in rows))
        self.assertTrue(all(len(r['lines'])<=r['geometry_line_capacity'] for r in rows))
        self.assertEqual(rows[0]['start'],100);self.assertEqual(rows[-1]['end'],1000)
        self.assertTrue(all(a['end']==b['start'] for a,b in zip(rows,rows[1:])))
    def test_user_movie_scope_complete_disjoint(self):
        import json
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'locales/zh-CN/movie-review-scope.json').read_text('utf8'))
        self.assertEqual(len(d['subtitle_required']),25);self.assertEqual(len(d['no_subtitles']),21)
        self.assertFalse(set(d['subtitle_required']) & set(d['no_subtitles']))
        self.assertIn('997777',d['no_subtitles'])
    def test_removed_movies_not_in_active_translation(self):
        import json
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'locales/zh-CN/movie-dialogue-01.json').read_text('utf8'))
        self.assertNotIn('180217',d['movies']);self.assertNotIn('1802171',d['movies'])
        self.assertEqual(len(d['movies']),23)
        self.assertEqual(sum(bool(t) for t in d['movies']['189992']),20)
        self.assertFalse(any(t for t in d['movies']['189992'][20:]))
    def test_punctuation_cluster_never_starts_line(self):
        self.assertEqual(wrap_pixels('甲乙，？！丙',Font(),40),['甲','乙，？！','丙'])
    def test_leading_punctuation_rejected(self):
        for text in ('，甲','……甲','。甲'):
            with self.assertRaises(ValueError):wrap_pixels(text,Font(),100)
    def test_right_rectangle_position_and_multiline(self):
        ass,rows=self.render([dict(start=100,end=1000,target='甲'*90)],safe_region=[320,246,628,338],font_size=18)
        self.assertIn('\\pos(474,334)',ass)
        self.assertEqual(rows[0]['geometry_line_capacity'],3)
        self.assertGreater(len(rows[0]['lines']),2)
        self.assertEqual(''.join(x['target'] for x in rows),'甲'*90)
    def test_invalid_rectangle_rejected(self):
        for region in ([640,200,700,300],[310,300,620,200],[310,330,620,335]):
            with self.assertRaises(ValueError):self.render([],safe_region=region)
    def test_dashes_rejected(self):
        for dash in ('\u2014','\u2013','\u2015','-'):
            with self.assertRaises(ValueError):self.render([dict(start=100,end=200,target='甲'+dash+'乙')])
    def test_active_movie_targets_no_dash_or_initial_punctuation(self):
        import json,unicodedata
        root=Path(__file__).resolve().parents[1]
        for name in ('movie-dialogue-01.json','movie-story-01.json'):
            d=json.loads((root/'locales/zh-CN'/name).read_text('utf8'))
            for entries in d['movies'].values():
                for entry in entries:
                    text=entry['target'] if isinstance(entry,dict) else entry
                    if not text:continue
                    self.assertFalse(any(unicodedata.category(c)=='Pd' for c in text))
                    self.assertFalse(unicodedata.category(text[0]).startswith('P'))
    def test_dialogue_layout_rectangles_inside_red_region(self):
        import json
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'locales/zh-CN/movie-dialogue-01.json').read_text('utf8'))
        layouts=[v for v in d['movie_layout'].values() if 'safe_region' in v]
        self.assertEqual(len(layouts),21)
        for v in layouts:
            x1,y1,x2,y2=v['safe_region']
            self.assertGreaterEqual(x1,310);self.assertGreaterEqual(y1,246)
            self.assertLessEqual(x2,628);self.assertLessEqual(y2,338)

    def test_pixel_metric_normalization_and_row_pitch(self):
        ass,rows=self.render([dict(start=100,end=1000,target='甲'*90)],safe_region=[449,246,627,338],font_size=24,pixel_font_size=True)
        self.assertIn('Style: Text,Fixture Font,35,',ass)
        self.assertIn('\\pos(538,278)',ass)
        self.assertIn('\\pos(538,306)',ass)
        self.assertIn('\\pos(538,334)',ass)
        self.assertEqual(rows[0]['geometry_line_capacity'],3)
        self.assertEqual(rows[0]['ass_font_size'],35)
        self.assertEqual(''.join(r['target'] for r in rows),'甲'*90)
        self.assertTrue(all(len(r['lines'])<=3 for r in rows))
        self.assertEqual(len(reference_events(ass)),sum(len(r['lines']) for r in rows))

    def test_pixel_mode_is_opt_in(self):
        ass,rows=self.render([dict(start=100,end=200,target='测试')])
        self.assertIn('Style: Text,Fixture Font,20,',ass)
        self.assertFalse(rows[0]['pixel_font_size'])

    def test_all_right_dialogue_fonts_enlarged(self):
        import json
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'locales/zh-CN/movie-dialogue-01.json').read_text('utf8'))
        for name,v in d['movie_layout'].items():
            if 'safe_region' in v:
                self.assertEqual(v['font_size'],24)
                self.assertTrue(v['pixel_font_size'])
            else:self.assertNotIn('pixel_font_size',v)

    def test_atomic_phrase_not_split(self):
        self.assertEqual(wrap_units(['他说','无论','作出什么判决，','他都会服从。'],Font(),70),['他说无论','作出什么判决，','他都会服从。'])

    def test_atomic_phrase_overflow_rejected_not_split(self):
        with self.assertRaises(ValueError):wrap_units(['作出什么判决，'],Font(),60)

    def test_atomic_phrase_punctuation_and_controls_rejected(self):
        for units in ([],[''],['，判决'],['{注入}'],['甲\\乙']):
            with self.assertRaises(ValueError):wrap_units(units,Font(),100)

    def test_reviewed_page_boundaries_retained(self):
        text='他说无论作出什么判决，他都会服从。'
        review=[dict(target=text,page_units=[['他说','无论'],['作出什么判决，','他都会服从。']])]
        ass,rows=self.render([dict(start=100,end=1000,target=text)],safe_region=[449,246,627,338],font_size=24,pixel_font_size=True,semantic_pages=review)
        self.assertEqual([r['target'] for r in rows],['他说无论','作出什么判决，他都会服从。'])
        self.assertEqual(''.join(r['target'] for r in rows),text)
        self.assertTrue(all(r['semantic_reviewed'] for r in rows))
        self.assertEqual(rows[0]['end'],rows[1]['start'])

    def test_reviewed_target_mismatch_and_missing_text_rejected(self):
        for review in ([],[dict(target='另文',page_units=[['另文']])],[dict(target='原文',page_units=[['原']])]):
            with self.assertRaises(ValueError):self.render([dict(start=100,end=500,target='原文')],semantic_pages=review)

    def test_reviewed_height_overflow_rejected_not_repaginated(self):
        with self.assertRaises(ValueError):self.render([dict(start=100,end=1000,target='甲'*90)],safe_region=[449,246,627,338],font_size=24,semantic_pages=[dict(target='甲'*90,page_units=[['甲']*90])])

    def test_reviewed_glossary_name_split_rejected(self):
        with self.assertRaises(ValueError):self.render([dict(start=100,end=500,target='卡琳兹')],semantic_pages=[dict(target='卡琳兹',page_units=[['卡琳'],['兹']])])

    def test_all_21_semantic_reviews_match_source_and_keep_phrases(self):
        import json
        from PIL import ImageFont
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'locales/zh-CN/movie-dialogue-01.json').read_text('utf8'))
        rev=json.loads((root/'locales/zh-CN'/d['layout_review']).read_text('utf8'))
        names={n for n,v in d['movie_layout'].items() if 'safe_region' in v}
        self.assertEqual(set(rev['movies']),names);self.assertEqual(len(names),21)
        total=0
        for n,review in rev['movies'].items():
            original=reference_events((root/d['reference']/(n+'.ass')).read_text('utf-8-sig'))
            rows=translated_events(original,d['movies'][n]);self.assertEqual(len(rows),len(review))
            for row,entry in zip(rows,review):
                self.assertEqual(row['target'],entry['target'])
                self.assertEqual(''.join(t for page in entry['page_units'] for t in page),entry['target'])
                total+=1
        self.assertEqual(total,115)
        self.assertIn(['他说','无论','作出什么判决，','他都会服从。'],rev['movies']['181307'][7]['page_units'])


if __name__=='__main__':unittest.main()
