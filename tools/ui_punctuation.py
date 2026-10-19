"""Explicit UI-only sentence-end policy; narrative text is not normalized."""
import re
import unicodedata


def single_sentence_period(text):
    body = text.rstrip()
    return (body.endswith('。') and body.count('。') == 1
            and not any(c in body[:-1] for c in '，,!?！？；;…'))


def single_clause_period(text):
    """Current no-other-punctuation rule; legacy recipes keep their v1 behavior."""
    body = text.rstrip()
    visible = re.sub(r'\$n|\$D\d{2}', '', body[:-1])
    visible = re.sub(r'(?<=\d)\.(?=\d)', '', visible)
    return (body.endswith('。') and bool(visible.strip())
            and not any(unicodedata.category(c).startswith('P') for c in visible))


def omit_period(text):
    if not single_sentence_period(text):
        return text
    end = len(text.rstrip())
    return text[:end-1] + text[end:]


def validated_empty_suffix(source, target):
    """Authorize only a fingerprinted, reviewed display suffix omission.

    This is not a global empty-translation exception. Callers still verify the
    actual source slot and mapped baseline bytes before writing a null string.
    """
    from font_poc import require
    p = target.get('empty_display_suffix')
    if target.get('target') != '':
        require(p is None, 'empty suffix proof on nonempty target')
        return False
    require(isinstance(p, dict) and p.get('schema') == 1
            and p.get('previous_target') == '。'
            and p.get('source_sha256') == source.get('source_sha256') == target.get('source_sha256')
            and p.get('id') == target.get('id') == source.get('id')
            and p.get('role') == 'composed-display-sentence-terminator'
            and re.fullmatch(r'[a-f0-9]{64}', p.get('consumer_sha256', ''))
            and target.get('status') == 'reviewed', 'unbound empty display suffix')
    from localization.text import protected_tokens
    from source_interpretation import source_text
    require(not protected_tokens(source_text(source)), 'protected source suffix')
    return True
