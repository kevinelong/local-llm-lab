"""Pure protocol tests; no model requests or child processes."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import http.client
import io
import json
import threading

import compare_staging_20260922 as runner


class ProtocolTests(unittest.TestCase):
    def test_scorer_correctness_is_not_replaced_by_lifecycle_outcome(self):
        process = MagicMock(returncode=0)
        process.communicate.return_value = ('{"passed":55,"total":55}', '')
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(runner, 'OWNED_JOBS', True), \
                patch.object(runner, 'spawn_owned', return_value=process), \
                patch.object(runner, 'finish_owned', return_value={'returncode': 0, 'active_before': 1, 'active_after': 0}):
            code, evaluation = runner.score_artifact('graph', Path(tmp)/'solution.py', Path(tmp), {})
        self.assertEqual(code, 0)
        self.assertEqual(evaluation['passed'], 55)
        self.assertEqual(evaluation['owned_tree']['active_before'], 1)

    def test_timeout_is_failure_even_if_all_phases_exited_cleanly(self):
        phases = [{'clean_finish': True}]
        self.assertTrue(runner.clean_run(phases, 1, False, False, None))
        self.assertFalse(runner.clean_run(phases, 1, True, False, None))
        self.assertFalse(runner.clean_run(phases, 1, False, True, None))

    def test_expected_cancel_unknown_usage_does_not_abort_fresh_trials(self):
        self.assertTrue(runner.infrastructure_failure({'quota_failure': 'quota_unknown'}))
        self.assertFalse(runner.infrastructure_failure({'quota_failure': 'quota_unknown', 'timed_out': True}))
        self.assertTrue(runner.infrastructure_failure({'timed_out': True, 'cleanup_error': 'still loaded'}))
        self.assertTrue(runner.infrastructure_failure({'quota_failure': 'backend_quota_overrun', 'timed_out': True}))

    def test_evaluator_timeout_is_zero_score_with_owned_cleanup(self):
        process = MagicMock()
        process.communicate.side_effect = [runner.subprocess.TimeoutExpired('evaluator', 30), ('', '')]
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(runner.subprocess, 'Popen', return_value=process), patch.object(runner, 'stop_owned', return_value={'reaped': True}) as cleanup:
                code, evaluation = runner.score_artifact('graph', Path(temporary) / 'solution.py', Path(temporary), {})
            self.assertEqual(code, 1)
            self.assertEqual(evaluation['passed'], 0)
            self.assertEqual(evaluation['total'], 55)
            self.assertTrue(evaluation['evaluation_timeout'])
            cleanup.assert_called_once_with(process)

    def test_import_time_exit_is_program_failure_not_pipeline_failure(self):
        process = MagicMock(returncode=2)
        process.communicate.return_value = ('', 'argparse: bad arguments')
        with tempfile.TemporaryDirectory() as temporary, patch.object(runner.subprocess, 'Popen', return_value=process):
            code, evaluation = runner.score_artifact('graph', Path(temporary) / 'solution.py', Path(temporary), {})
        self.assertEqual(code, 1)
        self.assertEqual(evaluation['passed'], 0)
        self.assertEqual(evaluation['abnormal_evaluator_exit'], 2)

    def test_failed_tree_cleanup_stops_experiment_even_after_parent_exit(self):
        for cleanup in ({'returncode': 1, 'stderr': 'Access denied'},
                        {'tree_kill_timed_out': True}):
            self.assertTrue(runner.infrastructure_failure({
                'timed_out': True, 'phases': [{'exit_code': 0, 'cleanup': cleanup}]}))
            self.assertTrue(runner.infrastructure_failure({
                'evaluation': {'evaluation_timeout': True, 'cleanup': cleanup}}))
        self.assertFalse(runner.infrastructure_failure({
            'timed_out': True, 'phases': [{'cleanup': {'returncode': 0}}]}))

    def test_pairs_are_adjacent_and_order_reproducible(self):
        tasks = ['alpha', 'beta', 'gamma', 'delta', 'epsilon']
        actual = runner.schedule(tasks)
        self.assertEqual(actual, runner.schedule(list(reversed(tasks))))
        self.assertEqual(len(actual), 30)
        self.assertEqual(len({r['label'] for r in actual}), 30)
        for i in range(0, 30, 2):
            a, b = actual[i:i + 2]
            self.assertEqual((a['task'], a['repeat']), (b['task'], b['repeat']))
            self.assertEqual({a['treatment'], b['treatment']}, {'one-shot', 'staged'})

    def test_quota_reduces_request_and_stops_when_exhausted(self):
        quota = runner.Budget(quota=100, cap=80)
        self.assertEqual(quota.allowance(), 80)
        quota.account({'completion_tokens': 70}, 80)
        self.assertEqual(quota.allowance(), 30)
        quota.account({'completion_tokens': 30}, 30)
        with self.assertRaisesRegex(RuntimeError, 'quota_exhausted'):
            quota.allowance()

    def test_unknown_or_invalid_usage_fails_closed(self):
        for usage in (None, {}, {'completion_tokens': -1}, {'completion_tokens': True}):
            quota = runner.Budget()
            quota.account(usage, quota.allowance())
            with self.assertRaisesRegex(RuntimeError, 'quota_unknown'):
                quota.allowance()

    def test_backend_overrun_is_recorded_not_hidden(self):
        quota = runner.Budget(quota=100, cap=80)
        quota.account({'completion_tokens': 81}, quota.allowance())
        self.assertEqual(quota.used, 81)
        with self.assertRaisesRegex(RuntimeError, 'backend_quota_overrun'):
            quota.allowance()

    def test_prepare_isolated_and_refuses_overwrite(self):
        tasks = {name: {'spec': 'Requirements', 'code': 'pass\n', 'public': 'pass\n'}
                 for name in ('a', 'b', 'c', 'd', 'e')}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder, entries = runner.prepare('pure-test', tasks, root)
            for entry in entries:
                workspace = folder / 'runs' / entry['label'] / 'workspace'
                self.assertEqual({p.name for p in workspace.iterdir()},
                                 {'README.md', 'solution.py', 'test_public.py'})
            with self.assertRaises(FileExistsError):
                runner.prepare('pure-test', tasks, root)
            with self.assertRaises(ValueError):
                runner.prepare('../escape', tasks, root)

    def test_actual_http_relay_accounts_stream_usage_and_caps_next_request(self):
        self.relay_case([7, 3], [8, 3], 'quota_exhausted')

    def test_actual_http_relay_stops_after_missing_stream_usage(self):
        self.relay_case([None], [8], 'quota_unknown')

    def relay_case(self, usages, expected_caps, failure):
        bodies = []
        def upstream(request, timeout):
            bodies.append(json.loads(request.data))
            used = usages[len(bodies) - 1]
            events = [{'choices': [{'delta': {'content': 'OK'}, 'finish_reason': 'stop'}]}]
            if used is not None:
                events.append({'choices': [], 'usage': {'completion_tokens': used}})
            return io.BytesIO((''.join('data: ' + json.dumps(e) + '\n\n' for e in events)
                               + 'data: [DONE]\n\n').encode())
        with tempfile.TemporaryDirectory() as temporary:
            server = runner.http.server.HTTPServer(('127.0.0.1', 0), runner.Relay)
            server.folder = Path(temporary)
            server.stop = server.folder / 'STOP'
            server.deadline = float('inf')
            server.budget = runner.Budget(quota=10, cap=8)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with patch.object(runner.urllib.request, 'urlopen', side_effect=upstream):
                    for index in range(len(usages) + 1):
                        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                        connection.request('POST', '/v1/chat/completions', json.dumps({'max_tokens': 999}))
                        response = connection.getresponse()
                        response.read()
                        self.assertEqual(response.status, 200 if index < len(usages) else 503)
                        connection.close()
                self.assertEqual([body['max_tokens'] for body in bodies], expected_caps)
                self.assertEqual(server.budget.failure, failure)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
