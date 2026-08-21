"""
DICOM template engine.
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
    Synchronize selected source DICOM attributes into a template.
    """
    
    def __init__(self, template_path: str):
        """
        Args:
            template_path: Path to the template DICOM file.
        """
        self.template_path = template_path
        # force=True supports unknown tags and incomplete file metadata.
        self._template_dcm = pydicom.dcmread(template_path, force=True)
        
    def get_template_copy(self) -> pydicom.dataset.FileDataset:
        """Return a deep copy of the loaded template."""
        return copy.deepcopy(self._template_dcm)
        
    def sync_from_source(self, source_dcm_path: str, 
                         sync_patient: bool = True, 
                         sync_geometry: bool = True,
                         sync_rt_specific: bool = True) -> pydicom.dataset.FileDataset:
        """
        Return a new dataset with selected source attributes synchronized.
        
        Args:
            source_dcm_path: Path to the source DICOM file.
            sync_patient: Synchronize patient attributes when true.
            sync_geometry: Synchronize geometry attributes when true.
            sync_rt_specific: Synchronize RT-specific attributes when true.
            
        Returns:
            A synchronized copy of the template dataset.
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
            
        # Copy selected attributes.
        self._copy_tags(source_dcm, target_dcm, tags_to_sync)
        
        # Warn when template and source modalities differ.
        if hasattr(source_dcm, 'Modality') and hasattr(target_dcm, 'Modality'):
            if source_dcm.Modality != target_dcm.Modality:
                logger.warning(f"Modality mismatch. Source: {source_dcm.Modality}, Template: {target_dcm.Modality}")
                
        # Template output is a new instance, so create new UIDs.
        target_dcm.SOPInstanceUID = generate_uid()
        # Treat each output as an independent series.
        target_dcm.SeriesInstanceUID = generate_uid()
        
        if hasattr(target_dcm, 'file_meta') and target_dcm.file_meta is not None:
            target_dcm.file_meta.MediaStorageSOPInstanceUID = target_dcm.SOPInstanceUID
            
        return target_dcm
        
    def _copy_tags(self, source: pydicom.dataset.Dataset, target: pydicom.dataset.Dataset, tag_names: list):
        """Copy the listed DICOM keywords from source to target."""
        copied_count = 0
        for tag_name in tag_names:
            if hasattr(source, tag_name):
                value = getattr(source, tag_name)
                # Replace the target value or add it when absent.
                setattr(target, tag_name, value)
                copied_count += 1
        logger.debug(f"Synchronized {copied_count} attributes.")
