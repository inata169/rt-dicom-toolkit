import pytest
import shutil
import pydicom
from pathlib import Path
from rt_dicom_toolkit.anonymizer.core import RTDicomAnonymizer


def test_integration_anonymize(dicom_test_dir, temp_output_dir):
    """単一ファイルを使った匿名化の統合テスト（高速版）"""
    source_file = dicom_test_dir / "RTPLAN_PHITStest.dcm"

    if not source_file.exists():
        pytest.skip(f"Test file {source_file} not found")

    # 1ファイルだけを temp の input_dir にコピーしてテスト
    input_dir = temp_output_dir / "input"
    input_dir.mkdir()
    shutil.copy2(source_file, input_dir / source_file.name)

    output_dir = temp_output_dir / "output"
    log_dir = temp_output_dir / "logs"

    anonymizer = RTDicomAnonymizer()
    anonymizer.input_dir = input_dir
    anonymizer.output_dir = output_dir
    anonymizer.log_dir = log_dir

    anonymizer.process_directory()

    # 出力ファイルが生成されていることを確認
    output_file = output_dir / source_file.name
    assert output_file.exists(), f"Output file not found at {output_file}"

    # 案A: force=True で読む（非標準形式にも対応）
    # 案B の効果として、write_like_original=False で保存されたファイルは
    # force=False でも読めるはずだが、念のため force=True も許容する形でテスト
    dcm = pydicom.dcmread(str(output_file), force=False)

    # 匿名化されていることを確認
    assert str(dcm.PatientName) == "ANONYMOUS", f"PatientName not anonymized: {dcm.PatientName}"
    assert hasattr(dcm, 'PatientID'), "PatientID missing"
    assert len(str(dcm.StationName)) <= 16 if hasattr(dcm, 'StationName') else True

    # 標準 DICOM ヘッダーが付与されていることを確認（案B の効果）
    assert hasattr(dcm, 'file_meta'), "file_meta missing - DICOM header not written"
    assert hasattr(dcm.file_meta, 'TransferSyntaxUID'), "TransferSyntaxUID missing in file_meta"


def test_uid_consistency(dicom_test_dir, temp_output_dir):
    """UID一貫性モードのテスト"""
    source_file = dicom_test_dir / "RTPLAN_PHITStest.dcm"
    if not source_file.exists():
        pytest.skip(f"Test file {source_file} not found")

    input_dir = temp_output_dir / "input"
    input_dir.mkdir()
    shutil.copy2(source_file, input_dir / source_file.name)

    anonymizer = RTDicomAnonymizer()
    anonymizer.uid_handling = "consistent"
    anonymizer.input_dir = input_dir
    anonymizer.output_dir = temp_output_dir / "output"
    anonymizer.log_dir = temp_output_dir / "logs"

    anonymizer.process_directory()

    # uid_map が作成されていることを確認
    assert len(anonymizer.uid_map) > 0, "uid_map should be populated in consistent mode"
