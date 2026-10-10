"""Resource screening must reject independent memory and concurrency failures."""
import struct
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
from pathlib import Path
from a3b_preflight_20260924 import eligibility, inspect, ollama_state
from a3b_serial_20260924 import danger, Monitor


class PreflightTests(unittest.TestCase):
    def test_offline_ollama_requires_process_absence(self):
        with patch('urllib.request.urlopen',side_effect=urllib.error.URLError('offline')):
            self.assertEqual(ollama_state([{'name':'explorer.exe'}])['status'],'offline_process_absence_verified')
            with self.assertRaises(RuntimeError):ollama_state([{'name':'ollama.exe'}])

    def test_abort_boundaries_independent(self):
        good={'physical_available_gib':3,'commit_headroom_gib':2,'gpu_free_gib':0.5}
        self.assertEqual(danger(good),[])
        for key in good:
            self.assertEqual(danger({**good,key:good[key]-0.01}),[key])

    def test_abort_only_terminates_owned_process(self):
        from unittest.mock import Mock
        monitor=Monitor.__new__(Monitor)
        monitor.process=Mock();monitor.process.poll.return_value=None
        monitor.abort('low RAM')
        monitor.process.terminate.assert_called_once_with()
        self.assertEqual(monitor.error,'low RAM')
    def test_each_resource_can_independently_hold(self):
        row = {'fits_estimated_'+k: True for k in ('ram', 'commit', 'vram')}
        self.assertEqual(eligibility(row, {}, []), [])
        for resource in ('ram', 'commit', 'vram'):
            with self.subTest(resource=resource):
                failed = dict(row, **{'fits_estimated_'+resource: False})
                self.assertEqual(eligibility(failed, {}, []), ['insufficient_'+resource])

    def test_concurrent_work_holds_even_with_enough_memory(self):
        row = {'fits_estimated_'+k: True for k in ('ram', 'commit', 'vram')}
        self.assertEqual(eligibility(row, {'models': [{}]}, ['RUNNING.lock']),
                         ['ollama_model_resident', 'existing_run_lock'])

    def test_invalid_headers_rejected_without_tensor_load(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'test.gguf'
            for data in (b'GGUF', b'nope', b'GGUF'+struct.pack('<IQQ', 3, 0, 0)):
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    inspect(path)


if __name__ == '__main__':
    unittest.main()
