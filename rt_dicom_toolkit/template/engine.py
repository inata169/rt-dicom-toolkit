"""
DICOMテンプレートエンジン
"""
import copy
import logging
from typing import Dict, Any, Optional

import pydicom
from pydicom.uid import generate_uid

from .tags import PATIENT_TAGS, GEOMETRY_TAGS, RT_SPECIFIC_TAGS

logger = logging.getLogger(__name__)

class DICOMTemplateEngine:
    """
    テンプレートとなるDICOMファイルに、別のDICOMファイルから情報を抽出・合成するクラス
    """
    
    def __init__(self, template_path: str):
        """
        Args:
            template_path: テンプレートとなるDICOMファイルのパス
        """
        self.template_path = template_path
        # force=True で読み込み、未知のタグや不完全なメタデータにも対応
        self._template_dcm = pydicom.dcmread(template_path, force=True)
        
    def get_template_copy(self) -> pydicom.dataset.FileDataset:
        """テンプレートのディープコピーを返す"""
        return copy.deepcopy(self._template_dcm)
        
    def sync_from_source(self, source_dcm_path: str, 
                         sync_patient: bool = True, 
                         sync_geometry: bool = True,
                         sync_rt_specific: bool = True) -> pydicom.dataset.FileDataset:
        """
        元のDICOMファイルから情報を抽出し、テンプレートに合成して新しいデータセットを返す
        
        Args:
            source_dcm_path: 情報の抽出元となるDICOMファイルのパス
            sync_patient: 患者情報を同期するか
            sync_geometry: 幾何学情報を同期するか
            sync_rt_specific: RT系特有の情報を同期するか
            
        Returns:
            合成済みの新しいDICOMデータセット
        """
        source_dcm = pydicom.dcmread(source_dcm_path, force=True)
        target_dcm = self.get_template_copy()
        
        tags_to_sync = []
        if sync_patient:
            tags_to_sync.extend(PATIENT_TAGS)
        if sync_geometry:
            tags_to_sync.extend(GEOMETRY_TAGS)
        if sync_rt_specific:
            tags_to_sync.extend(RT_SPECIFIC_TAGS)
            
        # タグのコピー
        self._copy_tags(source_dcm, target_dcm, tags_to_sync)
        
        # モダリティ不一致の警告
        if hasattr(source_dcm, 'Modality') and hasattr(target_dcm, 'Modality'):
            if source_dcm.Modality != target_dcm.Modality:
                logger.warning(f"Modality mismatch. Source: {source_dcm.Modality}, Template: {target_dcm.Modality}")
                
        # テンプレート化＝新しいインスタンス生成なので、UIDを更新
        target_dcm.SOPInstanceUID = generate_uid()
        # シリーズをまとめるか分けるかは要件によるが、今回は独立したファイルとして扱うためSeriesInstanceUIDも更新
        target_dcm.SeriesInstanceUID = generate_uid()
        
        if hasattr(target_dcm, 'file_meta') and target_dcm.file_meta is not None:
            target_dcm.file_meta.MediaStorageSOPInstanceUID = target_dcm.SOPInstanceUID
            
        return target_dcm
        
    def _copy_tags(self, source: pydicom.dataset.Dataset, target: pydicom.dataset.Dataset, tag_names: list):
        """指定されたタグのリストをsourceからtargetへコピーする"""
        copied_count = 0
        for tag_name in tag_names:
            if hasattr(source, tag_name):
                value = getattr(source, tag_name)
                # target に上書き（または新規追加）
                setattr(target, tag_name, value)
                copied_count += 1
        logger.debug(f"{copied_count} 個のタグを同期しました。")

