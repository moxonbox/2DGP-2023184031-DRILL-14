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


if __name__ == '__main__':
    unittest.main()
