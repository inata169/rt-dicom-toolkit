# Proposal: 003 Preserve UID Reference Consistency

- Status: ✅ APPROVED
- Author: Antigravity (Architect)
- Date: 2026-04-30

## 1. Background and objective

### Original problems

The anonymizer had three design defects:

1. **Referenced UIDs inside sequences were not replaced.**
   `anonymize_dicom()` inspected only top-level attributes with
   `hasattr(dcm, tag_name)`, so values such as
   `ReferencedSOPSequence > ReferencedSOPInstanceUID` remained unchanged.
2. **The `uid_map` key format could not support reference lookup.** Keys used
   `f"{tag}_{str(x)}"`, for example `SOPInstanceUID_1.2.3.4`, so a referenced
   old value such as `1.2.3.4` could not directly retrieve the new UID.
3. **Processing required two passes.** File order is not guaranteed. If an
   RTSTRUCT was processed before its CT images, the SOP Instance UID mapping for
   the referenced images might not exist yet.

### RT DICOM reference structure

```text
CT Image         -> SOPInstanceUID
                   ^
RTSTRUCT         -> ReferencedFrameOfReferenceSequence
                   `- RTReferencedStudySequence
                      `- RTReferencedSeriesSequence
                         `- ContourImageSequence
                            `- ReferencedSOPInstanceUID  <- CT SOP Instance UID

RTPLAN           -> ReferencedStructureSetSequence
                   `- ReferencedSOPInstanceUID  <- RTSTRUCT SOP Instance UID

RTDOSE           -> ReferencedRTPlanSequence
                   `- ReferencedSOPInstanceUID  <- RTPLAN SOP Instance UID
```

If those reference chains are inconsistent after anonymization, DICOM viewers
may be unable to load the dataset correctly.

## 2. Changes

### 2.1 Update `core.py`

#### A. Key `uid_map` by the old UID value

```python
# Before: tag type plus UID value
self.uid_map.setdefault(f"{tag}_{str(x)}", generate_uid())

# After: UID value only
self.uid_map.setdefault(str(x), generate_uid())
```

DICOM UIDs are globally unique, so the tag name is not required to prevent a
collision.

#### B. Rework `process_directory()` into two passes

```text
Pass 1, collect UIDs:
  Read every file with dcmread(stop_before_pixels=True).
  Collect Study, Series, SOP, and Frame of Reference UIDs.
  Build old-to-new mappings in uid_map.

Pass 2, anonymize and replace references:
  Read every file with dcmread(force=True).
  Apply the normal anonymization profile.
  Recursively replace mapped UI elements with _replace_uid_references().
  Save the result.
```

#### C. Add `_replace_uid_references(self, dataset)`

```python
def _replace_uid_references(self, dataset):
    """Recursively replace mapped UI elements in a dataset."""
    replaced = 0
    for elem in dataset:
        if elem.VR == "SQ" and elem.value:
            for item in elem.value:
                if item is not None:
                    replaced += self._replace_uid_references(item)
        elif elem.VR == "UI" and elem.value:
            old_uid = str(elem.value)
            if old_uid in self.uid_map:
                elem.value = self.uid_map[old_uid]
                replaced += 1
    return replaced
```

#### D. Update file meta

Update `MediaStorageSOPInstanceUID` in file meta from `uid_map` as well. Keep it
consistent with the anonymized dataset's `SOPInstanceUID` after pass 2.

### 2.2 Update `profiles.py`

Use `anonymizer.uid_map` for all UID-related profile entries. Branching between
`consistent` and `generate` remains in
`get_modified_anonymization_profile()`.

```python
"StudyInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
"SeriesInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
"SOPInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
"FrameOfReferenceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
```

### 2.3 Update `get_modified_anonymization_profile()`

Remove the `uid_handling == "consistent"` branch because mapping is now the
default. Retain the `generate` branch for backward-compatible random generation.

### 2.4 Files

| File | Operation | Summary |
|---|---|---|
| `rt_dicom_toolkit/anonymizer/core.py` | Modify | UID keys, two passes, recursive replacement |
| `rt_dicom_toolkit/anonymizer/profiles.py` | Modify | Map-based UID lambdas |
| `tests/test_uid_consistency.py` | Add | UID-consistency unit tests |

## 3. Impact and risks

### Performance

- Pass 1 is lightweight because it uses `stop_before_pixels=True`.
- Pass 2 has approximately the same cost as the original processing.
- The estimated total increase was 20-30 percent, not double.

### Backward compatibility

- `uid_handling == "generate"` continues to generate a random UID on each use.
- Output file structure is unchanged; referenced UIDs become consistent.
- Previously anonymized data is unaffected. Reprocessing, if needed, starts
  from the original source.

### Incorrect replacement risk

Only UI VR elements whose old UID is present in `uid_map` are replaced, which
keeps the risk of unrelated replacement low.

## 4. Validation plan

### 4.1 Unit tests

Use synthetic DICOM to verify:

1. after changing a CT SOP Instance UID, the RTSTRUCT reference follows it;
2. after changing an RTSTRUCT SOP Instance UID, the RTPLAN reference follows it;
3. a shared Frame of Reference UID becomes the same new UID in CT and RTSTRUCT;
4. the same old UID always maps to the same new UID.

### 4.2 Integration validation

The original plan called for manual validation against an operational dataset.
Under the current repository rules, equivalent validation must use synthetic
DICOM and must confirm that references remain traversable after anonymization.

### 4.3 Existing tests

Keep `tests/test_anonymizer.py` passing.
