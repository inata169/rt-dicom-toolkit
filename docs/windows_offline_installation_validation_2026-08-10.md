# Windows 10 オフライン導入検証記録（2026-08-10）

## 対象

- リポジトリ: `inata169/rt-dicom-toolkit`
- バンドル: `rt-dicom-toolkit-offline-win64-1.0.0.zip`
- バンドルSHA-256:
  `6f8a8fa07f71dd910c21af677279e74a865353f76f945fe544f7b2b36826b30a`
- 対象Python: CPython 3.12.10 x64
- 対象OS: Windows 10 x64

## 自動検証

開発環境では、外部通信先を到達不能な`127.0.0.1:9`へ固定した状態で、展開した
バンドルの`install_offline.bat`を実行した。

| 確認項目 | 結果 |
| --- | --- |
| PythonインストーラのAuthenticode署名 | PASS（Python Software Foundation） |
| ZIP内ペイロード59ファイルのSHA-256 | PASS |
| 固定依存wheel 17個＋アプリwheel 1個 | PASS |
| 専用`.venv`の作成 | PASS |
| `--no-index`でのwheel導入 | PASS |
| `pip check` | PASS |
| 合成DICOM匿名化 | PASS |
| 匿名化前後の検証 | PASS |
| Universal Template同期 | PASS |
| GUI依存のimport | PASS |
| pytest | 14件PASS |

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
