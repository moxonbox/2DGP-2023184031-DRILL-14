"""Scene integration checks without opening a window."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import boy
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

    def test_real_scene_can_reenter_and_preserves_movement_and_space_input(self):
        boy.Bird.image = None
        self.addCleanup(setattr, boy.Bird, 'image', None)
        with patch.multiple(boy, load_image=Mock(return_value=Mock(h=506)),
                            load_font=Mock(), get_time=Mock(return_value=0.0),
                            get_canvas_width=Mock(return_value=1600),
                            get_canvas_height=Mock(return_value=600)), \
                patch.object(play_mode, 'Grass'), \
                patch.object(boy.game_framework, 'frame_time', 1.0 / 60.0):
            for _ in range(2):
                play_mode.init()
                self.assertEqual(len(play_mode.flock.birds), 10)
                self.assertEqual(len(game_world.world[1]), 2)
                events = [SimpleNamespace(type=boy.SDL_KEYDOWN, key=boy.SDLK_RIGHT),
                          SimpleNamespace(type=boy.SDL_KEYDOWN, key=boy.SDLK_SPACE)]
                with patch.object(play_mode, 'get_events', return_value=events), \
                        patch('ball.load_image'), \
                        patch('ball.get_canvas_width', return_value=1600):
                    play_mode.handle_events()
                    play_mode.update()
                self.assertGreater(play_mode.boy.x, 400.0)
                self.assertEqual(len(game_world.world[1]), 3)
                play_mode.pause()
                self.assertEqual(play_mode.boy.state, 'IDLE')
                self.assertEqual(play_mode.boy.pressed_keys, set())
                play_mode.finish()
                self.assertTrue(all(not layer for layer in game_world.world))

    def test_escape_and_window_close_quit(self):
        for event in (SimpleNamespace(type=play_mode.SDL_QUIT),
                      SimpleNamespace(type=play_mode.SDL_KEYDOWN, key=play_mode.SDLK_ESCAPE)):
            with patch.object(play_mode, 'get_events', return_value=[event]), \
                    patch.object(play_mode.game_framework, 'quit') as quit_game:
                play_mode.handle_events()
                quit_game.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
