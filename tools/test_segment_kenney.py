import unittest
from PIL import Image, ImageDraw
from segment_kenney import split_limb


class KenneySegmenterTests(unittest.TestCase):
    def test_vertical_limb_splits_into_nonempty_halves_with_shared_seam(self):
        image = Image.new("RGBA", (40, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((12, 4, 27, 95), radius=7, fill=(220, 170, 120, 255))
        upper, lower, meta = split_limb(image, overlap=3)
        self.assertIsNotNone(upper.getchannel("A").getbbox())
        self.assertIsNotNone(lower.getchannel("A").getbbox())
        self.assertEqual(meta["method"], "alpha-mask-pca-midpoint-provisional")
        self.assertGreaterEqual(meta["pivotY"], 0.35)
        self.assertLessEqual(meta["pivotY"], 0.65)

    def test_horizontal_limb_uses_horizontal_principal_axis(self):
        image = Image.new("RGBA", (100, 40), (0, 0, 0, 0))
        ImageDraw.Draw(image).rounded_rectangle((4, 12, 95, 27), radius=7, fill=(220, 170, 120, 255))
        _, _, meta = split_limb(image)
        self.assertGreater(abs(meta["axis"][0]), abs(meta["axis"][1]))

    def test_rejects_empty_image(self):
        with self.assertRaises(ValueError):
            split_limb(Image.new("RGBA", (20, 20), (0, 0, 0, 0)))

    def test_rejects_negative_overlap(self):
        image = Image.new("RGBA", (30, 80), (220, 170, 120, 255))
        with self.assertRaises(ValueError):
            split_limb(image, overlap=-1)


if __name__ == "__main__":
    unittest.main()
