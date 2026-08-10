# Windows 10 オフライン導入手順

この手順は、インターネット未接続の Windows 10 x64 PC に RT DICOM Toolkit を
USB ストレージ経由で導入するためのものです。患者由来DICOMを導入確認には使用せず、
同梱スモークテストが実行時に生成する合成DICOMだけを使用します。

## 対象環境

- オンラインPC: Windows 10/11 x64、PowerShell 5.1以降、CPython 3.12 x64、pip
- オフラインPC: Windows 10 x64
- 同梱Python: CPython 3.12.10 x64
- インストール先: ZIPを展開したローカルフォルダ内の専用`.venv`

32-bit Windows、ARM64、Windows以外のOSはこのバンドルの対象外です。

## 1. オンラインPCでZIPを作る

リポジトリのルートでPowerShellを開きます。レビュー済みのコミットまたは作業ツリーを
使用し、実患者DICOMがGit管理対象に含まれていないことを確認してください。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\prepare_offline_bundle.ps1
```

作成用Pythonには `pip`、`setuptools`、`wheel` が必要です。不足している場合は、オンラインPCで次を実行してから再試行します。

```powershell
python -m pip install --upgrade pip setuptools wheel
```

同名ZIPを意図的に置換する場合だけ、`-Force`を追加します。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\prepare_offline_bundle.ps1 -Force
```

作成物:

```text
dist\rt-dicom-toolkit-offline-win64-1.0.0.zip
```

スクリプトは次を実行します。

1. ビルド用PythonがCPython 3.12 x64であることを確認
2. python.orgからPython 3.12.10 x64インストーラを取得
3. PythonインストーラのAuthenticode署名と署名者を確認
4. PyPIから固定バージョンのWindows x64 wheelだけを取得
5. RT DICOM Toolkit本体をwheel化
6. 実行用ソース、バッチ、文書、全wheel、Pythonに対するSHA-256一覧を作成
7. USB搬送用ZIPを作成

作成完了時に表示されるZIPのSHA-256を、USBとは別の安全な場所にも記録してください。
同梱の`SHA256SUMS.txt`は転送破損の検出用です。ZIP自体の真正性確認には、別に記録した
ZIPハッシュとの照合が必要です。

## 2. USBへコピーする

次のファイルをUSBストレージへコピーします。

```text
dist\rt-dicom-toolkit-offline-win64-1.0.0.zip
```

可能であれば、コピー後のZIPのSHA-256が作成時の値と一致することを確認します。

```powershell
Get-FileHash .\rt-dicom-toolkit-offline-win64-1.0.0.zip -Algorithm SHA256
```

患者DICOM、既存の`DICOM/`、`DICOM_LOGS/`はこのZIPに含まれません。

## 3. オフラインPCへインストールする

1. USB内のZIPを、書込み可能なローカルディスク上の空のフォルダへコピーします。
2. ZIPをその空のフォルダへ展開します。USB上で直接インストールしないでください。
3. 展開先の`install_offline.bat`をダブルクリックします。

管理者権限は通常不要です。インストーラは次の順に処理します。

- `SHA256SUMS.txt`に基づく全同梱ファイルの検証
- CPython 3.12.10 x64の確認。互換Pythonがなければ展開先の`.runtime`へ同梱版を導入
- 展開先の`.venv`への専用仮想環境作成
- `wheelhouse`だけを使った依存パッケージとアプリの導入
- `pip check`
- 合成DICOMスモークテスト

pipには次の通信禁止設定が常に指定されます。

```text
PIP_NO_INDEX=1
PIP_CONFIG_FILE=nul
--no-index
--find-links <同梱wheelhouse>
--only-binary=:all:
```

このため、オフライン導入処理がPyPIなどへ接続することはありません。

## 4. 起動する

`start_rt_dicom_toolkit.bat`をダブルクリックします。システムのPythonやPATHは使用せず、
専用`.venv`の`pythonw.exe`からGUIを起動します。既存Pythonを仮想環境の作成元として
使用した場合も、起動時に既存PythonやPATHを直接使用することはありません。

実患者DICOMを扱う前に、施設の運用規程、匿名化条件、出力先、アクセス権限を確認して
ください。スモークテスト成功は、あらゆるDICOMベンダー・モダリティでの匿名化品質を
保証するものではありません。

## 5. 再度スモークテストする

`smoke_test.bat`をダブルクリックします。成功時は次のメッセージが表示されます。

```text
SMOKE TEST PASSED: anonymizer, validator, template engine, and GUI imports
```

スモークテストは一時フォルダに最小の合成CT DICOMを作り、次を検証します。

- 匿名化ファイルの生成と標準DICOMとしての再読込
- PatientName、PatientID、SOP Instance UID、private tagの処理
- PixelDataの保持
- 匿名化前後の検証レポート
- Universal Templateの患者情報・幾何学情報同期とUID生成
- tkinter、CustomTkinter、matplotlib Tk backendのimport

一時データはテスト終了時に削除されます。

## 6. トラブルシューティング

### SHA-256 mismatch

ZIPの展開失敗、USB転送時の破損、ファイル変更が考えられます。導入を中止し、オンラインPCで
作成したZIPからコピーし直してください。検証を無効化して続行しないでください。

### Python installation failed

展開先が書込み可能か、十分な空き容量があるか、Windowsがx64かを確認してください。
USBやネットワークドライブではなくローカルディスクを使用します。

### Offline wheel installation failed

`wheelhouse`内のファイルを個別に変更・削除していないことを確認してください。
Python 3.12以外の環境へwheelを手動導入しないでください。

### GUIが表示されない

まず`smoke_test.bat`を実行します。スモークテストが成功しても画面が出ない場合は、
Windowsのイベントログ、セキュリティ製品によるブロック、画面外に残ったウィンドウ位置を
確認してください。

## 7. 再導入・削除

同じ展開先で`install_offline.bat`を再実行すると、同梱wheelから仮想環境を再確認・更新します。
GUIの既定の入出力・ログ・レポート保存先は、仮想環境とは分離された展開先の`data`フォルダです。
旧版が仮想環境内に作成した`data`は、再導入時に展開先の`data`へ移動します。既存の`data`と
重複する場合は`data\legacy-venv-data`へ退避し、同名の退避先も存在する場合はデータを削除せず
導入を停止します。

完全にやり直す場合も、展開先の`data`を別の安全な場所へ退避したうえで、展開先フォルダを削除し、
元のZIPを新しいローカルフォルダへ再展開してください。
