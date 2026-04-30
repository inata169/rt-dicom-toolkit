# Proposal: 003 UID参照の一貫性保持

- Status: ✅ APPROVED
- Author: Antigravity (Architect)
- Date: 2026-04-30

## 1. 背景 / 目的

### 現状の問題

現在の匿名化ツールには以下の3つの設計上の欠陥があります。

1. **シーケンス内部の参照UIDが書き換わらない**: `anonymize_dicom()` はトップレベルタグ（`hasattr(dcm, tag_name)`）のみを走査するため、シーケンス内部（例: `ReferencedSOPSequence > ReferencedSOPInstanceUID`）に含まれる参照UIDは一切置換されない。
2. **`uid_map` のキー形式が参照追跡に不適**: キーが `f"{tag}_{str(x)}"` 形式（例: `SOPInstanceUID_1.2.3.4`）のため、参照タグ側から旧UID値 `1.2.3.4` を引いて新UIDを取得できない。
3. **2パスが必要**: ファイル処理順が不定のため、例えば RTSTRUCT を先に処理した時点で参照先の CT 画像の SOPInstanceUID マッピングがまだ存在しない可能性がある。

### RT DICOM の参照構造

```
CT Image         → SOPInstanceUID
                   ↑
RTSTRUCT         → ReferencedFrameOfReferenceSequence
                   └ RTReferencedStudySequence
                     └ RTReferencedSeriesSequence
                       └ ContourImageSequence
                         └ ReferencedSOPInstanceUID  ← CT画像のSOPInstanceUID

RTPLAN           → ReferencedStructureSetSequence
                   └ ReferencedSOPInstanceUID  ← RTSTRUCTのSOPInstanceUID

RTDOSE           → ReferencedRTPlanSequence
                   └ ReferencedSOPInstanceUID  ← RTPLANのSOPInstanceUID
```

これらの参照チェーンが匿名化後も整合していないと、ビューア（Eclipse, RayStation, MIM等）でデータを読み込めなくなる。

## 2. 変更内容

### 2.1 `core.py` の修正

#### A. `uid_map` のキーを「旧UID値」に統一

```python
# 変更前（タグ種別＋UID値）
self.uid_map.setdefault(f"{tag}_{str(x)}", generate_uid())

# 変更後（UID値のみ）
self.uid_map.setdefault(str(x), generate_uid())
```

同一のDICOM UID値は（DICOM規格上）グローバルに一意であるため、タグ名を付けなくても衝突しない。

#### B. `process_directory()` を2パスに再構成

```
Pass 1 (UID収集):
  全ファイルを dcmread(stop_before_pixels=True) で軽量読込
  → 主要UID(Study/Series/SOP/FrameOfReference) を収集
  → self.uid_map に旧→新のマッピングを構築

Pass 2 (匿名化＋参照置換):
  全ファイルを dcmread(force=True) で読込
  → 通常の匿名化プロファイル適用
  → _replace_uid_references() でシーケンス内の全UIタグを再帰走査＋置換
  → 保存
```

#### C. `_replace_uid_references(self, dataset)` メソッドの新規追加

```python
def _replace_uid_references(self, dataset):
    """データセット内の全UIタグをuid_mapに基づき再帰的に置換"""
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

#### D. `file_meta` の更新

`MediaStorageSOPInstanceUID` (file_meta内) も uid_map に基づき更新する。
現在は L382-383 で匿名化後の `dcm.SOPInstanceUID` をコピーしているが、Pass 2 で参照置換した結果と整合させる。

### 2.2 `profiles.py` の修正

UID関連エントリのラムダを、`anonymizer.uid_map` を参照する形式に変更。
`consistent` / `generate` 両モードの分岐は `get_modified_anonymization_profile()` で行うため、profiles.py のデフォルトは `uid_map` ベースに統一。

```python
# 変更後
"StudyInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
"SeriesInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
"SOPInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
"FrameOfReferenceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
```

### 2.3 `get_modified_anonymization_profile()` の修正

`uid_handling == "consistent"` の分岐を削除（デフォルトで uid_map ベースになるため不要に）。
`uid_handling == "generate"` の場合のみ毎回新規生成に切り替え（互換性のため残す）。

### 2.4 ファイル一覧

| ファイル | 操作 | 変更概要 |
|---------|------|---------|
| `rt_dicom_toolkit/anonymizer/core.py` | MODIFY | uid_mapキー変更、2パス化、参照置換メソッド追加 |
| `rt_dicom_toolkit/anonymizer/profiles.py` | MODIFY | UIDラムダをuid_mapベースに統一 |
| `tests/test_uid_consistency.py` | NEW | UID一貫性のユニットテスト |

## 3. 影響範囲 / リスク

### パフォーマンス
- **Pass 1** は `stop_before_pixels=True` で読むため高速（CT 300枚でも数秒）。
- **Pass 2** は現行と同等の処理時間。
- 全体で **+20〜30%** の処理時間増を見込む（2倍にはならない）。

### 後方互換性
- `uid_handling == "generate"` モードは引き続き「毎回ランダムUID」のまま動作する。
- 匿名化後のファイル自体の構造には変更なし。参照UIDが正しくなるだけ。
- **既に匿名化済みのデータには影響しない**（再匿名化が必要な場合は原本から再実行）。

### 誤置換のリスク
- VR(UI) タグのみを対象とし、uid_map に登録済みのUIDだけを置換するため、無関係な値を書き換えるリスクは極めて低い。

## 4. テスト・検証計画

### 4.1 ユニットテスト (`tests/test_uid_consistency.py`)

以下のシナリオをモックDICOMで検証：

1. **CT + RTSTRUCT ペア**: CT画像のSOPInstanceUIDが変更された後、RTSTRUCTの `ReferencedSOPInstanceUID` が新しいUIDに追従していること。
2. **RTSTRUCT + RTPLAN ペア**: RTSTRUCTのSOPInstanceUIDが変更された後、RTPLANの `ReferencedSOPInstanceUID` が追従していること。
3. **FrameOfReferenceUID**: CT/RTSTRUCTで共有される `FrameOfReferenceUID` が同一の新UIDに置換されていること。
4. **uid_map の一貫性**: 同じ旧UIDに対して常に同じ新UIDが返ること。

### 4.2 統合テスト（手動）

実データ（原本）を匿名化し、以下を確認：
- `check_anonymization.py --scan` で個人情報残存なし
- 匿名化後ファイルをpydicomで読み込み、参照チェーンが辿れること

### 4.3 既存テストの確認

- `pytest tests/test_anonymizer.py` が引き続きPASSすること
