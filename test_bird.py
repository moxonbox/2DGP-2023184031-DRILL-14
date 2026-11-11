"""Headless checks for bird animation and flock flight."""

import unittest
from unittest.mock import Mock, patch

import boy
from boy import Bird


class BirdTests(unittest.TestCase):
    def setUp(self):
        Bird.image = None
        self.image = Mock(h=506)
        loader = patch.object(boy, 'load_image', return_value=self.image)
        self.loader = loader.start()
        self.addCleanup(loader.stop)
        self.addCleanup(setattr, Bird, 'image', None)
        for name, value in (('get_canvas_width', 1600), ('get_canvas_height', 600)):
            canvas = patch.object(boy, name, return_value=value)
            canvas.start()
            self.addCleanup(canvas.stop)

    def test_birds_share_one_sprite_texture(self):
        birds = [Bird(10.0, 10.0, i) for i in range(10)]
        self.loader.assert_called_once_with('bird_animation.png')
        self.assertTrue(all(bird.image is self.image for bird in birds))

    def test_sprite_uses_all_14_cells_and_skips_empty_cell(self):
        bird = Bird(10.0, 10.0)
        for frame in range(boy.FRAME_COUNT):
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

    def test_sprite_pitch_follows_climb_for_both_directions(self):
        bird = Bird(10.0, 10.0)
        bird.vy = 2.0
        bird.draw()
        self.assertGreater(self.image.clip_composite_draw.call_args.args[4], 0.0)
        bird.vx, bird.face_dir = -boy.CRUISE_SPEED, -1
        bird.draw()
        self.assertLess(self.image.clip_composite_draw.call_args.args[4], 0.0)
        bird.vx, bird.vy = 0.0, 100.0
        bird.draw()
        self.assertLessEqual(abs(self.image.clip_composite_draw.call_args.args[4]), 0.35)

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

    def test_velocity_integrates_acceleration_in_seconds(self):
        bird = Bird(10.0, 10.0)
        with patch.object(bird, 'acceleration', return_value=(0.0, -boy.GRAVITY)):
            bird.step(0.1)
        self.assertAlmostEqual(bird.x, 10.6)
        self.assertAlmostEqual(bird.vy, -boy.GRAVITY * 0.1)
        self.assertLess(bird.y, 10.0)
        bird.vx = -2.0
        bird.step(0.0)
        self.assertEqual(bird.face_dir, -1)

    def test_cruise_balances_weight_lift_thrust_and_drag(self):
        bird = Bird(10.0, 10.0)
        ax, ay = bird.acceleration((0.0, 0.0))
        self.assertAlmostEqual(ax, 0.0)
        self.assertAlmostEqual(ay, 0.0)
        with patch.object(boy, 'MAX_LIFT_COEFFICIENT', 0.0):
            self.assertAlmostEqual(bird.acceleration((0.0, 0.0))[1], -boy.GRAVITY)

    def test_drag_opposes_motion_and_grows_with_speed_squared(self):
        bird = Bird(10.0, 10.0)
        with patch.object(boy, 'MAX_THRUST', 0.0):
            slow = bird.acceleration((0.0, 0.0))[0]
            bird.vx *= 2
            fast = bird.acceleration((0.0, 0.0))[0]
            self.assertAlmostEqual(fast, 4 * slow)
            bird.vx *= -1
            self.assertGreater(bird.acceleration((0.0, 0.0))[0], 0.0)

    def test_wingbeat_phase_changes_lift(self):
        bird = Bird(10.0, 10.0)
        bird.phase = 0.25
        up = bird.acceleration((0.0, 0.0))[1]
        bird.phase = 0.75
        down = bird.acceleration((0.0, 0.0))[1]
        self.assertGreater(up, 0.0)
        self.assertLess(down, 0.0)

    def test_steering_brakes_before_turning_and_restores_altitude(self):
        bird = Bird(10.0, 10.0)
        steering = bird.steering(-1, 11.0)
        self.assertLess(steering[0], 0.0)
        self.assertGreater(steering[1], 0.0)
        bird.step(1.0 / 120.0, steering)
        self.assertGreater(bird.vx, 0.0)
        self.assertLess(bird.vx, boy.CRUISE_SPEED)
        self.assertLessEqual(boy.hypot(*bird.steering(-1, 1000.0)), boy.MAX_STEERING)

    def test_flock_spawns_and_draws_exactly_ten_birds(self):
        flock = boy.Flock()
        self.assertEqual(len(flock.birds), 10)
        self.assertEqual(len({(bird.x, bird.y) for bird in flock.birds}), 10)
        flock.step(1.0 / 120.0)
        flock.draw()
        self.assertEqual(self.image.clip_composite_draw.call_count, 10)

    def test_nearby_and_coincident_birds_separate(self):
        left, right = Bird(10.0, 10.0, 0), Bird(11.0, 10.0, 1)
        self.assertLess(left.flocking([left, right])[0], 0.0)
        self.assertGreater(right.flocking([left, right])[0], 0.0)
        right.x = left.x
        self.assertLess(left.flocking([left, right])[0], 0.0)
        self.assertGreater(right.flocking([left, right])[0], 0.0)

    def test_bird_aligns_velocity_only_with_local_neighbors(self):
        bird, neighbor = Bird(10.0, 10.0), Bird(13.0, 10.0, 1)
        neighbor.vx, neighbor.vy = 8.0, 2.0
        ax, ay = bird.flocking([bird, neighbor])
        self.assertGreater(ax, 0.0)
        self.assertGreater(ay, 0.0)
        neighbor.x = 30.0
        self.assertEqual(bird.flocking([bird, neighbor]), (0.0, 0.0))

    def test_equal_velocity_birds_cohere_towards_local_center(self):
        bird, neighbor = Bird(10.0, 10.0), Bird(14.0, 11.0, 1)
        ax, ay = bird.flocking([bird, neighbor])
        self.assertGreater(ax, 0.0)
        self.assertGreater(ay, 0.0)
        self.assertEqual(bird.flocking([bird]), (0.0, 0.0))

    def test_edges_reverse_target_without_instantly_reversing_velocity(self):
        flock = boy.Flock()
        leader = max(flock.birds, key=lambda bird: bird.x)
        leader.x = flock.width - boy.TURN_MARGIN
        flock.step(1.0 / 120.0)
        self.assertEqual(flock.direction, -1)
        self.assertGreater(leader.vx, 0.0)
        self.assertLess(leader.vx, boy.CRUISE_SPEED)
        flock.birds[0].x = boy.TURN_MARGIN
        flock.step(1.0 / 120.0)
        self.assertEqual(flock.direction, 1)

    def test_fixed_steps_ignore_negative_time_and_bound_long_stalls(self):
        flock = boy.Flock()
        with patch.object(flock, 'step') as step:
            with patch.object(boy.game_framework, 'frame_time', -1.0):
                flock.update()
            step.assert_not_called()
            with patch.object(boy.game_framework, 'frame_time', 5.0):
                flock.update()
            self.assertEqual(step.call_count, 30)
            self.assertLess(flock.accumulator, boy.PHYSICS_DT)

    def test_flight_bounds_stop_outward_motion(self):
        flock = boy.Flock()
        bird = flock.birds[0]
        bird.x, bird.y = -10.0, -10.0
        bird.vx, bird.vy = -20.0, -20.0
        flock.step(boy.PHYSICS_DT)
        self.assertEqual((bird.x, bird.y), (boy.SCREEN_MARGIN, boy.MIN_ALTITUDE))
        self.assertGreaterEqual(bird.vx, 0.0)
        self.assertGreaterEqual(bird.vy, 0.0)


if __name__ == '__main__':
    unittest.main()
