import unittest
import math
import tempfile
import os
import json
from core.orientation import compute_orientation, RawSensorFrame, OrientationState
from core.filters import EMAFilter, CircularEMAFilter
from core.calibration import CalibrationManager
from core.quality import evaluate_confidence

class TestOrientationEngine(unittest.TestCase):
    def test_heading_north(self):
        # az=9.81 (flat), mx=30 (magnetic north)
        frame = RawSensorFrame(ax=0, ay=0, az=9.81, mx=30, my=0, mz=0)
        state = compute_orientation(frame)
        self.assertAlmostEqual(state.heading_deg, 0.0, delta=5.0)

    def test_heading_east(self):
        # my=-30 (magnetic east in Android coordinates)
        frame = RawSensorFrame(ax=0, ay=0, az=9.81, mx=0, my=-30, mz=0)
        state = compute_orientation(frame)
        self.assertAlmostEqual(state.heading_deg, 90.0, delta=5.0)

    def test_heading_south(self):
        frame = RawSensorFrame(ax=0, ay=0, az=9.81, mx=-30, my=0, mz=0)
        state = compute_orientation(frame)
        self.assertAlmostEqual(state.heading_deg, 180.0, delta=5.0)

    def test_heading_west(self):
        frame = RawSensorFrame(ax=0, ay=0, az=9.81, mx=0, my=30, mz=0)
        state = compute_orientation(frame)
        self.assertAlmostEqual(state.heading_deg, 270.0, delta=5.0)

    def test_gimbal_lock_detection(self):
        # ax=9.5, az=1.0 -> very high pitch/tilt
        frame = RawSensorFrame(ax=9.5, ay=0, az=1.0, mx=30, my=0, mz=0)
        state = compute_orientation(frame)
        self.assertTrue(state.is_gimbal_lock)
        self.assertGreater(state.tilt_deg, 75.0)

    def test_zero_accel_returns_poor(self):
        frame = RawSensorFrame(ax=0, ay=0, az=0, mx=30, my=0, mz=0)
        state = compute_orientation(frame)
        self.assertEqual(state.confidence_state, "POOR")

class TestEMAFilter(unittest.TestCase):
    def test_first_call_no_smoothing(self):
        f = EMAFilter(alpha=0.2)
        self.assertEqual(f.update(100.0), 100.0)

    def test_smoothing_converges(self):
        f = EMAFilter(alpha=0.2)
        f.update(0.0)
        for _ in range(50):
            val = f.update(100.0)
        self.assertGreater(val, 99.0)

    def test_circular_wraparound(self):
        f = CircularEMAFilter(alpha=0.5)
        f.update(359.0)
        # 359 -> 1 via 0 (shortest path)
        val = f.update(1.0)
        # (359 + 0.5 * (2)) % 360 = 0.0 or something near 0/1
        # delta = (1 - 359 + 180) % 360 - 180 = (-358 + 180) % 360 - 180 = -178 % 360 - 180 = 182 - 180 = 2
        # value = (359 + 0.5 * 2) % 360 = 360 % 360 = 0.0
        self.assertTrue(358 < val or val < 2)
        self.assertAlmostEqual(val, 0.0, delta=0.1)

class TestCalibrationManager(unittest.TestCase):
    def test_compute_raises_on_insufficient_samples(self):
        with tempfile.NamedTemporaryFile() as tmp:
            cm = CalibrationManager(tmp.name)
            for _ in range(19):
                cm.add_sample(1.0, 2.0, 3.0)
            with self.assertRaises(ValueError):
                cm.compute()

    def test_compute_bias_correct(self):
        with tempfile.NamedTemporaryFile() as tmp:
            cm = CalibrationManager(tmp.name)
            # mx from -10 to 10, center 0
            # my from -5 to 5, center 0
            # mz from -2 to 2, center 0
            for i in range(21):
                val = (i - 10)
                cm.add_sample(val, val*0.5, val*0.2)
            bias = cm.compute()
            self.assertAlmostEqual(bias["bias_x"], 0.0, delta=0.1)
            self.assertAlmostEqual(bias["bias_y"], 0.0, delta=0.1)
            self.assertAlmostEqual(bias["bias_z"], 0.0, delta=0.1)

    def test_save_load_roundtrip(self):
        fd, path = tempfile.mkstemp()
        try:
            cm = CalibrationManager(path)
            for i in range(25):
                cm.add_sample(float(i), 0.0, 0.0)
            cm.save()
            
            cm2 = CalibrationManager(path)
            data = cm2.load()
            self.assertIsNotNone(data)
            self.assertEqual(cm2._bias["bias_x"], 12.0) # (24+0)/2
        finally:
            os.close(fd)
            if os.path.exists(path):
                os.remove(path)

class TestQualityEvaluator(unittest.TestCase):
    def test_good_signal(self):
        frame = RawSensorFrame(ax=0, ay=0, az=9.81, mx=40, my=0, mz=0)
        self.assertEqual(evaluate_confidence(frame, 10.0), "GOOD")

    def test_poor_magnetic_interference(self):
        frame = RawSensorFrame(ax=0, ay=0, az=9.81, mx=200, my=200, mz=200)
        self.assertEqual(evaluate_confidence(frame, 10.0), "POOR")

    def test_poor_gimbal_lock(self):
        frame = RawSensorFrame(ax=0, ay=0, az=9.81, mx=40, my=0, mz=0)
        self.assertEqual(evaluate_confidence(frame, 80.0), "POOR")

if __name__ == '__main__':
    unittest.main()
