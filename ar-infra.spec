# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ar-infra CLI.
Build with: pyinstaller ar-infra.spec

Security notes:
- Excludes test/development dependencies
- No code signing (users verify checksums)
- UPX compression disabled by default (some antiviruses flag compressed binaries)
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

base_path = Path(SPECPATH)

datas = []
binaries = []
hiddenimports = []

tmp_ret = collect_all('jinja2')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('rich')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('questionary')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

hiddenimports += collect_submodules('click')
hiddenimports += collect_submodules('typer')

hiddenimports += [
    'pydantic',
    'pydantic_settings',
    'yaml',
    'requests',
    'httpx',
    'pathspec',
    'toml',
    'git',
]

project_datas = []

ar_infra_dir = base_path / 'src' / 'ar_infra'
if ar_infra_dir.exists():
    # Include templates directory
    template_dir = ar_infra_dir / 'templates'
    if template_dir.exists():
        for item in template_dir.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(base_path / 'src')
                project_datas.append((str(item), str(rel_path.parent)))

    # Include cli/resources directory (banner.txt, etc.)
    resources_dir = ar_infra_dir / 'cli' / 'resources'
    if resources_dir.exists():
        print(f"[OK] Found resources directory: {resources_dir}")
        for item in resources_dir.rglob('*'):
            if item.is_file():
                print(f"  Adding: {item.name} -> ar_infra/cli/resources/")
                project_datas.append((str(item), 'ar_infra/cli/resources'))
    else:
        print(f"[WARN] Resources directory not found: {resources_dir}")
        print(f"  Checking if ar_infra_dir exists: {ar_infra_dir.exists()}")
        if ar_infra_dir.exists():
            print(f"  Contents of cli/: {list((ar_infra_dir / 'cli').iterdir()) if (ar_infra_dir / 'cli').exists() else 'cli/ not found'}")

    # Include any other data files (*.txt, *.json, *.yaml, *.yml, *.toml, etc.)
    for pattern in ['*.txt', '*.json', '*.yaml', '*.yml', '*.toml', '*.md', '*.j2', '*.jinja2']:
        for item in ar_infra_dir.rglob(pattern):
            if item.is_file():
                rel_path = item.relative_to(base_path / 'src')
                project_datas.append((str(item), str(rel_path.parent)))

# Include .env file
env_file = base_path / '.env'
if env_file.exists():
    project_datas.append((str(env_file), '.'))

a = Analysis(
    ['src/ar_infra/cli/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas + project_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_cov',
        'pytest_mock',
        'pytest_asyncio',
        'pytest_xdist',
        'pytest_timeout',
        'pytest_benchmark',
        'unittest',
        'test',
        'tests',
        '_pytest',
        'IPython',
        'ipdb',
        'black',
        'ruff',
        'mypy',
        'bandit',
        'coverage',
        'sphinx',
        'tkinter',
        'turtle',
        'pydoc',
        'doctest',
        'xmlrpc',
        'pdb',
        'bdb',
        'profile',
        'cProfile',
        'pstats',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ar-infra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
