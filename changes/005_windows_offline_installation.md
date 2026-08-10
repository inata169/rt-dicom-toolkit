# Proposal: Windows 10 オフライン導入パッケージ

- Status: ✅ APPROVED
- Author: Codex (Developer Agent)
- Date: 2026-08-10

## 1. 背景 / 目的

インターネット未接続の Windows 10 x64 PC に、USB ストレージ経由で
RT DICOM Toolkit を導入できるようにする。オンライン PC で公式 CPython
インストーラ、Windows 用 wheel、リポジトリ本体を一つの ZIP に収集し、
オフライン PC では外部通信を行わず、専用仮想環境へインストールする。

既に `dicomxphits` で動作確認されている方式を参考にしつつ、本リポジトリの
依存関係と起動方法に合わせた最小構成とする。

## 2. 調査結果

### 2.1 Python 対応範囲

- `setup.py` は `python_requires=">=3.6"` としている。
- ルート README は Python 3.10 以上、古い `docs/readme.md` は 3.6 以上と記載し、
  現状は整合していない。
- 実行コード自体には Python 3.10 より新しい構文は見つからなかった。
- 現在の主要依存のうち `matplotlib 3.10.3` が Python 3.10 以上を要求するため、
  現行依存を含む実用上の下限は Python 3.10 である。
- Windows オフライン配布の固定対象は、`dicomxphits` でも使用している
  **CPython 3.12.10 64-bit** とする。
- CPython 3.12.10 64-bit 上で既存テスト 9 件がすべて PASS した。

### 2.2 実際のランタイム依存

ソースの import、`setup.py`、requirements、README、現在の動作環境を照合した。

- コア: `pydicom`, `numpy`, `pandas`, `matplotlib`
- 標準 GUI: `customtkinter`
- `customtkinter` の依存: `darkdetect`, `packaging`
- `matplotlib` / `pandas` の推移依存: `contourpy`, `cycler`, `fonttools`,
  `kiwisolver`, `pillow`, `pyparsing`, `python-dateutil`, `six`, `pytz`, `tzdata`

現状の `setup.py` と `rt_dicom_toolkit/requirements.txt` には
`customtkinter` がなく、README の手動インストール手順だけがこれを補っている。
この不整合を解消する必要がある。

調査環境で既存テストを通過した直接依存の組合せは次のとおり。

- `pydicom==2.4.4`
- `numpy==1.26.4`
- `pandas==2.3.1`
- `matplotlib==3.10.3`
- `customtkinter==5.2.2`
- `darkdetect==0.8.0`

オフライン用ロックには、上記に加えて解決された推移依存を全て完全固定する。

## 3. 変更内容

### 3.1 依存・パッケージ情報

- `setup.py` の Python 下限を 3.10 に合わせ、標準 GUI の直接依存
  `customtkinter` を追加する。
- ランタイム依存一覧を現行コードと一致させる。
- CPython 3.12 / Windows x64 専用の完全固定 requirements を追加する。

### 3.2 オンライン PC 用バンドル作成

PowerShell スクリプトを追加し、次を一括実行する。

1. 実行環境が Windows、CPython 3.12、64-bit であることを確認する。
2. python.org から CPython 3.12.10 x64 インストーラを取得する。
3. Authenticode 署名と署名者を確認する。
4. PyPI から CPython 3.12 / `win_amd64` の wheel のみを取得する。
5. リポジトリ本体を wheel 化する。
6. Python、全 wheel、導入・起動・スモークテスト用ファイルの SHA-256 一覧を作る。
7. `dist/` に USB 搬送用 ZIP を作る。

患者データやローカル生成物の混入を防ぐため、アプリ本体は Git 管理対象から
作成し、`DICOM/`, `DICOM_LOGS/`, `.git/`, 仮想環境、キャッシュを含めない。

### 3.3 オフライン PC 用導入・起動

- `install_offline.bat`
  - バンドルの SHA-256 を検証する。
  - CPython 3.12.10 x64がなければ、同梱 Python をローカルの専用ランタイムへ
    無人導入する。互換Pythonが既にある場合は仮想環境の作成元にのみ使用する。
  - バンドル内に専用 `.venv` を作る。
  - `PIP_NO_INDEX=1`, `PIP_CONFIG_FILE=nul`, `--isolated`, `--no-index`,
    `--find-links` を指定し、同梱 wheel だけからインストールする。
  - `pip check` と import 確認を行う。
- `start_rt_dicom_toolkit.bat`
  - 専用 `.venv` の `pythonw.exe` だけを使って GUI を起動する。
- `smoke_test.bat`
  - 専用 `.venv` で合成 DICOM スモークテストを実行する。

バンドルは USB 上で直接実行せず、書込み可能なローカルフォルダへコピー・展開して
使用する手順とする。

### 3.4 合成 DICOM スモークテスト

患者由来データを一切使わず、実行時の一時ディレクトリに最小の合成 DICOM を生成し、
次を確認する。

- 匿名化: PatientName / PatientID / UID / private tag が期待どおり処理され、
  標準 DICOM として再読込できる。
- 検証: 匿名化前後の比較が完了し、主要タグの変更と構造・PixelData の保持を検出する。
- Universal Template: 患者情報・幾何学情報の同期と新規 SOP Instance UID の生成を確認する。
- GUI 依存: `tkinter`, `customtkinter`, matplotlib Tk backend を import できる。

### 3.5 文書化

オンライン PC でのバンドル作成、USB 搬送、オフライン PC での導入、起動、
スモークテスト、ログ確認、再導入、代表的なエラーの切り分けを日本語で文書化する。

## 4. 影響範囲 / リスク

- **依存定義の不整合**: `customtkinter` の追加で、パッケージ導入だけでも標準 GUI が
  起動できる状態へ合わせる。コア処理のロジックは変更しない。
- **Windows 10 の版・アーキテクチャ**: 対象は Windows 10 x64 とする。
  32-bit Windows と ARM64 は対象外。
- **Python 3.12.10 固定**: 同じ wheel を確実に使うため、オフラインバンドルは
  CPython 3.12 ABI に固定する。通常のソース利用は Python 3.10 以上を維持する。
- **Tkinter**: GUI のため、Python インストーラで Tcl/Tk を除外しない。
- **OS証明書状態**: オンライン作成時の Authenticode 検証は、Windows の証明書ストアが
  正常であることを前提とする。
- **ZIP改ざん対策の限界**: 同梱 SHA-256 一覧は転送破損検出には有効だが、一覧自体を
  含むバンドル全体の真正性は、別経路で公開する ZIP ハッシュとの照合が必要。
- **既存の未追跡DICOM**: 現在の作業ツリーに `DICOM/` と `DICOM_LOGS/` があるが、
  内容には触れず、バンドルにもテストにも含めない。
- **既存ユーザー変更**: `99-handover_context.md` の変更には触れない。

## 5. テスト・検証計画

1. CPython 3.12.10 x64 で既存 pytest 9 件を再実行する。
2. 依存定義、wheel 固定、バッチのオフライン指定、患者データ除外を自動テストする。
3. 合成 DICOM スモークテストを通常環境で実行する。
4. オンライン PC 用スクリプトで実バンドル ZIP を作成し、全ファイルが wheel または
   許可された同梱物だけであること、全 SHA-256 が一致することを検査する。
5. 新しいローカルフォルダへバンドルを展開し、ネットワーク依存なしで
   `install_offline.bat` 相当の導入を検証する。
6. 専用 `.venv` から `pip check`、スモークテスト、GUI import を実行する。

実 GUI の表示操作は自動テストでは行わず、起動バッチと GUI import を自動確認し、
最終的な画面表示を Windows 10 オフライン実機の確認項目として文書化する。

## 6. 実装・検証結果

- 実施日: 2026-08-10
- CPython 3.12.10 x64で合計17件のpytestがPASS。
- Python 3.12.10 x64公式インストーラのAuthenticode署名は`Valid`、署名者は
  Python Software Foundationであることを確認。
- 固定依存wheel 17個とアプリwheel 1個、合計18個を収録。
- ZIP内のペイロード59ファイルすべてについてSHA-256検証がPASS。
- HTTP/HTTPS/ALL proxyとpip取得元を到達不能な`127.0.0.1:9`へ設定した状態で、
  専用`.venv`の作成、`--isolated --no-index`インストール、`pip check`、
  合成DICOMスモークテストがPASS。
- `python.exe`欠損・非Python実行ファイル置換の各`.venv`を検出して再作成し、
  旧データのSHA-256一致と同一版パッケージの破損修復を確認。
- 専用`.venv`のPythonは3.12.10、64-bitで、アプリが同仮想環境の
  `site-packages`から読み込まれることを確認。
- 物理的にネットワークを切断したWindows 10実機で、GUIの導入・起動・利用が
  正常に行えることを利用者が確認。

生成物:

```text
dist/rt-dicom-toolkit-offline-win64-1.0.0.zip
source commit: 898e2d8adc3060764041fb6814cd59597cac594d
SHA-256: bb4912e2286ed60ed1ade7aee9a86b00f09b4beeb5dbe3df7d86ad71eca8e642
```
