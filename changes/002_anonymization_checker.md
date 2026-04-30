# Proposal: 匿名化チェッカーの実装 (CLI & GUI)

- Status: ✅ APPROVED
- Author: Antigravity
- Date: 2026-04-30

## 1. 背景 / 目的
匿名化処理後のDICOMファイルが「本当に匿名化できているか」を検証する手段を強化するため。
既存の `validator` は原本とのペア比較かつGUI依存であったため、以下のニーズに応える：
1. 匿名化済みディレクトリ単体での「個人情報残存スキャン」機能の提供
2. CLIからの高速な検証と、複数形式（MD, JSON, TXT）のレポート出力
3. 軽量かつスタンドアロンなツール構成

## 2. 変更内容
- **check_anonymization.py**: CLIベースのチェッカー。単独スキャンとペア比較の2モードを実装。
- **check_anonymization_gui.py**: CustomTkinterを用いたモダンなGUIラッパー。
- **start_checker_gui.bat**: GUI起動用バッチファイル。
- **DICOM_LOGS/**: レポート保存用ディレクトリの自動生成。

## 3. 影響範囲 / リスク
- 既存の `rt_dicom_toolkit` モジュールには一切変更を加えず、ルートにスタンドアロンツールとして配置するため、既存機能への影響はない。
- `pydicom` および `customtkinter` に依存。

## 4. テスト・検証計画
- `DICOM\MonacoPhantom03x03\anonymized` に対するスキャンとペア比較を実行し、正常終了を確認。
- 匿名化前の原本ディレクトリに対してスキャンを実行し、意図通り警告が出ることを確認。
- `pytest` により既存の単体テスト・統合テストがすべてPASSすることを維持。
