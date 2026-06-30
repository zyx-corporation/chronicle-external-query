# chronicle-external-query

`chronicle-external-query` は Chronicle Stack の下流にある派生コンシューマです。
Chronicle が生成した handoff bundle を読み取り、query / retrieval / runtime
の実行責務を Chronicle の一次記録境界の外側に保ちます。

English README: [README.md](README.md)

## 境界

- Chronicle `.chronicle/chronicle.jsonl` が一次記録として authoritative
- この repository は派生 export と handoff contract だけを消費する
- Chronicle への暗黙の write-back は行わない
- graph / vector / query runtime の責務はこの repo に置き、Chronicle core に戻さない

## 現在の対応範囲

この repository は現在、次を提供します。

- Chronicle handoff bundle directory の読込
- contract version、required file、required key の validation
- graph export の読込
- adapter skeleton の読込
- 実 bundle 由来の sanitized fixture による contract test
- graph-only / hybrid retrieval、shared provenance、provider-neutral vector seam
- runtime answer、evaluation artifact、markdown report の local-only flow
- clean checkout から再現できる smoke baseline
- committed baseline fixture と optional fixture pack を分離する
  pluggable fixture registry
- env-only credential discovery と opt-in test 分離を持つ provider plugin registry
- opt-in でだけ動作する local `gemma4` answer plugin
- optional な hosted provider plugin と baseline 比較評価

## Repository Layout

```text
chronicle-external-query/
  docs/
  contracts/
    chronicle/
  scripts/
  src/chronicle_external_query/
    ingest/
    retrieval/
    runtime/
    evaluation/
  tests/
```

## 主要ドキュメント

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Extension Roadmap](docs/extension-roadmap.md)
- [Pluggable Extension Spec](docs/pluggable-extension-spec.md)
- [Coding Guidelines](docs/coding-guidelines.md)
- [Development Workflow](docs/development-workflow.md)
- [Testing Strategy](docs/testing-strategy.md)
- [Retrieval Contract](docs/retrieval-contract.md)
- [Runtime Answer Contract](docs/runtime-answer-contract.md)
- [Chronicle Trial Alignment](docs/chronicle-trial-alignment.md)
- [Chronicle Write-back Boundary](docs/chronicle-writeback-boundary.md)
- [Clean Checkout](docs/clean-checkout.md)
- [Operator Runbook](docs/operator-runbook.md)
- [Release Automation](docs/releases/release-automation.md)
- [i18n Strategy](docs/i18n-strategy.md)
- [ADR Index](docs/adr/README.md)

## ローカル開発

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

baseline smoke を 1 コマンドで通す場合:

```bash
bash scripts/smoke_clean_checkout.sh
```

デフォルトの `python3` が 3.11 未満なら、`PYTHON_BIN` を明示します。

```bash
PYTHON_BIN=/usr/local/bin/python3.11 bash scripts/smoke_clean_checkout.sh
```

## ローカル CLI

```bash
chronicle-external-query validate-bundle /path/to/handoff-bundle --json
chronicle-external-query show-bundle /path/to/handoff-bundle --json
chronicle-external-query list-fixtures --json
chronicle-external-query list-plugins --json
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode graph --answer-plugin gemma4 --json
chronicle-external-query compare-query-runs /path/to/handoff-bundle --query "release planning context" --mode graph --answer-plugin openai-compatible-hosted --json
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode graph --json
chronicle-external-query render-artifact-report trial-artifact.json --output trial-report.md --json
chronicle-external-query render-comparison-report first-artifact.json second-artifact.json --output comparison-report.md --json
```

## Fixture Registry

Milestone F では、supported baseline を変えずに fixture 拡張面だけを
pluggable にしました。

- `baseline_minimal` と `baseline_representative` は引き続き committed
  baseline fixture として default test suite を支えます
- optional fixture pack は `fixture-pack.json` manifest で追加できます
- optional fixture pack directory は `--fixture-dir` または
  `CHRONICLE_EXTERNAL_QUERY_FIXTURE_DIRS` から opt-in で読み込みます

例:

```bash
chronicle-external-query list-fixtures --json --no-env-fixture-dirs
CHRONICLE_EXTERNAL_QUERY_FIXTURE_DIRS=/path/to/fixture-pack chronicle-external-query list-fixtures --json
```

## Provider Plugin Surface

Milestone G では provider plugin の seam だけを先に導入し、provider 自体は
supported baseline に混ぜていません。

- provider plugin は明示登録され、`chronicle-external-query list-plugins --json`
  で inspection できます
- credential は plugin ごとの環境変数に隔離されます
- default の `pytest` と smoke baseline は provider plugin test を実行しません
- provider が未設定でも baseline path は変化せず、available 状態だけが明示されます

現時点の built-in seam:

- `static-test-provider`
- required credential env var:
  `CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_API_KEY`
- optional endpoint override:
  `CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_ENDPOINT`
- runtime への実接続は引き続き reserved-only

opt-in provider test:

```bash
pytest --run-provider-plugins tests/providers/
```

## Local Gemma4 Plugin

Milestone H では、最初の実 answer-generation plugin として local `gemma4`
を追加しました。ただし deterministic baseline はデフォルトのまま残します。

- plugin 名: `gemma4`
- CLI 有効化: `--answer-plugin gemma4`
- 想定 runtime: OpenAI-compatible な `POST /v1/chat/completions`
- デフォルト path: `--answer-plugin` を省略した場合は従来どおり
- 失敗時: plugin を要求したのに未設定または到達不可なら明示エラー

必須環境変数:

- `GEMMA4_ENABLED=true`
- `GEMMA4_BASE_URL=http://127.0.0.1:11434`
- `GEMMA4_MODEL=gemma4`

任意環境変数:

- `GEMMA4_TIMEOUT=30`
- `GEMMA4_API_KEY=...`

例:

```bash
GEMMA4_ENABLED=true \
GEMMA4_BASE_URL=http://127.0.0.1:11434 \
GEMMA4_MODEL=gemma4 \
chronicle-external-query run-query tests/fixtures/query_engine_bundle/representative_cli_bundle --query "release planning follow-up context" --mode hybrid --vector-fixture tests/fixtures/vector_matches/representative-vector-matches.json --answer-plugin gemma4 --json
```

opt-in gemma4 test:

```bash
pytest --run-provider-plugins --run-gemma4 tests/providers/test_gemma4_plugin.py
```

## Hosted Provider Comparison

Milestone I では、最初の hosted provider plugin と、baseline との比較評価導線を
追加しました。

- hosted plugin 名: `openai-compatible-hosted`
- 比較 CLI:
  `chronicle-external-query compare-query-runs ... --answer-plugin openai-compatible-hosted`
- baseline smoke path: 変更なし
- 比較 contract: 既存の evaluation artifact shape と compare ロジックをそのまま利用

必須環境変数:

- `OPENAI_COMPATIBLE_HOSTED_ENABLED=true`
- `OPENAI_COMPATIBLE_HOSTED_BASE_URL=https://provider.example`
- `OPENAI_COMPATIBLE_HOSTED_MODEL=provider-model`
- `OPENAI_COMPATIBLE_HOSTED_API_KEY=...`

任意環境変数:

- `OPENAI_COMPATIBLE_HOSTED_TIMEOUT=30`

例:

```bash
OPENAI_COMPATIBLE_HOSTED_ENABLED=true \
OPENAI_COMPATIBLE_HOSTED_BASE_URL=https://provider.example \
OPENAI_COMPATIBLE_HOSTED_MODEL=provider-model \
OPENAI_COMPATIBLE_HOSTED_API_KEY=secret \
chronicle-external-query compare-query-runs tests/fixtures/query_engine_bundle/representative_cli_bundle --query "release planning follow-up context" --mode hybrid --vector-fixture tests/fixtures/vector_matches/representative-vector-matches.json --answer-plugin openai-compatible-hosted --baseline-output baseline-artifact.json --plugin-output hosted-artifact.json --json
```

opt-in hosted provider test:

```bash
pytest --run-provider-plugins --run-hosted-providers tests/providers/test_openai_compatible_hosted_plugin.py
```

## CI Baseline

```bash
bash scripts/smoke_clean_checkout.sh
```

同じ baseline を GitHub Actions の `main` 向け push / pull request でも実行します。

## Release Automation

Milestone J では baseline CI の先にある release automation を追加しました。

- release workflow: `.github/workflows/release.yml`
- release-candidate gate: `bash scripts/release_candidate_gate.sh`
- release notes generator:
  `python scripts/generate_release_notes.py --version vX.Y.Z`
- plugin compatibility report:
  `python scripts/check_plugin_compatibility.py`

optional plugin check は、明示的に要求しない限り baseline release を blocking
しません。

## リリース状況

現在の release-preparation target は `v0.3.0` です。

release-closeout artifacts:

- [v0.3.0 Release Notes](docs/releases/v0.3.0-release-notes.md)
- [v0.3.0 Completion Checklist](docs/releases/v0.3.0-completion-checklist.md)
- [v0.3.0 Boundary Summary](docs/releases/v0.3.0-boundary-summary.md)

最初の supported local downstream runtime baseline は
[docs/releases/v0.2.0-first-supported-baseline.md](docs/releases/v0.2.0-first-supported-baseline.md)
にまとめています。

今後の拡張方針は [docs/extension-roadmap.md](docs/extension-roadmap.md) と
[docs/pluggable-extension-spec.md](docs/pluggable-extension-spec.md) を参照してください。

現時点では Milestone K まで実装済みで、fixture 拡張は registry 経由、
provider credential は分離、`gemma4` と hosted provider は opt-in、
release automation は追加済み、Chronicle write-back は明示的に out of scope、
baseline smoke は従来どおり committed fixture 固定です。

この状態で、現在の supported boundary に対する `v0.3.0` リリース準備が
整っています。
