"""Optional coverage rasterization experiments; no resource-format assumptions."""
from functools import lru_cache
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def validate_options(options):
    ss = options.get('supersample', 1)
    gamma = options.get('gamma', 1.0)
    thresholds = options.get('thresholds', [43, 128, 213])
    bold = options.get('embolden_px', 0.0)
    strength = options.get('embolden_strength', 1.0)
    if ss not in (1, 4) or not math.isfinite(gamma) or not 0.25 <= gamma <= 4:
        raise ValueError('invalid supersampling/gamma')
    if len(thresholds) != 3 or any(type(t) is not int for t in thresholds) or not 0 < thresholds[0] < thresholds[1] < thresholds[2] <= 255:
        raise ValueError('three increasing 8-bit thresholds required')
    if not math.isfinite(bold) or not 0 <= bold <= 1 or not 0 <= strength <= 1:
        raise ValueError('invalid emboldening')
    if abs(bold * ss - round(bold * ss)) > 1e-8:
        raise ValueError('emboldening radius must match high-resolution pixel grid')
    return ss, gamma, thresholds, round(bold * ss), strength


def quantization_lut(options):
    _, gamma, thresholds, _, _ = validate_options(options)
    return [sum(round(255 * (v / 255) ** (1 / gamma)) >= t for t in thresholds) for v in range(256)]


def topology(image):
    """8-connected foreground / 4-connected enclosed background, levels >= 2."""
    w, h = image.size
    pixels = list(image.get_flattened_data() if hasattr(image, 'get_flattened_data') else image.getdata())
    def count(foreground, neighbours):
        seen = set(); total = 0
        for at in range(w * h):
            if at in seen or (pixels[at] >= 2) != foreground:
                continue
            stack = [at]; seen.add(at); edge = False
            while stack:
                p = stack.pop(); x, y = p % w, p // w
                edge |= x == 0 or y == 0 or x == w - 1 or y == h - 1
                for dx, dy in neighbours:
                    xx, yy = x + dx, y + dy; q = yy * w + xx
                    if 0 <= xx < w and 0 <= yy < h and q not in seen and (pixels[q] >= 2) == foreground:
                        seen.add(q); stack.append(q)
            total += foreground or not edge
        return total
    return count(True, [(x, y) for x in (-1, 0, 1) for y in (-1, 0, 1) if x or y]), count(False, [(1, 0), (-1, 0), (0, 1), (0, -1)])


@lru_cache(maxsize=32)
def face(path, size):
    return ImageFont.truetype(path, size)


def render_ink(character, font_path, size, options, width, height):
    ss, _, _, radius, strength = validate_options(options)
    hi = Image.new('L', (96 * ss, 96 * ss))
    ImageDraw.Draw(hi).text((32 * ss, 24 * ss), character, font=face(str(font_path), size * ss), fill=255)
    original = hi.resize((96, 96), Image.Resampling.LANCZOS) if ss != 1 else hi
    candidate = original; reason = None
    if radius and strength:
        grown = Image.blend(hi, hi.filter(ImageFilter.MaxFilter(2 * radius + 1)), strength)
        candidate = grown.resize((96, 96), Image.Resampling.LANCZOS) if ss != 1 else grown
        lut = quantization_lut(options)
        box = candidate.point(lut).getbbox()
        if box and (box[2] - box[0] > width or box[3] - box[1] > height):
            reason = 'bold_exceeds_cell'
        elif box:
            region = (box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1)
            before = topology(original.point(lut).crop(region)); after = topology(candidate.point(lut).crop(region))
            if after[0] < before[0] or after[1] < before[1]:
                reason = 'bold_merges_components_or_closes_holes'
        if reason:
            candidate = original  # Explicit per-glyph guard recorded in build proof.
    return candidate, candidate.point(quantization_lut(options)).getbbox(), reason
