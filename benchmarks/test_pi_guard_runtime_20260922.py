"""Actual Pi/extension integration using a deterministic local mock, no model."""
import http.server
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

import compare_staging_20260922 as base


class MockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers['Content-Length']))
        self.server.calls += 1
        number = self.server.calls
        if number <= 5:
            delta = {'tool_calls': [{'index': 0, 'id': f'call_{number}', 'type': 'function',
                      'function': {'name': 'powershell', 'arguments': json.dumps({'command': "Write-Output 'GUARD_CONTROL'", 'timeout': 5})}}]}
            reason = 'tool_calls'
        else:
            delta, reason = {'content': 'Finished.'}, 'stop'
        chunks = [{'id': f'mock-{number}', 'object': 'chat.completion.chunk',
                   'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]},
                  {'choices': [{'index': 0, 'delta': {}, 'finish_reason': reason}]},
                  {'choices': [], 'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20}}]
        wire = ''.join('data: ' + json.dumps(c) + '\n\n' for c in chunks) + 'data: [DONE]\n\n'
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.end_headers()
        self.wfile.write(wire.encode())


class PiGuardIntegration(unittest.TestCase):
    def test_live_extension_blocks_then_terminates_and_observe_does_not(self):
        base.OWNED_JOBS = True
        for mode in ('guard', 'observe'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                config = root / 'config'
                config.mkdir()
                (root / 'solution.py').write_text('pass\n')
                server = http.server.HTTPServer(('127.0.0.1', 0), MockHandler)
                server.calls = 0
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                models = {'providers': {'mock': {'baseUrl': f'http://127.0.0.1:{server.server_port}/v1',
                          'api': 'openai-completions', 'apiKey': 'local-only',
                          'models': [{'id': 'control', 'contextWindow': 32768, 'maxTokens': 512}]}}}
                (config / 'models.json').write_text(json.dumps(models))
                (config / 'settings.json').write_text(json.dumps({'retry': {'enabled': False}, 'cacheWarming': 'off'}))
                env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ('API_KEY', 'AUTH_TOKEN', 'OAUTH_TOKEN'))}
                log = root / 'guard.jsonl'
                env.update(PI_CODING_AGENT_DIR=str(config), PI_OFFLINE='1', PI_TELEMETRY='0',
                           LAB_LOOP_MODE=mode, LAB_LOOP_LOG=str(log))
                command = ['node', str(base.PI), '--offline', '--no-extensions', '--no-skills',
                           '--no-context-files', '--no-prompt-templates', '--no-themes', '--no-session',
                           '--extension', str(base.HERE / 'repeat_guard_20260922.mjs'), '--provider', 'mock',
                           '--model', 'control', '--tools', 'powershell', '--mode', 'json', '-p', 'Run the control.']
                process = base.spawn_owned(command, cwd=root, env=env, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=base.NO_WINDOW)
                try:
                    stdout, stderr = process.communicate(timeout=75)
                    self.assertEqual(process.returncode, 0, stderr)
                    self.assertTrue(log.exists(), stderr + stdout[-2000:])
                    events = [json.loads(line) for line in log.read_text().splitlines()]
                    self.assertEqual(server.calls, 5 if mode == 'guard' else 6)
                    self.assertEqual(sum(bool(e.get('block')) for e in events), 2 if mode == 'guard' else 0)
                    self.assertEqual(any(e.get('terminate') for e in events), mode == 'guard')
                finally:
                    if process.poll() is None:
                        base.stop_owned(process)
                    cleanup = base.finish_owned(process)
                    self.assertEqual(cleanup['returncode'], 0)
                    self.assertEqual(cleanup['active_after'], 0)
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
