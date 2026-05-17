"""
ScRecorder build script.

Usage:
    python build.py                         build with current version
    python build.py 1.2.3                   set explicit version, then build
    python build.py --bump patch            1.0.0 -> 1.0.1, then build
    python build.py --bump minor            1.0.1 -> 1.1.0, then build
    python build.py --bump major            1.1.0 -> 2.0.0, then build
    python build.py --bump patch --no-build bump only, skip PyInstaller
"""

import sys
import os
import re
import subprocess
import argparse
import textwrap

ROOT             = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE     = os.path.join(ROOT, "version.py")
SPEC_FILE        = os.path.join(ROOT, "ScRecorder.spec")
VERSION_INFO_FILE = os.path.join(ROOT, "version_info.txt")
DIST_DIR         = os.path.join(ROOT, "dist")
ASSETS_DIR       = os.path.join(ROOT, "assets")
ICON_PATH        = os.path.join(ASSETS_DIR, "icons", "app.ico")
FFMPEG_PATH      = os.path.join(ASSETS_DIR, "ffmpeg.exe")


# ── version helpers ──────────────────────────────────────────────────────────

def read_version() -> str:
    """Read __version__ from version.py without importing it."""
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^__version__\s*=\s*["\']([^"\']+)["\']', line)
            if m:
                return m.group(1)
    raise RuntimeError("Could not find __version__ in version.py")


def write_version(version: str) -> None:
    """Rewrite version.py with a new version string, keeping all derived constants in sync."""
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    major, minor, patch = version.split(".")

    content = re.sub(
        r'^__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{version}"',
        content, flags=re.MULTILINE,
    )
    content = re.sub(r'^VERSION_MAJOR\s*=\s*\d+', f'VERSION_MAJOR = {major}', content, flags=re.MULTILINE)
    content = re.sub(r'^VERSION_MINOR\s*=\s*\d+', f'VERSION_MINOR = {minor}', content, flags=re.MULTILINE)
    content = re.sub(r'^VERSION_PATCH\s*=\s*\d+', f'VERSION_PATCH = {patch}', content, flags=re.MULTILINE)
    content = re.sub(
        r'^VERSION_TUPLE\s*=\s*\([^)]+\)',
        f'VERSION_TUPLE = ({major}, {minor}, {patch})',
        content, flags=re.MULTILINE,
    )

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def bump_version(current: str, part: str) -> str:
    major, minor, patch = [int(x) for x in current.split(".")]
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown part: {part!r}")


def validate_version(version: str) -> None:
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        raise ValueError(f"Invalid version format: {version!r} — expected major.minor.patch")


# ── Windows PE version metadata ───────────────────────────────────────────────

def make_version_info(version: str) -> str:
    """Return a PyInstaller-compatible VSVersionInfo block for embedding in the exe."""
    major, minor, patch = [int(x) for x in version.split(".")]
    build = 0
    return textwrap.dedent(f"""\
        # UTF-8
        VSVersionInfo(
          ffi=FixedFileInfo(
            filevers=({major}, {minor}, {patch}, {build}),
            prodvers=({major}, {minor}, {patch}, {build}),
            mask=0x3f,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0)
          ),
          kids=[
            StringFileInfo([
              StringTable(u'040904B0', [
                StringStruct(u'CompanyName',      u'ScRecorder'),
                StringStruct(u'FileDescription',  u'ScRecorder Screen Recorder'),
                StringStruct(u'FileVersion',      u'{version}.{build}'),
                StringStruct(u'InternalName',     u'ScRecorder'),
                StringStruct(u'LegalCopyright',   u'Copyright (C) 2025 ScRecorder'),
                StringStruct(u'OriginalFilename', u'ScRecorder-{version}.exe'),
                StringStruct(u'ProductName',      u'ScRecorder'),
                StringStruct(u'ProductVersion',   u'{version}.{build}'),
              ])
            ]),
            VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
          ]
        )
    """)


# ── PyInstaller .spec ─────────────────────────────────────────────────────────

def make_spec(version: str) -> str:
    """Return a generated PyInstaller .spec file string."""
    icon_line = (
        f"    icon=r'{ICON_PATH}',"
        if os.path.isfile(ICON_PATH)
        else "    # icon omitted — place app.ico at assets/icons/app.ico to enable"
    )
    ffmpeg_line = (
        f"        (r'{FFMPEG_PATH}', 'assets'),"
        if os.path.isfile(FFMPEG_PATH)
        else "        # ffmpeg.exe not found at assets/ffmpeg.exe"
    )
    return textwrap.dedent(f"""\
        # -*- mode: python ; coding: utf-8 -*-
        # Auto-generated by build.py — do not edit manually.
        block_cipher = None

        a = Analysis(
            [r'{os.path.join(ROOT, "main.py")}'],
            pathex=[r'{ROOT}'],
            binaries=[
        {ffmpeg_line}
            ],
            datas=[
                (r'{os.path.join(ASSETS_DIR, "icons")}', 'assets/icons'),
            ],
            hiddenimports=[],
            hookspath=[],
            runtime_hooks=[],
            excludes=[],
            cipher=block_cipher,
        )

        pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

        exe = EXE(
            pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            [],
            name='ScRecorder-{version}',
            debug=False,
            strip=False,
            upx=False,
            console=False,
            version=r'{VERSION_INFO_FILE}',
        {icon_line}
        )
    """)


# ── build ─────────────────────────────────────────────────────────────────────

def run_build(version: str) -> None:
    print(f"[build] Version  : {version}")

    with open(VERSION_INFO_FILE, "w", encoding="utf-8") as f:
        f.write(make_version_info(version))
    print(f"[build] Written  : version_info.txt")

    with open(SPEC_FILE, "w", encoding="utf-8") as f:
        f.write(make_spec(version))
    print(f"[build] Written  : ScRecorder.spec")

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", SPEC_FILE]
    print(f"[build] Running  : {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=ROOT)

    # Clean up generated intermediates regardless of outcome
    for tmp in [VERSION_INFO_FILE, SPEC_FILE]:
        try:
            os.remove(tmp)
        except OSError:
            pass

    if result.returncode != 0:
        print("\n[build] ERROR: PyInstaller failed.")
        sys.exit(result.returncode)

    expected = os.path.join(DIST_DIR, f"ScRecorder-{version}.exe")
    if os.path.isfile(expected):
        size_mb = os.path.getsize(expected) / (1024 * 1024)
        print(f"\n[build] Output   : {expected}  ({size_mb:.1f} MB)")
    else:
        print(f"\n[build] WARNING  : Expected output not found: {expected}")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ScRecorder build script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("version_arg", nargs="?", metavar="VERSION",
                        help="Explicit version to build, e.g. 1.2.3")
    parser.add_argument("--bump", choices=["major", "minor", "patch"],
                        help="Bump this version component before building")
    parser.add_argument("--no-build", action="store_true",
                        help="Update version.py but skip the PyInstaller step")
    args = parser.parse_args()

    if args.version_arg and args.bump:
        parser.error("Cannot use both an explicit version and --bump at the same time.")

    current = read_version()

    if args.version_arg:
        target = args.version_arg
        validate_version(target)
        if target != current:
            write_version(target)
            print(f"[build] Version  : {current} -> {target}")
        else:
            print(f"[build] Version  : {current} (unchanged)")
    elif args.bump:
        target = bump_version(current, args.bump)
        write_version(target)
        print(f"[build] Bumped {args.bump:5s}: {current} -> {target}")
    else:
        target = current
        print(f"[build] Version  : {target} (current)")

    if args.no_build:
        print("[build] --no-build set - skipping PyInstaller.")
        return

    run_build(target)


if __name__ == "__main__":
    main()
