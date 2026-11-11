"""Headless regression checks for frame timing and mode shutdown."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import game_framework


class GameFrameworkTests(unittest.TestCase):
    def setUp(self):
        game_framework.frame_time = 0.0
        self.mode = SimpleNamespace(**{
            name: Mock() for name in
            ('init', 'handle_events', 'update', 'render', 'finish')
        })
        clock = patch.object(game_framework.time, 'perf_counter',
                             side_effect=[10.0, 10.0, 10.02, 10.07])
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        sleep = patch.object(game_framework.time, 'sleep')
        sleep.start()
        self.addCleanup(sleep.stop)

    def assert_finished(self):
        self.mode.finish.assert_called_once_with()
        self.assertFalse(game_framework.running)
        self.assertEqual(game_framework.stack, [])

    def test_frame_time_reaches_update_and_allows_zero_elapsed(self):
        elapsed = []
        self.mode.update.side_effect = lambda: elapsed.append(game_framework.frame_time)
        self.mode.handle_events.side_effect = lambda: (
            game_framework.quit() if len(elapsed) == 2 else None
        )

        game_framework.run(self.mode)

        self.assertEqual(elapsed[0], 0.0)
        self.assertAlmostEqual(elapsed[1], 0.02)
        self.assertEqual(len(elapsed), 2)
        self.assertEqual(self.mode.render.call_count, 2)
        self.assert_finished()

    def test_last_mode_can_pop_during_events_or_update(self):
        for phase in ('handle_events', 'update'):
            with self.subTest(phase=phase):
                self.mode.handle_events.reset_mock(side_effect=True)
                self.mode.update.reset_mock(side_effect=True)
                self.mode.finish.reset_mock()
                self.clock.side_effect = [10.0, 10.02]
                getattr(self.mode, phase).side_effect = game_framework.pop_mode

                game_framework.run(self.mode)

                self.mode.render.assert_not_called()
                if phase == 'handle_events':
                    self.mode.update.assert_not_called()
                self.assert_finished()

    def test_update_error_still_finishes_mode(self):
        self.mode.update.side_effect = RuntimeError('update failed')

        with self.assertRaisesRegex(RuntimeError, 'update failed'):
            game_framework.run(self.mode)

        self.assert_finished()

    def test_run_resets_frame_time_before_init(self):
        game_framework.frame_time = 99.0
        self.mode.init.side_effect = lambda: self.assertEqual(game_framework.frame_time, 0.0)
        self.mode.handle_events.side_effect = game_framework.quit

        game_framework.run(self.mode)

        self.mode.update.assert_not_called()
        self.assert_finished()


if __name__ == '__main__':
    unittest.main()
