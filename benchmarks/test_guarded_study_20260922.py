import tempfile
from pathlib import Path
import unittest
import guarded_study_20260922 as study


class ScheduleTests(unittest.TestCase):
    def test_all_schedules_prepare_real_task_fixtures(self):
        original = study.base.schedule
        with tempfile.TemporaryDirectory() as tmp:
            for suite, expected in [('smoke', 2), ('ablation', 12), ('staging', 30)]:
                entries = study.entries_for(suite)
                self.assertEqual(len(entries), expected)
                self.assertEqual(len({e['label'] for e in entries}), expected)
                self.assertTrue(all(e['task'] in study.TASKS for e in entries))
                try:
                    study.base.schedule = lambda _: entries
                    _, actual = study.base.prepare(suite, study.TASKS, root=Path(tmp))
                finally:
                    study.base.schedule = original
                self.assertEqual(actual, entries)
                for i in range(0, len(entries), 2):
                    a, b = entries[i:i+2]
                    self.assertEqual((a['task'], a['repeat']), (b['task'], b['repeat']))
                    if suite == 'ablation':
                        self.assertEqual({a['loop_mode'], b['loop_mode']}, {'guard', 'observe'})


if __name__ == '__main__':
    unittest.main()
