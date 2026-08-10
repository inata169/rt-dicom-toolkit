from pathlib import Path
import importlib
import re

from tools.offline_smoke_test import run_smoke_test


ROOT = Path(__file__).resolve().parents[1]


def test_patient_dicom_ignore_rules_are_case_insensitive():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "[Dd][Ii][Cc][Oo][Mm]/" in ignore
    assert "[Dd][Ii][Cc][Oo][Mm]_[Ll][Oo][Gg][Ss]/" in ignore
    assert "/[Dd][Ii][Cc][Oo][Mm]/" not in ignore
    assert "/[Dd][Ii][Cc][Oo][Mm]_[Ll][Oo][Gg][Ss]/" not in ignore
    assert "*.[Dd][Cc][Mm]" in ignore
    assert "*.[Dd][Ii][Cc][Oo][Mm]" in ignore
    assert "*.[Dd][Ii][Rr]" in ignore
    assert "[Dd][Ii][Cc][Oo][Mm][Dd][Ii][Rr]" in ignore
    assert "*.[Nn][Ii][Ii]" in ignore
    assert "*.[Nn][Ii][Ii].[Gg][Zz]" in ignore


def test_documented_python_minimum_matches_package_metadata():
    for relative_path in ("docs/readme.md", "docs/user_manual.md", "readmemd.md"):
        readme = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "Python 3.10" in readme
        assert "Python 3.6" not in readme


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
    assert 'set "PIP_CONFIG_FILE=nul"' in installer
    assert "--no-index" in lower
    assert "--find-links" in lower
    assert "--only-binary=:all:" in lower
    assert "--force-reinstall" in lower
    assert "pip --isolated install" in lower
    assert "rt-dicom-toolkit==%application_version%" in lower
    assert "rt-dicom-toolkit==1.0.0" not in lower
    assert "__rtdt_project_version__" in lower
    assert 'call :select_python' in lower
    assert "import struct,sys,tkinter; raise systemexit" in lower
    assert 'rmdir /s /q "%bundle_root%.venv"' in lower
    assert "incompatible virtual environment could not be removed" in lower
    assert '"%base_python%" -m venv' in lower
    assert 'set "pythonhome="' in lower
    assert 'set "pythonpath="' in lower
    assert 'set "rtdt_data_root=%bundle_root%data"' in lower
    assert "call :preserve_legacy_data" in lower
    assert 'move /y "%legacy_data%"' in lower
    assert "legacy application data remains inside" in lower
    assert "http://" not in lower
    assert "https://" not in lower
    assert "invoke-webrequest" not in lower
    assert "curl" not in lower
    assert "%systemroot%\\system32\\windowspowershell\\v1.0\\powershell.exe" in lower
    assert "hashset[string]" in lower
    assert "unexpected bundle file" in lower
    assert "bundle inventory count mismatch" in lower
    assert "'.venv','.runtime','data','sha256sums.txt'" in lower
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
    for script in (launcher, smoke_launcher):
        assert 'set "PYTHONHOME="' in script
        assert 'set "PYTHONPATH="' in script
        assert 'set "RTDT_DATA_ROOT=%~dp0data"' in script


def test_application_data_root_can_be_kept_outside_the_environment(
    monkeypatch, tmp_path
):
    import rt_dicom_toolkit.config as config

    data_root = tmp_path / "persistent-data"
    monkeypatch.setenv("RTDT_DATA_ROOT", str(data_root))
    try:
        importlib.reload(config)
        assert config.DATA_DIR == data_root.absolute()
        assert config.DEFAULT_INPUT_DIR.is_dir()
        assert config.DEFAULT_ANONYMOUS_DIR.is_dir()
        assert config.DEFAULT_LOG_DIR.is_dir()
        assert config.DEFAULT_REPORT_DIR.is_dir()
    finally:
        monkeypatch.delenv("RTDT_DATA_ROOT", raising=False)
        importlib.reload(config)


def test_bundle_builder_checks_official_python_signature_and_uses_wheels_only():
    builder = (ROOT / "tools" / "prepare_offline_bundle.ps1").read_text(
        encoding="utf-8"
    )
    assert "https://www.python.org/ftp/python/" in builder
    assert "Get-AuthenticodeSignature" in builder
    assert "Python Software Foundation" in builder
    assert "import pip,setuptools,struct,sys,wheel" in builder
    assert "with pip, setuptools, and wheel is required" in builder
    assert '"-m", "pip", "--isolated", "download"' in builder
    assert '"--index-url", "https://pypi.org/simple"' in builder
    assert '"--no-cache-dir"' in builder
    assert ".Replace($VersionToken, $ProjectVersion)" in builder
    assert "exactly one project-version token" in builder
    assert '$env:PIP_CONFIG_FILE = "nul"' in builder
    assert '"--only-binary=:all:"' in builder
    assert '"--no-deps"' in builder
    assert "SHA256SUMS.txt" in builder
    assert '"DICOM"' not in builder
    assert '"DICOM_LOGS"' not in builder


def test_synthetic_dicom_smoke_workflow():
    run_smoke_test()
