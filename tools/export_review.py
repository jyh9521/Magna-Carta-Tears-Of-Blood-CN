"""Export a complete structural catalog and target drafts for local proofreading.

Original text stays in ignored output directories. No resource writes, implicit
translations, deduplicated IDs, or automatic review approvals are performed.
"""
from __future__ import annotations
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import font_poc as core
from validate_translation_batch import validate, glossary_terms


def join_targets(catalog, batches, terms):
    result = {}
    core.require(len({batch.get('locale') for batch in batches}) <= 1,
                 'mixed review locales')
    for batch in batches:
        validate(catalog, batch, terms)
        for entry in batch['entries']:
            core.require(entry['id'] not in result, 'overlapping translation batches')
            result[entry['id']] = entry
    return result


def review_row(source, targets, locale):
    target = targets.get(source['id'])
    return dict(source=source, source_text=source.get('references', {}).get(locale),
                target=target['target'] if target else '',
                translation_status=target['status'] if target else 'untranslated',
                reinsertion_authorized=False)


def page(title, body):
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width">'
            '<title>'+escape(title)+'</title><style>'
            'body{font:16px sans-serif;max-width:1200px;margin:2em auto;padding:1em}'
            'table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;'
            'padding:.5em;vertical-align:top}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
            'small{color:#555}</style><h1>'+escape(title)+'</h1>'+body+'</html>')


def export(catalog, targets, out):
    core.require(not out.exists() or not any(out.iterdir()), 'review output must be empty')
    out.mkdir(parents=True, exist_ok=True)
    locale = catalog['source_locale']
    counts = Counter(); index_rows = []
    # Full pools and resource audit metadata preserve bytes outside FPB views.
    with (out/'resource-metadata.jsonl').open('w', encoding='utf-8', newline='\n') as metadata:
        for resource in catalog['resources']:
            metadata.write(json.dumps({key:value for key,value in resource.items()
                                       if key != 'entries'}, ensure_ascii=False)+'\n')
    with (out/'review.jsonl').open('w', encoding='utf-8', newline='\n') as stream:
        for number, resource in enumerate(catalog['resources']):
            rows = [review_row(source, targets, locale) for source in resource['entries']]
            cells = []
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False)+'\n')
                counts['records'] += 1
                counts[row['translation_status']] += 1
                source = row['source']
                if source.get('decode') == 'failed': counts['decode_failed'] += 1
                if source.get('controls') == 'quarantined': counts['quarantined_controls'] += 1
                cells.append('<tr><td><small>'+escape(source['id'])+'<br>'+
                             escape(row['translation_status'])+'<br>'+
                             escape(source.get('semantic', 'unknown'))+'</small></td><td><pre>'+
                             escape(row['source_text'] if row['source_text'] is not None
                                    else '[decode failed] '+source.get('raw_hex', ''))+
                             '</pre></td><td><pre>'+escape(row['target'])+'</pre></td></tr>')
            filename = f'resource-{number:04d}.html'
            (out/filename).write_text(page(resource['resource'],
                '<p><a href="index.html">目录</a> · 原文和 ID 保持不变；初稿不等于已校对。</p>'
                '<table><tr><th>ID / 状态 / 语义</th><th>韩文原文</th><th>中文初稿</th></tr>'+
                ''.join(cells)+'</table>'), encoding='utf-8')
            translated = sum(row['translation_status'] != 'untranslated' for row in rows)
            index_rows.append('<tr><td><a href="'+filename+'">'+escape(resource['resource'])+
                              '</a></td><td>'+str(len(rows))+'</td><td>'+str(translated)+'</td></tr>')
    # These candidates are not merged into translation units or counted as dialogue.
    (out/'celfid-candidates.json').write_text(json.dumps(dict(
        candidates=catalog.get('celfid_candidates', []),
        resource_mirrors=catalog.get('celfid_resource_mirrors', [])),
        ensure_ascii=False, indent=2), encoding='utf-8')
    summary = dict(schema=1, source_iso_sha256=catalog['iso_sha256'],
                   resources=len(catalog['resources']), **dict(counts),
                   celfid_candidates=len(catalog.get('celfid_candidates', [])),
                   all_game_text_coverage='not established', reinsertion='not performed')
    (out/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (out/'index.html').write_text(page('全量已提取目录与中文初稿',
        '<p>结构字段、候选标识符、空字段和解码异常均保留。候选记录不等于可见文本。'
        '资源编号不表示剧情顺序。完整原文仅在本地保存；当前版本不执行导入。</p><pre>'+
        escape(json.dumps(summary, ensure_ascii=False, indent=2))+'</pre>'
        '<table><tr><th>资源</th><th>记录数</th><th>已译初稿 / 已校对</th></tr>'+
        ''.join(index_rows)+'</table>'), encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--batch', type=Path, action='append', default=[])
    parser.add_argument('--glossary', type=Path, default=ROOT/'GLOSSARY.md')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text('utf-8'))
    batches = [json.loads(path.read_text('utf-8')) for path in args.batch]
    targets = join_targets(catalog, batches, glossary_terms(args.glossary))
    out = core.output_directory(args.out)
    print('REVIEW EXPORT PASS '+json.dumps(export(catalog, targets, out), sort_keys=True))


if __name__ == '__main__': main()
