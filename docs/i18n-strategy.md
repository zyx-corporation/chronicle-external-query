# i18n Strategy

This document adapts Chronicle Stack's localization discipline for the
`chronicle-external-query` downstream runtime repository.

## Why i18n matters here

Even though this repository currently exposes developer-oriented Python code, it
will grow user-visible surfaces such as:

- CLI validation errors
- bundle inspection output
- retrieval summaries
- runtime answer metadata
- evaluation and trial reports

Those surfaces should not hardcode a single language assumption into the
repository's long-term contracts.

## Supported User Locales

Initial planned locales:

- `ja`
- `en`
- `zh-CN`

Defaults:

- default locale: `ja`
- fallback locale: `en`

## Boundary Rule

Localization is presentation behavior, not retrieval truth.

That means:

- localized strings may describe results, warnings, and boundaries
- localization must not change the underlying contract semantics
- localization must not strengthen uncertain or partial runtime outcomes

## What must be localizable

- CLI help and operator-facing messages
- import-validation failures intended for operators
- retrieval summaries and empty states
- runtime response summaries intended for human reading
- evaluation report headings and warning labels

## What may remain internal English for now

- Python identifiers
- internal helper names
- test function names
- low-level developer-only comments

## Translation Key Rule

When user-facing text becomes more than a one-off message, move it behind stable
semantic keys.

Recommended examples:

- `bundle.error.missing_required_files`
- `bundle.error.unsupported_contract_version`
- `retrieval.summary.graph_only`
- `retrieval.summary.hybrid`
- `runtime.answer.no_matches`
- `evaluation.warning.partial_provenance`

Avoid presentational keys like:

- `red_banner_text`
- `empty_label_1`

## Locale Selection Guidance

When a CLI or service entrypoint gains locale support, prefer:

1. explicit CLI option such as `--locale`
2. environment variable
3. repository or user config
4. system locale
5. fallback locale

## Wording Boundaries

Translations must preserve these distinctions:

- loaded vs validated
- matched vs accepted
- derived vs source-authored
- preview vs executed
- insufficient vs failed
- missing vs unsupported

These wording boundaries matter because this repository interprets downstream
data without owning Chronicle's primary records.

## Test Expectations for i18n

Localization changes should be tested for:

- key presence
- fallback behavior
- wording boundary preservation on critical messages
- stable semantics across `ja`, `en`, and `zh-CN`

## Adoption Plan

1. keep current developer-only strings simple and easy to externalize
2. introduce a message catalog before adding a public CLI
3. add locale-aware tests when the first operator-facing command lands
