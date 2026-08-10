from pathlib import Path
import re

from tools.offline_smoke_test import run_smoke_test


ROOT = Path(__file__).resolve().parents[1]


def test_patient_dicom_ignore_rules_are_case_insensitive():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/[Dd][Ii][Cc][Oo][Mm]/" in ignore
    assert "/[Dd][Ii][Cc][Oo][Mm]_[Ll][Oo][Gg][Ss]/" in ignore
    assert "*.[Dd][Cc][Mm]" in ignore
    assert "*.[Dd][Ii][Rr]" in ignore


def test_offline_lock_is_complete_and_exact():
    lock_path = ROOT / "requirements" / "offline-win64-py312.txt"
    requirements = [
        line.strip()
        for line in lock_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+==[^\s]+", item) for item in requirements)
    names = {item.split("==", 1)[0].lower() for item in requirements}
    assert names == {
        "contourpy",
        "customtkinter",
        "cycler",
        "darkdetect",
        "fonttools",
        "kiwisolver",
        "matplotlib",
        "numpy",
        "packaging",
        "pandas",
        "pillow",
        "pydicom",
        "pyparsing",
        "python-dateutil",
        "pytz",
        "six",
        "tzdata",
    }


def test_offline_installer_forbids_package_index_access():
    installer = (ROOT / "offline" / "install_offline.bat").read_text(
        encoding="utf-8"
    )
    lower = installer.lower()
    assert "pip_no_index=1" in lower
    assert "pip_config_file=nul" in lower
    assert "--no-index" in lower
    assert "--find-links" in lower
    assert "--only-binary=:all:" in lower
    assert 'call :select_python' in lower
    assert "import struct,sys,tkinter; raise systemexit" in lower
    assert '"%base_python%" -m venv' in lower
    assert "http://" not in lower
    assert "https://" not in lower
    assert "invoke-webrequest" not in lower
    assert "curl" not in lower
    assert "%systemroot%\\system32\\windowspowershell\\v1.0\\powershell.exe" in lower
    assert "hashset[string]" in lower
    assert "unexpected bundle file" in lower
    assert "bundle inventory count mismatch" in lower
    assert "'.venv','.runtime','sha256sums.txt'" in lower
    assert "^|" not in installer


def test_launchers_use_only_dedicated_virtual_environment():
    launcher = (ROOT / "offline" / "start_rt_dicom_toolkit.bat").read_text(
        encoding="utf-8"
    )
    smoke_launcher = (ROOT / "offline" / "smoke_test.bat").read_text(
        encoding="utf-8"
    )
    assert ".venv\\Scripts\\pythonw.exe" in launcher
    assert ".venv\\Scripts\\python.exe" in smoke_launcher
    assert " -m rt_dicom_toolkit" in launcher


def test_bundle_builder_checks_official_python_signature_and_uses_wheels_only():
    builder = (ROOT / "tools" / "prepare_offline_bundle.ps1").read_text(
        encoding="utf-8"
    )
    assert "https://www.python.org/ftp/python/" in builder
    assert "Get-AuthenticodeSignature" in builder
    assert "Python Software Foundation" in builder
    assert "import pip,setuptools,struct,sys,wheel" in builder
    assert "with pip, setuptools, and wheel is required" in builder
    assert '"--only-binary=:all:"' in builder
    assert '"--no-deps"' in builder
    assert "SHA256SUMS.txt" in builder
    assert '"DICOM"' not in builder
    assert '"DICOM_LOGS"' not in builder


def test_synthetic_dicom_smoke_workflow():
    run_smoke_test()
