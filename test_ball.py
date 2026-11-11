"""Regression checks for the existing space-key projectile path."""

import unittest
from unittest.mock import patch

import ball
import game_framework
import game_world


class BallTests(unittest.TestCase):
    def setUp(self):
        ball.Ball.images.clear()
        game_world.clear()
        self.addCleanup(ball.Ball.images.clear)
        self.addCleanup(game_world.clear)

    def test_projectile_moves_and_is_removed_on_ground_contact(self):
        with patch.object(ball, 'load_image'), \
                patch.object(ball, 'get_canvas_width', return_value=1600), \
                patch.object(game_framework, 'frame_time', 0.1):
            projectile = ball.Ball(400, 90, 1)
            game_world.add_oject(projectile)
            projectile.update()
            self.assertAlmostEqual(projectile.x, 430.0)
            self.assertGreater(projectile.y, 90.0)
            self.assertAlmostEqual(projectile.velocity_y, 300 - ball.GRAVITY * 0.1)
            projectile.y, projectile.velocity_y = 40.0, -20.0
            projectile.update()
            self.assertNotIn(projectile, game_world.world[1])


if __name__ == '__main__':
    unittest.main()
