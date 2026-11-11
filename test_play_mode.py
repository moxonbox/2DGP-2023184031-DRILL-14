"""Scene integration checks without opening a window."""

import unittest
from unittest.mock import Mock, patch

import game_world
import play_mode


class PlayModeTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.addCleanup(play_mode.finish)

    def test_scene_registers_updates_and_draws_flock(self):
        bird_flock = Mock()
        with patch.object(play_mode, 'Boy'), patch.object(play_mode, 'Grass'), \
                patch.object(play_mode, 'Flock', return_value=bird_flock):
            play_mode.init()
            self.assertIn(bird_flock, game_world.world[1])
            play_mode.update()
            game_world.render()
        bird_flock.update.assert_called_once_with()
        bird_flock.draw.assert_called_once_with()
        play_mode.finish()
        self.assertIsNone(play_mode.boy)
        self.assertIsNone(play_mode.flock)
        self.assertTrue(all(not layer for layer in game_world.world))


if __name__ == '__main__':
    unittest.main()
