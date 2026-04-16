import unittest
import time
import json
import io
from unittest.mock import MagicMock, patch
from sensors.mock_adapter import MockAdapter
from sensors.termux_adapter import TermuxAdapter

class TestMockAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = MockAdapter(freq_hz=1.0)

    def test_mock_start_sets_start_time(self):
        self.assertIsNone(self.adapter._start_time)
        self.adapter.start()
        self.assertIsInstance(self.adapter._start_time, float)

    def test_mock_read_returns_all_keys(self):
        self.adapter.start()
        data = self.adapter.read()
        keys = {"ax", "ay", "az", "mx", "my", "mz"}
        self.assertTrue(keys.issubset(data.keys()))

    def test_mock_read_returns_floats(self):
        self.adapter.start()
        data = self.adapter.read()
        for val in data.values():
            self.assertIsInstance(val, float)

    def test_mock_sinusoid_changes_over_time(self):
        self.adapter.start()
        res1 = self.adapter.read()
        time.sleep(0.1)
        res2 = self.adapter.read()
        self.assertNotEqual(res1["mx"], res2["mx"])

class TestTermuxAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = TermuxAdapter("accelerometer,magnetic")

    @patch('subprocess.Popen')
    def test_termux_read_combined_json(self, mock_popen):
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = (
            '{"LSM6DSM Accelerometer": {"values": [1.0, 2.0, 3.0]}, '
            '"MMC5603NJ Magnetometer": {"values": [4.0, 5.0, 6.0]}}\n'
        )
        mock_popen.return_value = mock_process
        
        self.adapter.start()
        res = self.adapter.read()
        
        self.assertEqual(res["ax"], 1.0)
        self.assertEqual(res["ay"], 2.0)
        self.assertEqual(res["az"], 3.0)
        self.assertEqual(res["mx"], 4.0)
        self.assertEqual(res["my"], 5.0)
        self.assertEqual(res["mz"], 6.0)

    @patch('subprocess.Popen')
    def test_termux_read_handles_malformed_json(self, mock_popen):
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = 'error: sensor not found\n'
        mock_popen.return_value = mock_process
        
        self.adapter.start()
        res = self.adapter.read()
        
        self.assertIsNone(res)

    @patch('subprocess.Popen')
    def test_termux_stop_terminates_process(self, mock_popen):
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        self.adapter.start()
        self.adapter.stop()
        
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

if __name__ == '__main__':
    unittest.main()
