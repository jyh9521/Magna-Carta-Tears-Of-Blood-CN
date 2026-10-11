"""Explicit field-local source language and codec; primary catalog defaults unchanged."""
import hashlib


def source_text(entry, default_locale='ko-KR'):
    refs = entry.get('references', {})
    locale = entry.get('source_locale', default_locale)
    if 'source_locale' in entry and locale not in refs:
        raise ValueError('explicit source locale reference missing')
    return refs.get(locale, refs.get('und', ''))


def source_codec(entry):
    codec = entry.get('source_encoding', 'cp949')
    if codec == 'cp949':
        return codec
    proof = entry.get('source_interpretation', {})
    if (codec not in ('cp932', 'utf-8') or proof.get('original_decode') != 'failed'
            or proof.get('raw_sha256') != entry.get('source_sha256')
            or proof.get('native_source_span_verified') is not True
            or proof.get('runtime_encoding_verified') is not False
            or proof.get('reading_sha256') != hashlib.sha256(source_text(entry).encode('utf8')).hexdigest()):
        raise ValueError('alternate source codec requires bound interpretation')
    return codec


def decode_source(raw, entry):
    if hashlib.sha256(raw).hexdigest() != entry['source_sha256']:
        raise ValueError('source interpretation raw fingerprint mismatch')
    codec = source_codec(entry)
    text = raw.decode(codec, errors='strict')
    if text != source_text(entry) or (codec != 'cp949' and text.encode(codec) != raw):
        raise ValueError('source interpretation text/roundtrip mismatch')
    return text


def control_policy(entry, target=None):
    policy = entry.get('source_control_policy')
    if policy is None:
        return None
    from localization.text import LITERAL_POLICY, TERMINAL_LF_POLICY, SINGLE_TAB_POLICY, TERMINAL_NUL_POLICY
    proof = entry.get('source_control_interpretation', {})
    if (policy not in (LITERAL_POLICY, TERMINAL_LF_POLICY, SINGLE_TAB_POLICY, TERMINAL_NUL_POLICY) or proof.get('schema') != 1
            or proof.get('original_controls') != 'quarantined'
            or proof.get('raw_sha256') != entry.get('source_sha256')
            or proof.get('native_source_span_verified') is not True
            or proof.get('runtime_control_semantics_verified') is not False
            or proof.get('reading_sha256') != hashlib.sha256(source_text(entry).encode('utf8')).hexdigest()
            or not isinstance(proof.get('native_binding_sha256'), str)
            or len(proof.get('native_binding_sha256', '')) != 64
            or (target is not None and proof.get('target_sha256') != hashlib.sha256(target.encode('utf8')).hexdigest())):
        raise ValueError('literal source control policy requires bound interpretation')
    return policy


def encode_target(encoder, entry, target):
    policy = control_policy(entry, target)
    return encoder.encode(target, control_policy=policy) if policy else encoder.encode(target)
