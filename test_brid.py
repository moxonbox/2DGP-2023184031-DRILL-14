"""Headless checks for bird animation and flock flight."""

import unittest
from unittest.mock import Mock, patch

import brid
from brid import Bird


class BirdTests(unittest.TestCase):
    def setUp(self):
        Bird.image = None
        self.image = Mock(h=506)
        loader = patch.object(brid, 'load_image', return_value=self.image)
        self.loader = loader.start()
        self.addCleanup(loader.stop)
        self.addCleanup(setattr, Bird, 'image', None)

    def test_birds_share_one_sprite_texture(self):
        birds = [Bird(10.0, 10.0, i) for i in range(10)]
        self.loader.assert_called_once_with('bird_animation.png')
        self.assertTrue(all(bird.image is self.image for bird in birds))

    def test_sprite_uses_all_14_cells_and_skips_empty_cell(self):
        bird = Bird(10.0, 10.0)
        for frame in range(brid.FRAME_COUNT):
            bird.frame = frame
            bird.face_dir = -1
            bird.draw()
            args = self.image.clip_composite_draw.call_args.args
            self.assertEqual(args[:4], (
                (frame % 5) * 183, 506 - (frame // 5 + 1) * 168, 183, 168))
            self.assertEqual(args[5], 'h')
            self.assertGreaterEqual(args[1], 0)
            self.assertLessEqual(args[0] + args[2], 918)
        bird.face_dir = 1
        bird.draw()
        self.assertEqual(self.image.clip_composite_draw.call_args.args[5], '')

    def test_animation_depends_on_elapsed_time_with_individual_phases(self):
        bird, other = Bird(10.0, 10.0), Bird(10.0, 10.0, 1)
        self.assertNotEqual(bird.frame, other.frame)
        bird.animate(0.125)
        self.assertAlmostEqual(bird.frame, 7.0)
        bird.animate(0.125)
        self.assertAlmostEqual(bird.frame, 0.0)
        before = bird.frame
        bird.animate(0.0)
        self.assertEqual(bird.frame, before)


if __name__ == '__main__':
    unittest.main()
