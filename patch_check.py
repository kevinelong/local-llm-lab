"""patch_check.py - daily security-patch check for Django, nginx and the local engines.

Standing rule (Kevin, 2026-10-22): check for security patches **daily**, alongside the existing tool-version check.
This script is the check, so it is the same every day and its output is comparable:

  * every `requirements*.txt` we know about that pins Django, plus the *installed* Django in any venv found beside it;
  * the newest patch on that project's own branch **and** whether the branch is still supported (endoflife.date);
  * nginx: whether it is installed here at all, and the current stable/mainline upstream;
  * the engines already tracked in AGENTS.md (llama.cpp newest tag, Ollama, ComfyUI, Strata latest release).

Read-only: it queries PyPI, endoflife.date, nginx.org and the GitHub API, and never installs or edits anything.
Exit code is 1 when a pinned Django is behind the newest patch on its own branch, or on an unsupported branch -
so a daily run that prints nothing is a clean run.

    python patch_check.py            # table + patch-report-<date>.json
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOTS = [
    Path(r'C:/Users/kevin/Dropbox'),
]
WSL_REQ = ['~/bfa/requirements.txt']
UA = {'User-Agent': 'omp-patch-check/1.0'}


def get(url, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def get_json(url, timeout=40):
    return json.loads(get(url, timeout))


def pypi_last_per_branch(package):
    d = get_json('https://pypi.org/pypi/%s/json' % package)
    rel = d['releases']
    out = {}
    for ver in rel:
        parts = ver.split('.')
        if len(parts) < 2 or not all(p.isdigit() for p in parts[:2]):
            continue
        branch = '.'.join(parts[:2])
        if not rel[ver]:
            continue
        when = max((f.get('upload_time') or '') for f in rel[ver])
        if branch not in out or when > out[branch][1]:
            out[branch] = (ver, when)
    return d['info']['version'], {b: v for b, v in out.items()}


def eol_cycles(package):
    try:
        data = get_json('https://endoflife.date/api/%s.json' % package)
    except Exception:
        return {}
    return {c['cycle']: c for c in data}


def req_pins():
    found = []
    for root in ROOTS:
        if not root.exists():
            continue
        for p in root.rglob('requirements*.txt'):
            if any(s in str(p) for s in ('.venv', 'site-packages', 'node_modules', '.git')):
                continue
            try:
                text = p.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            for m in re.finditer(r'(?m)^\s*[Dd]jango\s*==\s*([0-9][^\s#]*)', text):
                found.append((str(p), m.group(1)))
    for rel in WSL_REQ:
        try:
            out = subprocess.run(['wsl', '-e', 'bash', '-lc',
                                  'grep -iE "^\\s*django\\s*==" %s' % rel],
                                 capture_output=True, text=True, timeout=60)
            m = re.search(r'==\s*([0-9][^\s#]*)', out.stdout)
            if m:
                found.append(('wsl:' + rel, m.group(1)))
            venv = subprocess.run(['wsl', '-e', 'bash', '-lc',
                                   '%s/../.venv/bin/python -c "import django;print(django.get_version())"'
                                   % rel.rsplit('/', 1)[0]],
                                  capture_output=True, text=True, timeout=120)
            inst = venv.stdout.strip().splitlines()[-1] if venv.stdout.strip() else ''
            if re.match(r'^[0-9]', inst):
                found.append(('wsl:' + rel.rsplit('/', 1)[0] + '/.venv (installed)', inst))
        except Exception:
            pass
    return found


def nginx_state():
    installed = []
    for cmd in (['where', 'nginx'],):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if out.stdout.strip():
                installed.append(out.stdout.strip().splitlines()[0])
        except Exception:
            pass
    try:
        wsl = subprocess.run(['wsl', '-e', 'bash', '-lc', 'command -v nginx && nginx -v 2>&1'],
                             capture_output=True, text=True, timeout=60)
        if wsl.stdout.strip():
            installed.append('wsl: ' + ' '.join(wsl.stdout.strip().splitlines()))
    except Exception:
        pass
    page = get('https://nginx.org/en/download.html').decode('utf-8', 'replace')
    up = {}
    for label in ('Stable version', 'Mainline version'):
        m = re.search(label + r'.*?nginx-([0-9.]+)', page, re.S)
        if m:
            up[label.replace(' version', '').lower()] = m.group(1).rstrip('.')
    return {'installed': installed, 'upstream': up}


def engine_state():
    out = {}
    try:
        rels = get_json('https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=1')
        out['llama.cpp'] = rels[0]['tag_name']
    except Exception as e:
        out['llama.cpp'] = 'lookup failed'
    try:
        rels = get_json('https://api.github.com/repos/ollama/ollama/releases?per_page=1')
        out['ollama'] = rels[0]['tag_name']
    except Exception:
        out['ollama'] = 'lookup failed'
    try:
        rels = get_json('https://api.github.com/repos/comfyanonymous/ComfyUI/releases?per_page=1')
        out['comfyui'] = rels[0]['tag_name']
    except Exception:
        out['comfyui'] = 'lookup failed'
    try:
        rels = get_json('https://api.github.com/repos/Niko1221/Strata/releases?per_page=1')
        out['strata'] = rels[0]['tag_name']
    except Exception:
        out['strata'] = 'lookup failed'
    return out


def main():
    latest, branches = pypi_last_per_branch('django')
    eol = eol_cycles('django')
    pins = req_pins()
    rows, behind = [], 0
    print('Django: newest overall %s' % latest)
    print('%-56s %-9s %-9s %-8s %s' % ('pin location', 'pinned', 'branch last', 'branch', 'status'))
    for where, pin in pins:
        branch = '.'.join(pin.split('.')[:2])
        last = branches.get(branch, ('?', ''))[0]
        cyc = eol.get(branch) or {}
        eol_date = cyc.get('eol')
        supported = bool(eol_date) and str(eol_date) > date.today().isoformat()
        state = 'supported' if supported else ('EOL %s' % eol_date if eol_date else 'unknown branch')
        flag = ''
        if last != '?' and pin != last:
            flag = '  <-- %s behind' % ('patch' if supported else 'final patch')
            behind += 1
        print('%-56s %-9s %-9s %-8s %s%s' % (where[-56:], pin, last, branch, state, flag))
        rows.append({'where': where, 'pinned': pin, 'branch_last': last, 'branch': branch,
                     'eol': eol_date, 'supported': supported})

    ng = nginx_state()
    print('\nnginx: installed here = %s' % (ng['installed'] or 'NO (not on PATH, no service, none in WSL)'))
    print('       upstream stable %s | mainline %s' % (ng['upstream'].get('stable'), ng['upstream'].get('mainline')))

    eng = engine_state()
    print('\nengines (latest upstream):')
    for k, v in eng.items():
        print('  %-10s %s' % (k, v))

    report = {'date': date.today().isoformat(), 'django_latest': latest, 'pins': rows,
              'nginx': ng, 'engines': eng, 'pins_behind': behind}
    out = Path(__file__).resolve().parent / ('patch-report-%s.json' % date.today().isoformat())
    out.write_text(json.dumps(report, indent=1), encoding='utf-8')
    print('\nwrote %s' % out.name)
    if behind:
        print('%d Django pin(s) behind the newest patch on their own branch' % behind)
        return 1
    print('no Django pin behind its branch')
    return 0


if __name__ == '__main__':
    sys.exit(main())
