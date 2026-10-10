"""Pure tests for the dormant Bonsai packing comparison runner."""
import io
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import compare_bonsai_packing_20260922 as packing


class FakeProcess:
    def __init__(self):
        self.pid = 123
        self.returncode = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def kill(self):
        self.killed = True
        self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode


class PackingTests(unittest.TestCase):
    def test_required_tool_control_uses_pinned_server_string_format(self):
        plain = {'choices': [{'message': {'content': 'LOCAL_OK'}}]}
        tool = {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
            {'function': {'name': 'emit_result', 'arguments': '{"value":7}'}}]}}]}
        stream = {'calls': {0: {'name': 'emit_result', 'arguments': '{"value":7}'}}}
        with mock.patch.object(packing, 'request_json', side_effect=[(plain, 1), (tool, 1)]) as request, \
                mock.patch.object(packing, 'request_sse', return_value=(stream, 1)) as sse:
            packing.control_requests(1234)
        self.assertEqual(request.call_args_list[1].args[2]['tool_choice'], 'required')
        self.assertFalse(request.call_args_list[1].args[2]['parallel_tool_calls'])
        self.assertEqual(sse.call_args.args[1]['tool_choice'], 'required')

    def test_pinned_download_allows_content_addressed_cdn_redirect(self):
        body = b'pinned-test-model'
        response = io.BytesIO(body)
        response.headers = {'Content-Length': str(len(body))}
        response.geturl = lambda: 'https://cdn.example/content-addressed-object'
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(packing.urllib.request, 'urlopen', return_value=response), \
                mock.patch.object(packing, 'PTQ1_BYTES', len(body)), \
                mock.patch.object(packing, 'PTQ1_SHA256', hashlib.sha256(body).hexdigest()):
            destination = Path(directory) / 'model.gguf'
            packing.download_ptq1(packing.PTQ1_URL, destination)
            self.assertEqual(destination.read_bytes(), body)

    def test_tool_stream_fragments_and_usage_only_event(self):
        lines = [
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"name":"emit_result","arguments":"{\\"value\\":"}}]}}]}',
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"7}"}}]},"finish_reason":"tool_calls"}]}',
            'data: {"choices":[],"usage":{"completion_tokens":7}}',
            'data: [DONE]',
        ]
        result = packing.reconstruct_sse(lines)
        self.assertEqual(result['calls'][0], {'name': 'emit_result', 'arguments': '{"value":7}'})

    def test_stream_reconstruction(self):
        lines = [
            'data: {"choices":[{"delta":{"content":"hel"}}]}\n',
            'data: {"choices":[{"delta":{"content":"lo"}}]}\n',
            'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n',
            'data: {"choices":[],"usage":{"completion_tokens":2}}\n',
            'data: [DONE]\n',
        ]
        result = packing.reconstruct_sse(lines)
        self.assertEqual(result['text'], 'hello')
        self.assertTrue(result['done'])
        with self.assertRaisesRegex(ValueError, 'without'):
            packing.reconstruct_sse(lines[:-1])

    def test_download_url_requires_host_revision_and_ptq1(self):
        valid = (f'https://huggingface.co/example/repo/resolve/{packing.HF_REVISION}/'
                 'Bonsai-PTQ1.gguf')
        packing.validate_download_url(valid)
        for invalid in [valid.replace('https:', 'http:'),
                        valid.replace(packing.HF_REVISION, 'main'),
                        valid.replace('PTQ1', 'PQ2')]:
            with self.assertRaises(ValueError):
                packing.validate_download_url(invalid)

    def test_owned_server_cleans_up_on_body_failure(self):
        fake = FakeProcess()
        response = mock.Mock(status=200)
        response.read.return_value = b'OK'
        connection = mock.Mock()
        connection.getresponse.return_value = response
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(packing.subprocess, 'Popen', return_value=fake), \
                mock.patch.object(packing.http.client, 'HTTPConnection', return_value=connection):
            command = ['server', '--port', '12345']
            with self.assertRaisesRegex(RuntimeError, 'body failed'):
                with packing.owned_server(command, Path(directory) / 'server.log'):
                    raise RuntimeError('body failed')
        self.assertTrue(fake.terminated)
        self.assertFalse(fake.killed)

    def test_fixed_request_disables_sampling_and_thinking(self):
        request = packing.fixed_request()
        self.assertEqual(request['temperature'], 0)
        self.assertEqual(request['seed'], packing.SEED)
        self.assertFalse(request['chat_template_kwargs']['enable_thinking'])
        self.assertFalse(request['stream'])


if __name__ == '__main__':
    unittest.main()
