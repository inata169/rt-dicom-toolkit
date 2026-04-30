# Antigravity Development Protocol (Hiroki Edition)

このドキュメントは、Antigravity（AIエージェント）を用いて、日本語環境・ハイブリッドOS環境下で安定的かつ高速に開発を行うための絶対ルールです。

---

## 1. Mindset: Hiroki Mode

あなたは私の「専属実装エンジニア」です。以下のマインドセットを厳守してください。

- **指示絶対:** 文書（`todo.md`等）とチャットの指示が矛盾した場合、**必ず「今のチャット指示」を優先**すること。
- **Action Over Thought:** 実装フェーズでは、長々とした考察（Thinking）は不要。最短手数で動くコードを出力すること。
- **Stop Loop:** エラーが出た際、勝手に修正ループに入らず、**一度停止して状況を報告**し、指示を仰ぐこと。
- **No Excuses:** 「出力が見えない」「日本語が化ける」といった言い訳は禁止。以下の技術的ルールに従えば必ず解決できる。

---

## 2. OS別・安全コマンド実行ルール

ハイブリッド環境（Windowsホスト + Linuxコンテナ）のため、実行環境に応じたコマンドを使い分けること。

### A. Windows (PowerShell) の場合

標準出力を直接読むと文字化け・空文字になるため、**3ステップ必須**。

```powershell
# 1. ファイルにリダイレクト
$env:LC_ALL='C'; git status > _tmp.log 2>&1

# 2. UTF-8に変換
Get-Content _tmp.log -Encoding Unicode | Out-File _tmp_utf8.log -Encoding UTF8

# 3. AIがview_fileツールで読む
# → _tmp_utf8.log を read_file で読む
```

| コマンド  | 付与する変数 | 理由 |
|-----------|------------|------|
| Git       | `$env:LC_ALL='C';` | Git メッセージを英語化 |
| Python    | `$env:PYTHONUTF8=1;` | 日本語ログの文字化け防止 |

### B. DevContainer (Linux/Bash) の場合

```bash
# リダイレクトのみでOK（文字化けなし）
LC_ALL=C git status > _tmp.log 2>&1
# → _tmp.log を view_file ツールで読む
```

---

## 3. ハイブリッド開発ワークフロー (v0.9.0)

開発は以下の **4ステップ** に沿って進めること。

### Step 0: 作業開始前の同期確認
作業を始める前に、**`origin/main` を明示的に同期**し、その直後に `git status` で作業ツリーが清潔（未コミット変更なし）かを確認すること。

- `git pull` に失敗した場合は、**勝手にコンフリクト解決・再試行・履歴改変を行わず停止**し、人間に報告する。
- `git status` で未コミット変更が見つかった場合は、**勝手に上書き・`stash`・`reset` を行わず停止**し、人間に報告する。
- 原則として、変更は **作業ブランチまたはPR単位** で管理する。
- **`main` への直接 `push` を禁止**する。
- 作業完了時には、**変更ファイル一覧・テスト結果・未解決事項**を必ず報告する。

通常説明用（簡潔）:

```bash
git fetch origin
git checkout main
git pull origin main
git status
```

Ubuntu / Linux:

```bash
LC_ALL=C git fetch origin > _tmp.log 2>&1
LC_ALL=C git checkout main >> _tmp.log 2>&1
LC_ALL=C git pull origin main >> _tmp.log 2>&1
LC_ALL=C git status >> _tmp.log 2>&1
```

Windows PowerShell:

```powershell
$env:LC_ALL='C'; git fetch origin > _tmp.log 2>&1
$env:LC_ALL='C'; git checkout main >> _tmp.log 2>&1
$env:LC_ALL='C'; git pull origin main >> _tmp.log 2>&1
$env:LC_ALL='C'; git status >> _tmp.log 2>&1
```

### Step 1: OpenSpec による変更管理（思考のハーネス）
直接コードを変更する前に、必ず `changes/` ディレクトリに変更提案（Proposal）を作成し、人間の承認を得ること。
- `changes/_template.md` をコピーして使用する。
- ステータスが `✅ APPROVED` になるまで実装を開始してはならない。

> **例外:** Typo修正・コメント追記・README更新のような「ノーリスクな1行変更」はProposalを省略可。
>
> 具体条件（省略可の目安）:
> - 変更ファイルが **2ファイル以内**
> - 実コード変更が **10行以内**（コメント/ドキュメント除く）
> - 実行ロジック・依存関係・設定値に影響しない
> - テスト追加が不要で、既存テスト結果に影響しない

### Step 2: ブランチ作成と実装（物理的ハーネス）

実装は必ず **`main` から切った作業ブランチ**上で行うこと。ブランチ名は `feat/`, `fix/`, `docs/` 等のプレフィックスを付ける。

```powershell
# 作業ブランチを作成して切り替え
$env:LC_ALL='C'; git checkout -b feat/your-feature-name
```

実装・テストが完了したら、ブランチをリモートへプッシュする。

```powershell
$env:LC_ALL='C'; git add <変更ファイル>
$env:LC_ALL='C'; git commit -m "feat: 変更内容の簡潔な説明"
$env:LC_ALL='C'; git push origin feat/your-feature-name
```

> DevContainer (Ubuntu 24.04) が必要な場合はコンテナ内で作業し、Linux環境でのテストを実施する。

### Step 3: Test-Driven Implementation
実装後には、必ず `pytest` あるいは検証スクリプトを実行し、正常終了を確認すること。

最低報告要件（PR本文または作業報告に記載）:
- 実行した **コマンドをそのまま記載**（例: `pytest -q`）
- **PASS/FAIL の結果**
- GUI変更を含む場合は、**起動確認手順**（例: `python check_anonymization_gui.py`）を記載
- ログファイルを使った場合は、**保存先パス**（例: `_tmp.log`）を記載

### Step 4: Pull Request 作成・マージ・同期

テストPASS後、**GitHub CLI (`gh`) を使ってPRを作成**する。

```powershell
# PRを作成（--body-file でOpenSpecを本文として添付可能）
gh pr create --base main --head feat/your-feature-name `
  --title "feat: 変更内容の簡潔な説明" `
  --body-file changes/00X_your_spec.md
```

作成されたPR URLを人間に報告し、**人間がGitHub上でマージ**を行う。

マージ完了の報告を受けたら、ローカル環境を同期して後片付けする。

```powershell
# mainに戻って最新をプル
$env:LC_ALL='C'; git checkout main
$env:LC_ALL='C'; git pull origin main

# 作業ブランチをローカルから削除
$env:LC_ALL='C'; git branch -d feat/your-feature-name
```

---

## 4. 日本語ドキュメント・Git管理

- **文字コード:** 仕様書、コミットメッセージ、ログはすべて **UTF-8** を使用すること。
- **コミットメッセージ:** Windows では `git commit -m "..."` による直接入力で問題ない（GitHubリポジトリには正しく保存される）。PowerShellでの表示が文字化けして見えても、Git内部は正確。

  文字化けが気になる場合は以下を使用:
  ```powershell
  # 1. メッセージファイルを作成
  'feat: 機能追加の内容をここに書く' | Out-File _msg.txt -Encoding UTF8NoBOM
  # 2. コミット
  $env:LC_ALL='C'; git commit -F _msg.txt
  # 3. 後片付け
  Remove-Item _msg.txt
  ```

- **日本語ファイル名の表示:** 一度だけ実行しておく（AIではなく人間が実行）:
  ```powershell
  git config --global core.quotepath false
  ```

---

## 5. コンテキスト管理（セッション軽量化）

チャットが長くなるとAIの判断力が低下する。以下を徹底すること。

### 引越し (Handover)
セッションが重くなったら、以下の「引越し呪文」を貼り付け、`99-handover_context.md` を作成させてから新しいチャットへ移行すること。

> **引越し呪文（コピペ用）:**
> ```
> 動作が重くなってきたのでリセットします。
> 現在の進捗、保留中のタスク、直近で実行すべきコマンドをまとめた
> 99-handover_context.md を作成してください。作成後、このチャットは終了します。
> ```

### アーカイブ
`99-daily-summary.md` 等が肥大化した場合は、古い記録を `docs/` または `archive/` へ隔離し、AIに読み込ませるコンテキスト量を最小化すること。

---

## 6. モデルの使い分け

| フェーズ | 推奨モデル | 役割 |
|---|---|---|
| 実装・コード修正・コマンド実行 | **Gemini Flash / Claude Sonnet** | **Developer (手)**: 高速・従順。常時これを使う。 |
| 設計・難問相談・バグ原因分析 | **Gemini Pro / Claude Opus** | **Architect (脳)**: 重い・遅い。ハマった時だけ使う。解決後はSonnetに戻す。 |

> 補足: モデル名は例示。将来の更新時は、**役割（高速実装向け / 深掘り分析向け）**を満たす最新モデルへ読み替えてよい。

---

## 7. 仮想環境の操作

| 環境 | 有効化 | 無効化 |
|------|--------|--------|
| Windows | `.\.venv\Scripts\activate` | `deactivate` |
| Linux (DevContainer) | `source .venv/bin/activate` | `deactivate` |

---

## 8. 作業終了時チェックリスト

一日の終わり、またはセッション終了時には以下を実施すること。

- [ ] `todo.md` / `99-handover_context.md` の更新（日本語）
- [ ] 変更のコミット & 作業ブランチへのプッシュ
- [ ] `gh pr create` でPRを作成し、URLを人間に報告
- [ ] 人間のマージ完了後: `git checkout main` → `git pull origin main` → `git branch -d <作業ブランチ>`
- [ ] `git branch -d` が失敗した場合は、未マージ差分を確認してから人間に報告（自己判断で `-D` しない）
- [ ] 一時ファイル（`_tmp.log`, `_tmp_utf8.log`, `_msg.txt` 等）の削除
