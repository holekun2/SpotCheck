import unittest
from datetime import datetime, timedelta
import numpy as np
import statistics
from test_helpers import determine_altitude_changes, determine_gimbal_angle, sphere,calculate_position,fit_curve,assign_time_groups, categorize_segment, calculate_goodness_of_fit, categorize_flights, identify_flight_segments
import pytest




class TestDataProcessing(unittest.TestCase):
    def test_calculate_position_single_point(self):
        data = [
            {'Flight Yaw Degree': 0, 'Flight X speed': 1, 'Flight Y speed': 0, 'Relative height': 10}
        ]
        expected_positions = np.array([[0, 0, 10]])
        expected_initial_coordinates = np.array([0, 0, 10])

        positions, initial_coordinates = calculate_position(data)

        np.testing.assert_allclose(positions, expected_positions)
        np.testing.assert_allclose(initial_coordinates, expected_initial_coordinates)

    def test_calculate_position_multiple_points(self):
        data = [
            {'Flight Yaw Degree': 0, 'Flight X speed': 1, 'Flight Y speed': 0, 'Relative height': 10},
            {'Flight Yaw Degree': 90, 'Flight X speed': 0, 'Flight Y speed': 2, 'Relative height': 12},
            {'Flight Yaw Degree': 180, 'Flight X speed': -1, 'Flight Y speed': 0, 'Relative height': 14},
            {'Flight Yaw Degree': 270, 'Flight X speed': 0, 'Flight Y speed': -3, 'Relative height': 16}
        ]
        expected_positions = np.array([[0, 0, 10],
                                    [0, 2, 12],
                                    [-1, 2, 14],
                                    [-1, -1, 16]])
        expected_initial_coordinates = np.array([0, 0, 10])

        positions, initial_coordinates = calculate_position(data)

        np.testing.assert_allclose(positions, expected_positions)
        np.testing.assert_allclose(initial_coordinates, expected_initial_coordinates)

    def test_calculate_position_empty_data(self):
        data = []
        expected_positions = np.array([])
        expected_initial_coordinates = None

        positions, initial_coordinates = calculate_position(data)

        np.testing.assert_array_equal(positions, expected_positions)
        self.assertIsNone(initial_coordinates)

    def test_sphere_shape(self):
        coords = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        x0, y0, z0, r = 0, 0, 0, 1
        result = sphere(coords, x0, y0, z0, r)
        assert result.shape == coords.shape[:1]

    def test_sphere_inside(self):
        coords = np.array([[0.5, 0.5, 0.5]])
        x0, y0, z0, r = 0, 0, 0, 1
        result = sphere(coords, x0, y0, z0, r)
        assert np.allclose(result, -0.1339745962155614)

    def test_sphere_outside(self):
        coords = np.array([[2, 0, 0]])
        x0, y0, z0, r = 0, 0, 0, 1
        result = sphere(coords, x0, y0, z0, r)
        assert np.allclose(result, 1)

    def test_sphere_on_surface(self):
        coords = np.array([[1, 0, 0]])
        x0, y0, z0, r = 0, 0, 0, 1
        result = sphere(coords, x0, y0, z0, r)
        assert np.allclose(result, 0)

    def test_sphere_random_coords(self):
        coords = np.random.rand(100, 3)
        x0, y0, z0, r = 0.5, 0.5, 0.5, 0.25
        result = sphere(coords, x0, y0, z0, r)
        assert result.shape == (100,)



class TestDetermineGimbalAngle(unittest.TestCase):
    def test_average_gimbal_angle(self):
        groups = {
            'group1': {
                'data': [{'Gimbal Pitch Angle': 22}, {'Gimbal Pitch Angle': 22}, {'Gimbal Pitch Angle': 22}]
            }
        }
        result = determine_gimbal_angle(groups)
        self.assertEqual(result['group1']['average_gimbal_angle'], 22)
        self.assertFalse(result['group1']['gimbal_angle_altered'])

    def test_gimbal_angle_altered(self):
        groups = {
            'group2': {
                'data': [{'Gimbal Pitch Angle': 1}, {'Gimbal Pitch Angle': 50}, {'Gimbal Pitch Angle': 100}]
            }
        }
        result = determine_gimbal_angle(groups)
        self.assertAlmostEqual(result['group2']['average_gimbal_angle'], 50.33, places=2)
        self.assertTrue(result['group2']['gimbal_angle_altered'])

class TestDetermineAltitudeChanges(unittest.TestCase):
    def test_average_altitude(self):
        groups = {
            'group1': {
                'data': [{'Relative Altitude': 100}, {'Relative Altitude': 100}, {'Relative Altitude': 100}]
            }
        }
        result = determine_altitude_changes(groups)
        self.assertEqual(result['group1']['average_altitude'], 100)
        self.assertFalse(result['group1']['altitude_altered'])

    def test_altitude_altered(self):
        groups = {
            'group2': {
                'data': [{'Relative Altitude': 50}, {'Relative Altitude': 150}, {'Relative Altitude': 250}]
            }
        }
        result = determine_altitude_changes(groups)
        self.assertAlmostEqual(result['group2']['average_altitude'], 150, places=1)
        self.assertTrue(result['group2']['altitude_altered'])




if __name__ == '__main__':
    unittest.main()