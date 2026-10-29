"""Launch a normal-platform desktop check with isolated projects/reference caches.

Only existing public captures are seeded; there are no network requests here.
The GUI remains open for computer-use inspection. This is not a production launcher.
"""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SCRATCH = ROOT / '.venv/checks/desktop-feedback'

if '--window' not in sys.argv:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    env = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR') if key in os.environ}
    for name in ('profile', 'tmp'):
        (SCRATCH / name).mkdir(exist_ok=True)
    env.update(TEMP=str(SCRATCH / 'tmp'), TMP=str(SCRATCH / 'tmp'),
               HOME=str(SCRATCH / 'profile'), USERPROFILE=str(SCRATCH / 'profile'),
               APPDATA=str(SCRATCH / 'profile'), LOCALAPPDATA=str(SCRATCH / 'profile'),
               PATH=str(ROOT / '.venv/Scripts') + os.pathsep + str(Path(env['SystemRoot']) / 'System32'))
    with (SCRATCH / 'application.log').open('ab') as log:
        process = subprocess.Popen([sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--window'],
                                   cwd=ROOT, env=env, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    print(f'Isolated desktop process started: {process.pid}')
else:
    sys.path.insert(0, str(ROOT))
    from PySide6.QtWidgets import QApplication
    from ecas.ui.main_window import ECASWindow
    from ecas.ingestion.exomol_product import ProductRequest, validate_product
    from ecas.ingestion.exomol_product_network import RetrievedCrossSection
    from ecas.ingestion.exomol_reference_cache import cached_references, store_reference

    references = SCRATCH / 'reference-cache/references'
    if not cached_references(references)[0]:
        data = ROOT / 'data/ExoMol/2026-10-28'
        captures = (
            ('12C-16O2', data / 'CO2-12C-16O2-500K-4000-4010-dnu1.sigma'),
            ('1H2-16O', data / 'additional-products/H2O-500K-4000-4010-dnu1.sigma'),
            ('12C-1H4', data / 'additional-products/CH4-500K-4000-4010-dnu1.sigma'),
        )
        for isotope, path in captures:
            raw = path.read_bytes()
            request = ProductRequest(4000, 4010, 500, '1', isotope)
            store_reference(references, RetrievedCrossSection(request, raw, validate_product(raw, request)))
    app = QApplication([])
    window = ECASWindow(projects_dir=SCRATCH / 'projects', reference_cache_dir=SCRATCH / 'reference-cache')
    window.show()
    sys.exit(app.exec())
