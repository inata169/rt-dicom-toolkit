from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_start_gui_uses_only_the_development_virtual_environment():
    launcher = (ROOT / "start_gui.bat").read_text(encoding="utf-8").lower()

    assert 'set "venv_python=%~dp0.venv\\scripts\\python.exe"' in launcher
    assert 'if not exist "%venv_python%"' in launcher
    assert '"%venv_python%" -m rt_dicom_toolkit' in launcher
    assert "python -m rt_dicom_toolkit" not in launcher.replace(
        '"%venv_python%" -m rt_dicom_toolkit', ""
    )


def test_start_gui_explains_fresh_clone_setup():
    launcher = (ROOT / "start_gui.bat").read_text(encoding="utf-8").lower()

    assert "python -m venv .venv" in launcher
    assert ".\\.venv\\scripts\\python.exe -m pip install" in launcher
    assert "rt_dicom_toolkit\\requirements.txt" in launcher
    assert "exit /b 1" in launcher


def test_readme_documents_the_same_development_environment():
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()

    assert "python -m venv .venv" in readme
    assert ".\\.venv\\scripts\\python.exe -m rt_dicom_toolkit" in readme
    assert "start_gui.bat" in readme
    assert "unconfigured system python" in readme
