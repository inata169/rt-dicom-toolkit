# 放射線治療DICOM匿名化・検証ツールキット

放射線治療（RT）用DICOMファイルの匿名化と検証を行うための包括的なツールキットです。

## 特徴

### 匿名化ツール

- 完全または部分的な匿名化
- カスタマイズ可能な匿名化プロファイル
- 臨床的に重要な構造の保持（臓器名など）
- 一貫した患者ID対応づけ
- UID管理（一貫性維持または再生成）
- プライベートタグの処理（削除または保持）
- 詳細なログとレポート
- 元のディレクトリ構造保持オプション
- GUIとコマンドラインインターフェース

### 検証ツール

- 匿名化されたDICOMファイルの包括的な検証
- 元のファイルと匿名化されたファイルの比較
- 残留個人情報（PHI）の検出
- 構造保持の検証
- 匿名化品質に関する統計レポート
- 検証結果の視覚化
- 詳細なレポート
- GUIとコマンドラインインターフェース

## インストール

### 必要条件

- Python 3.10以上
- 依存パッケージ: pydicom, numpy, matplotlib, pandas

### インストール手順

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/rt-dicom-toolkit.git
cd rt-dicom-toolkit

# 依存パッケージをインストール
pip install -r requirements.txt

# パッケージとしてインストール（オプション）
pip install -e .

使用方法
GUIモード
bashCopy# 匿名化ツール
python -m rt_dicom_toolkit.gui.anonymizer_gui

# 検証ツール
python -m rt_dicom_toolkit.gui.validator_gui
コマンドラインモード
bashCopy# 匿名化ツール
python -m rt_dicom_toolkit.cli anonymize --input /path/to/input --output /path/to/output

# 検証ツール
python -m rt_dicom_toolkit.cli validate --original /path/to/original --anonymized /path/to/anonymized
プロジェクト構造
プロジェクトは以下のモジュールで構成されています：

anonymizer: DICOM匿名化機能
validator: 匿名化検証機能
gui: グラフィカルユーザーインターフェース
utils: ユーティリティ関数
config: 設定パラメータ
cli: コマンドラインインターフェース

ライセンス
[LICENSE情報を記載]
貢献
[貢献方法の説明を記載]
Copy
#### 7.2 `docs/user_manual.md`

```markdown
# RT DICOM匿名化・検証ツール ユーザーマニュアル

## 目次

1. [はじめに](#1-はじめに)
2. [匿名化ツール](#2-匿名化ツール)
3. [検証ツール](#3-検証ツール)
4. [トラブルシューティング](#4-トラブルシューティング)
5. [付録](#5-付録)

## 1. はじめに

RT DICOM匿名化・検証ツールは、放射線治療に関連するDICOMファイルの匿名化と検証を行うためのソフトウェアスイートです。このツールは、医学研究や多施設共同研究でのデータ共有において、患者のプライバシーを保護しつつ、放射線治療計画データを適切に扱うことを目的としています。

### 1.1 システム要件

- **オペレーティングシステム**：Windows 10以降、macOS 10.14以降、各種Linuxディストリビューション
- **Python環境**：Python 3.10以上
- **必要ライブラリ**：pydicom, pandas, matplotlib, numpy

### 1.2 インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/rt-dicom-toolkit.git
cd rt-dicom-toolkit

# 依存パッケージをインストール
pip install -r requirements.txt

# パッケージとしてインストール（オプション）
pip install -e .
2. 匿名化ツール
2.1 起動方法
GUIモード:
bashCopypython -m rt_dicom_toolkit.gui.anonymizer_gui
コマンドラインモード:
bashCopypython -m rt_dicom_toolkit.cli anonymize --input /path/to/input --output /path/to/output
2.2 使用方法
[詳細な使用方法をスクリーンショット付きで記載]
2.3 匿名化設定
[匿名化設定のオプションと詳細な説明を記載]
3. 検証ツール
3.1 起動方法
GUIモード:
bashCopypython -m rt_dicom_toolkit.gui.validator_gui
コマンドラインモード:
bashCopypython -m rt_dicom_toolkit.cli validate --original /path/to/original --anonymized /path/to/anonymized
3.2 使用方法
[詳細な使用方法をスクリーンショット付きで記載]
3.3 検証レポート
[検証レポートの読み方と解釈方法を記載]
4. トラブルシューティング
[よくあるエラーと対処法を記載]
5. 付録
[ファイル形式、タグリスト、コマンドライン引数の詳細などを記載]
Copy
## 移行計画

現在のコードから新しいモジュール化されたコードベースへの移行には、以下のステップを提案します。

1. **モジュール構造の作成**: 上記のディレクトリ階層を作成し、各モジュールの初期化ファイルを作成します。

2. **コアロジックの抽出**: 既存のコードから各モジュールのコアロジックを抽出し、適切なファイルに配置します。

3. **テスト**: 各モジュールの動作を確認するための基本的なテストを作成し、実行します。

4. **GUIの移行**: GUIコードを移行し、コアロジックと正しく連携することを確認します。

5. **CLIの実装**: コマンドラインインターフェイスを実装します。

6. **ドキュメントの作成**: ユーザーマニュアルと開発者ガイドを作成し、必要に応じて更新します。

7. **パッケージ化**: 必要な設定ファイル（setup.py, requirements.txt）を作成し、パッケージとしてインストール可能にします。

8. **既存コードの削除**: 新しいコードベースが完全に動作することを確認したら、古いコードファイルを削除し、新しいコードのみを残します。

このモジュール化により、コードの保守性、拡張性、再利用性が向上し、将来的な機能追加や修正がより容易になります。Retry
