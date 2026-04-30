# Proposal: 004 Universal DICOM Template の実装

- Status: ✅ APPROVED
- Author: Antigravity
- Date: 2026-04-30

## 1. 背景 / 目的

### 現状の問題
PHITSからDICOM（RTDOSE等）へ変換する際、ベースとなる臨床DICOMファイル（原本）の構造がメーカーや出力設定によって異なり、変換スクリプトが特定のタグ構成に依存している場合にエラーが発生したり、出力されたDICOMがビューアで正しく表示されなかったりすることがあります。

### 解決策
「Universal Template」戦略を採用します。これは、あらかじめ用意した「標準的でクリーンなDICOMファイル（テンプレート）」をベースとし、そこに原本DICOMから抽出した特定の幾何学的パラメータ（座標、解像度等）や患者情報を注入して新しいDICOMを生成する手法です。これにより、出力ファイルの構造が常に一定に保たれ、システムの安定性が向上します。

## 2. 変更内容

### 2.1 新規モジュール `rt_dicom_toolkit/template/`
- **`engine.py`**: テンプレート操作の中核ロジック。
  - `DICOMTemplateEngine` クラスを実装。
  - `inject_tags(template_path, source_tags_dict)`: タグの注入。
  - `sync_geometry(template_path, source_dicom_path)`: 幾何学情報の同期。
- **`tags.py`**: 同期すべき標準タグリストの定義。
  - `GEOMETRY_TAGS`: `ImagePositionPatient`, `PixelSpacing`, `Rows`, `Columns` 等。
  - `PATIENT_TAGS`: `PatientName`, `PatientID`, `StudyInstanceUID` 等。

### 2.2 CLIの拡張 (`rt_dicom_toolkit/cli.py`)
- `--template` オプションの追加。
- `template-base` コマンド（または既存コマンドのサブオプション）の実装。

### 2.3 GUIの拡張 (`rt_dicom_toolkit/gui/`)
- テンプレートファイルを選択するUI要素の追加。

## 3. 影響範囲 / リスク
- **既存の匿名化機能**: 影響なし。本機能は独立したツール/モードとして提供。
- **モダリティ不一致**: テンプレート（例: CT）と原本（例: RTDOSE）のモダリティが異なる場合、手動でのタグ調整が必要になる可能性がある。初期実装では警告を出す。

## 4. テスト・検証計画

### 4.1 ユニットテスト
- テンプレートファイルに特定の値が正しく注入されることを確認。
- 幾何学情報（座標・間隔）が原本と一致するように更新されることを確認。

### 4.2 統合テスト
- `DICOM/sample.dcm` をテンプレートとして使用し、実データから抽出したパラメータで新しいDICOMを生成。
- 生成されたDICOMを DICOM チェッカーでスキャンし、エラーがないことを確認。
- 線量分布などの幾何学的整合性を確認。
