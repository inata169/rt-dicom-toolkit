# Windows 10 オフライン導入検証記録（2026-08-10）

## 対象

- リポジトリ: `inata169/rt-dicom-toolkit`
- バンドル: `rt-dicom-toolkit-offline-win64-1.0.0.zip`
- バンドル作成元コミット: `ff1a08b91d938a86287d35bc25af79ffac3f3c62`
- バンドルSHA-256:
  `36e2074be41bbbd2043a18ec28f98621b29148766d4c98f940884d1e5fdf77da`
- 対象Python: CPython 3.12.10 x64
- 対象OS: Windows 10 x64

## 自動検証

バンドル作成は`PYTHONHOME`と`PYTHONPATH`に無効なパスを設定した状態で実行し、
producer Pythonとそのビルドサブプロセスが継承環境から隔離されることを確認した。

開発環境では、外部通信先を到達不能な`127.0.0.1:9`へ固定し、`PIP_FIND_LINKS`、
`PIP_INDEX_URL`、`PIP_EXTRA_INDEX_URL`を到達不能なURLへ設定した状態で、展開した
バンドルの`install_offline.bat`を実行した。`PYTHONHOME`と`PYTHONPATH`にも無効な
パスを設定し、バッチファイルによる環境分離を確認した。

| 確認項目 | 結果 |
| --- | --- |
| PythonインストーラのAuthenticode署名 | PASS（Python Software Foundation） |
| ZIP内ペイロード59ファイルのSHA-256 | PASS |
| 固定依存wheel 17個＋アプリwheel 1個 | PASS |
| 専用`.venv`の作成 | PASS |
| `--isolated --no-index`でのwheel導入 | PASS |
| `python.exe`が欠損した`.venv`のデータ退避・再作成 | PASS |
| 非Python実行ファイルへ置換した`.venv`の検出・再作成 | PASS |
| 旧`.venv`内データの退避とSHA-256一致 | PASS |
| 同一版アプリファイル破損後の強制再導入 | PASS |
| `pip check` | PASS |
| 合成DICOM匿名化 | PASS |
| 匿名化前後の検証 | PASS |
| Universal Template同期 | PASS |
| GUI依存のimport | PASS |
| pytest | 17件PASS |

スモークテストには実患者データを使用せず、実行時に生成して終了時に削除する最小の
合成CT DICOMだけを使用した。

## Windows 10オフライン実機確認

2026-08-10、利用者から次の結果が報告された。

- インターネット未接続のWindows 10 PCへGUIをインストールできた。
- 専用環境からGUIを起動できた。
- GUIを実際に使用し、正常に動作することを確認できた。

実機の詳細なWindowsビルド番号は本記録では未収集である。

## 結論

本バンドルは、Windows 10 x64オフラインPCへのUSB経由導入、専用仮想環境での
実行、および主要機能の利用が可能であることを確認した。

今後バンドル内容または依存ロックを変更した場合は、ZIPのSHA-256を更新し、
`install_offline.bat`、`pip check`、合成DICOMスモークテスト、GUI目視起動を再確認する。
