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
- [Clean Checkout](docs/clean-checkout.md)
- [Operator Runbook](docs/operator-runbook.md)
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

## CI Baseline

```bash
bash scripts/smoke_clean_checkout.sh
```

同じ baseline を GitHub Actions の `main` 向け push / pull request でも実行します。

## リリース状況

最初の supported local downstream runtime baseline は
[docs/releases/v0.2.0-first-supported-baseline.md](docs/releases/v0.2.0-first-supported-baseline.md)
にまとめています。

今後の拡張方針は [docs/extension-roadmap.md](docs/extension-roadmap.md) と
[docs/pluggable-extension-spec.md](docs/pluggable-extension-spec.md) を参照してください。

現時点では Milestone F まで実装済みで、fixture 拡張は registry 経由、
baseline smoke は従来どおり committed fixture 固定です。
