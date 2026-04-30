import os
import pytest
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from rt_dicom_toolkit.template import DICOMTemplateEngine

@pytest.fixture
def mock_dicom_files(tmp_path):
    """テスト用のモックDICOMファイルを生成する"""
    # テンプレートファイル
    template_path = tmp_path / "template.dcm"
    template_dcm = FileDataset(str(template_path), {}, file_meta=FileMetaDataset())
    template_dcm.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    template_dcm.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.2" # RT DOSE
    template_dcm.file_meta.MediaStorageSOPInstanceUID = generate_uid()
    template_dcm.is_little_endian = True
    template_dcm.is_implicit_VR = False
    
    template_dcm.Modality = "RTDOSE"
    template_dcm.PatientName = "TEMPLATE^PATIENT"
    template_dcm.PatientID = "TMPL001"
    template_dcm.ImagePositionPatient = [0, 0, 0]
    template_dcm.PixelSpacing = [1.0, 1.0]
    template_dcm.SOPInstanceUID = template_dcm.file_meta.MediaStorageSOPInstanceUID
    template_dcm.save_as(str(template_path), write_like_original=False)
    
    # ソースファイル
    source_path = tmp_path / "source.dcm"
    source_dcm = FileDataset(str(source_path), {}, file_meta=FileMetaDataset())
    source_dcm.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    source_dcm.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.2"
    source_dcm.file_meta.MediaStorageSOPInstanceUID = generate_uid()
    source_dcm.is_little_endian = True
    source_dcm.is_implicit_VR = False
    
    source_dcm.Modality = "RTDOSE"
    source_dcm.PatientName = "REAL^PATIENT"
    source_dcm.PatientID = "REAL123"
    source_dcm.ImagePositionPatient = [-100.5, -50.0, 25.5]
    source_dcm.PixelSpacing = [2.5, 2.5]
    source_dcm.SOPInstanceUID = source_dcm.file_meta.MediaStorageSOPInstanceUID
    source_dcm.save_as(str(source_path), write_like_original=False)
    
    return str(template_path), str(source_path)

def test_template_engine_init(mock_dicom_files):
    template_path, _ = mock_dicom_files
    engine = DICOMTemplateEngine(template_path)
    
    assert engine.template_path == template_path
    assert engine._template_dcm.PatientID == "TMPL001"

def test_sync_from_source(mock_dicom_files):
    template_path, source_path = mock_dicom_files
    engine = DICOMTemplateEngine(template_path)
    
    # 同期実行
    synced_dcm = engine.sync_from_source(source_path)
    
    # 患者情報がソースから同期されているか
    assert synced_dcm.PatientName == "REAL^PATIENT"
    assert synced_dcm.PatientID == "REAL123"
    
    # 幾何学情報がソースから同期されているか
    assert synced_dcm.ImagePositionPatient == [-100.5, -50.0, 25.5]
    assert synced_dcm.PixelSpacing == [2.5, 2.5]
    
    # 新しいUIDが生成されているか
    assert synced_dcm.SOPInstanceUID != engine._template_dcm.SOPInstanceUID
    assert synced_dcm.file_meta.MediaStorageSOPInstanceUID == synced_dcm.SOPInstanceUID
    
def test_sync_partial(mock_dicom_files):
    template_path, source_path = mock_dicom_files
    engine = DICOMTemplateEngine(template_path)
    
    # 幾何学情報のみ同期
    synced_dcm = engine.sync_from_source(source_path, sync_patient=False)
    
    # 患者情報はテンプレートのまま
    assert synced_dcm.PatientID == "TMPL001"
    
    # 幾何学情報はソースのもの
    assert synced_dcm.PixelSpacing == [2.5, 2.5]
