"""Explicit bounded display-resource plans; reuse existing FPB and slot writers."""
from pathlib import Path
import json
import font_poc as core
from localization.text import rewrite_fpb, rewrite_fixed_slot
from translate.fpb import parse_fpb_raw, synthesize_implicit_seq0
from slot_resource import mirror_resource


def display_cases(config):
    result = []
    for plan in config.get('text_resources', []):
        for row in plan['targets']:
            suffix = f"seq/{row['seq']}" if plan['kind'] == 'fpb' else f"record/{row['profile']['record_id']}/field/0"
            result.append(dict(id=f"SHIP/{plan['resource']}/{suffix}", kind=plan['kind'],
                               target=row['target']))
    return result


def character_entries(config, root):
    if 'font_characters' not in config:
        return json.loads((root / config['glyph_map']).read_text('utf8'))['entries']
    path = (root / config['font_characters']).resolve()
    core.require(path.is_relative_to(root.resolve()), 'character inventory outside project')
    chars = json.loads(path.read_text('utf8'))['characters']
    core.require(isinstance(chars, list) and chars and all(isinstance(c, str) and len(c) == 1 and ord(c) >= 128 for c in chars)
                 and len(set(chars)) == len(chars), 'invalid character inventory')
    return [dict(character=c) for c in chars]


def apply_display_resources(ship, bundle, encoder, plans, fonts=None, width_estimator=None):
    core.require(isinstance(plans, list) and bool(plans), 'empty display resource plans')
    overrides, reports = {}, []
    for plan in plans:
        name = plan['resource']
        core.require(name in ship and name.lower() not in overrides, 'unknown or duplicate display resource')
        old = ship[name]
        core.require(core.digest(old) == plan['expected_sha256'], 'display resource fingerprint mismatch')
        rows = plan['targets']
        core.require(isinstance(rows, list) and bool(rows), 'empty display targets')
        if plan['kind'] == 'fpb':
            core.require(Path(name).suffix.lower() == '.fpb', 'FPB resource extension mismatch')
            ids = [row['seq'] for row in rows]
            core.require(all(type(i) is int and i >= 0 for i in ids) and len(set(ids)) == len(ids), 'duplicate or invalid FPB targets')
            _, windows, pool = parse_fpb_raw(old)
            views = {seq: pool[offset:offset + length] for seq, offset, length in synthesize_implicit_seq0(windows, len(pool))}
            for row in rows:
                core.require(row['seq'] in views, 'display sequence missing')
                core.require(core.digest(views[row['seq']]) == row['source_sha256'], 'display source window mismatch')
            modified, fields = rewrite_fpb(old, {row['seq']: row['target'] for row in rows}, encoder)
        elif plan['kind'] == 'fixed-display-slot':
            core.require(Path(name).suffix.lower() == '.tui', 'fixed display format not supported')
            ids = [row['profile']['record_id'] for row in rows]
            core.require(all(type(i) is int and i >= 0 for i in ids) and len(set(ids)) == len(ids), 'duplicate or invalid fixed targets')
            modified, fields = old, []
            for row in rows:
                profile = row['profile']
                core.require(profile['text_offset'] == 4 and profile['text_bytes'] == 256
                             and profile['header_size'] == 8 and profile['record_size'] == 516, 'unsupported bounded TUI field')
                core.require(type(row['max_estimated_pixels']) is int and row['max_estimated_pixels'] > 0, 'invalid width budget')
                modified, field = rewrite_fixed_slot(modified, profile, row['target'], encoder)
                if fonts is not None:
                    core.require(width_estimator is not None, 'width estimator missing')
                    widths = {name: width_estimator(row['target'], encoder, serial) for name, serial in fonts.items()}
                    core.require(all(max(values) <= row['max_estimated_pixels'] for values in widths.values()), 'display width budget exceeded')
                    field['candidate_widths'] = widths
                fields.append(field)
        else:
            raise ValueError('unsupported display resource kind')
        copies = plan['cached_copies']
        core.require(type(copies) is int and copies in (0, 1) and bundle.count(old) == copies, 'display cached copy mismatch')
        offset = None
        if copies:
            bundle, offset = mirror_resource(bundle, old, modified)
        overrides[name.lower()] = modified
        reports.append(dict(resource=name, kind=plan['kind'], fields=fields, cached_offset=offset,
                            original_sha256=core.digest(old), modified_sha256=core.digest(modified)))
    return overrides, bundle, reports
