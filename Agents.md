# AI Agents (Antigravity Protocol)

このプロジェクトでは、AIエージェント（Antigravity）を用いて開発効率を最大化します。作業の性質に応じて、以下の2つのモード（エージェント役割）を使い分けます。

## 1. Developer Agent (手)
**推奨モデル:** Gemini Flash / Claude Sonnet 等の高速モデル
**主な役割:**
- 確定した仕様（OpenSpec）に基づく高速なコード実装
- テストコード（pytest）の作成と実行
- 単純なバグ修正、リファクタリング、Lintエラーの解消
- コマンド（ファイル操作、Git操作）の迅速な実行
**特徴:** Action Over Thought（考察よりも行動を優先）。エラーが出たら勝手に修正ループに入らず、状況を報告して人間に指示を仰ぐ。

## 2. Architect Agent (脳)
**推奨モデル:** Gemini Pro / Claude Opus 等の高推論モデル
**主な役割:**
- アーキテクチャ設計、複雑な課題の解決策の立案
- OpenSpec（変更提案・仕様書）の作成とレビュー
- 難解なバグの根本原因分析
- プロジェクト全体の方向性や技術選定に関する相談
**特徴:** 実行よりも深い洞察と計画を優先。方向性が確定したら、Developer Agentに実装を引き継ぐ。

---

## エージェントとOpenSpecの連携ワークフロー
1. **提案 (Architect/Developer):** 新機能や大きな変更を行う場合、エージェントは `changes/` に OpenSpec 形式で提案書を作成する。
2. **レビュー (Human):** 人間が OpenSpec を確認し、ステータスを `✅ APPROVED` に変更する。
3. **実装 (Developer):** 承認された OpenSpec に従い、Developer Agent がコードを実装・検証する。
4. **報告 (Developer):** テストがすべてPASSしたことを人間に報告し、作業を完了する。
