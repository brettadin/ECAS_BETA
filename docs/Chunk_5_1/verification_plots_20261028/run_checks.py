"""Reproducible offline checks with the existing isolated project environment."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from importlib.metadata import version

root = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
stage = sys.argv[1]
if stage not in ('focused', 'full'):
    raise SystemExit('Expected focused or full')
scratch = root / '.venv/checks'
env = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR') if key in os.environ}
env.update(TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'),
           HOME=str(scratch / 'profile'), USERPROFILE=str(scratch / 'profile'),
           APPDATA=str(scratch / 'profile'), LOCALAPPDATA=str(scratch / 'profile'),
           QT_QPA_PLATFORM='offscreen', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
           PATH=str(root / '.venv/Scripts') + os.pathsep + str(Path(env['SystemRoot']) / 'System32'))
command = [sys.executable, '-I', '-B', '-m', 'pytest', '-p', 'no:cacheprovider',
           '-o', 'pythonpath=.', '--basetemp=' + str(scratch / ('pytest-plots-' + stage))]
if stage == 'focused':
    command += ['tests/test_workspace_pages.py', 'tests/test_comparison_browser.py', 'tests/test_main_window.py',
                'tests/test_molecular_browser.py', 'tests/test_exomol_product.py', 'tests/test_projects_ui.py']
command += ['-q']
started = time.monotonic()
result = subprocess.run(command, cwd=root, env=env, capture_output=True,
                        text=True, errors='replace', timeout=120)
output = result.stdout + result.stderr
(evidence / (stage + '.log')).write_text(output, encoding='utf-8')
(evidence / (stage + '-run.json')).write_text(json.dumps(dict(
    command=command, environment_keys=sorted(env), exit_code=result.returncode,
    elapsed_seconds=time.monotonic() - started, python=sys.version,
    versions={name: version(name) for name in ('pytest', 'PySide6', 'pyqtgraph', 'numpy')}
), indent=2), encoding='utf-8')
print(output)
raise SystemExit(result.returncode)
