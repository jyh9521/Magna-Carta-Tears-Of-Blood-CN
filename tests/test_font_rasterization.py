import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from PIL import Image, ImageFont
from unittest.mock import patch
from font_rasterization import quantization_lut, validate_options, topology, render_ink


class RasterTests(unittest.TestCase):
    def test_default_quantizer_legacy_exact(self):
        self.assertEqual(quantization_lut({}), [(v * 3 + 127) // 255 for v in range(256)])
    def test_threshold_edges(self):
        lut = quantization_lut({'thresholds': [40, 120, 200]})
        self.assertEqual([lut[v] for v in (39, 40, 119, 120, 199, 200)], [0, 1, 1, 2, 2, 3])
    def test_gamma_direction(self):
        self.assertGreater(sum(quantization_lut({'gamma': 1.2})), sum(quantization_lut({})))
    def test_bad_options(self):
        for opt in ({'supersample': 3}, {'gamma': 0}, {'gamma': float('nan')}, {'thresholds': [40,40,200]}, {'embolden_px': .25}, {'embolden_px': 2}):
            with self.assertRaises(ValueError): validate_options(opt)
    def test_fractional_high_resolution_bold(self):
        self.assertEqual(validate_options({'supersample': 4, 'embolden_px': .25})[3], 1)
    def test_components(self):
        im=Image.new('L',(5,5));im.putpixel((1,1),3);im.putpixel((3,3),3)
        self.assertEqual(topology(im),(2,0))
    def test_hole(self):
        im=Image.new('L',(5,5))
        for x,y in ((1,1),(2,1),(3,1),(1,2),(3,2),(1,3),(2,3),(3,3)):im.putpixel((x,y),3)
        self.assertEqual(topology(im),(1,1))
    def test_bold_boundary_guard(self):
        with patch('font_rasterization.face',return_value=ImageFont.load_default(size=40)):
            im,box,reason=render_ink('A','unused',10,{'supersample':4,'embolden_px':.25},1,1)
        self.assertIsNotNone(box);self.assertEqual(reason,'bold_exceeds_cell')
    def test_ss4_image_target_size(self):
        with patch('font_rasterization.face',return_value=ImageFont.load_default(size=40)):
            im,box,reason=render_ink('A','unused',10,{'supersample':4},19,21)
        self.assertEqual(im.size,(96,96));self.assertIsNotNone(box);self.assertIsNone(reason)

if __name__ == '__main__': unittest.main()
