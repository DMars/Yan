"""GitHub mailbox -> local UE inbox -> GitHub reports. Requires gh auth login."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Plugins/YanMaterialBridge/Content/Python'))
from yan_ir import validate

def api(endpoint, payload=None):
    cmd = ['gh', 'api', endpoint]
    if payload is not None: cmd += ['--method', 'PUT', '--input', '-']
    result = subprocess.run(cmd, input=json.dumps(payload) if payload else None,
                            capture_output=True, text=True, check=True, timeout=30)
    return json.loads(result.stdout)

def sync(repo, branch, project):
    from urllib.parse import quote
    root = project / 'Saved/YanBridge'
    inbox, reports = root / 'inbox', root / 'reports'
    inbox.mkdir(parents=True, exist_ok=True); reports.mkdir(parents=True, exist_ok=True)
    entries = api(f'repos/{repo}/contents/tasks?ref={quote(branch, safe="")}')
    for entry in entries:
        if entry['type'] != 'file' or not entry['name'].endswith('.json'): continue
        name = entry['name']
        target = inbox / name
        if target.exists() or (reports / name).exists(): continue
        blob = api(f'repos/{repo}/git/blobs/{entry["sha"]}')
        content = base64.b64decode(blob['content'])
        if len(content) > 256000: raise ValueError('Task exceeds 256 KB')
        task = json.loads(content)
        validate(task)
        if name != task['id'] + '.json': raise ValueError('Task filename/id mismatch')
        tmp = target.with_suffix('.tmp')
        tmp.write_bytes(content); os.replace(tmp, target)
        print('Queued', name, flush=True)
    for report in reports.glob('*.json'):
        marker = report.with_suffix('.uploaded')
        if marker.exists(): continue
        # Reports are immutable: conflicting existing reports require manual inspection.
        api(f'repos/{repo}/contents/reports/{report.name}', {
            'message': 'Report UE material task ' + report.stem, 'branch': branch,
            'content': base64.b64encode(report.read_bytes()).decode('ascii')})
        marker.write_text('uploaded', encoding='utf-8')
        print('Uploaded', report.name, flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', default='DMars/Yan')
    parser.add_argument('--branch', default='master')
    parser.add_argument('--project', type=Path, default=ROOT)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    while True:
        try: sync(args.repo, args.branch, args.project.resolve())
        except (subprocess.SubprocessError, ValueError, KeyError, OSError) as error:
            print('Bridge error:', error, file=sys.stderr, flush=True)
            if args.once: raise SystemExit(1)
        if args.once: break
        time.sleep(15)
if __name__ == '__main__': main()
