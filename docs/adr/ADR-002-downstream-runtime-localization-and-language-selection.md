# ADR-002: Downstream Runtime Localization and Language Selection

## Status

Accepted

## Date

2026-06-28

## Related documents

- [i18n Strategy](../i18n-strategy.md)
- [Testing Strategy](../testing-strategy.md)
- [Architecture](../architecture.md)
- Chronicle Stack `ADR-002: i18n and Language Selection`
- Chronicle Stack `ADR 0087: Downstream Query-Engine Handoff Stays Read-Only`

## Context

This repository will likely expose operator-facing messages before it exposes a
full end-user application. Even so, bundle validation, retrieval summaries, and
evaluation reports will become user-visible surfaces that cross language
boundaries.

Because `chronicle-external-query` interprets derived Chronicle exports, wording
matters. A poorly chosen translation can make a preview look executed, make a
match look accepted, or make a downstream inference look source-authored.

Chronicle Stack already treats localization as a first-class boundary concern.
This repository should inherit that discipline before its first stable CLI or
reporting surface arrives.

## Decision

`chronicle-external-query` will treat localization as presentation behavior and
will preserve semantic wording boundaries across locales.

Initial supported user locales are:

- `ja`
- `en`
- `zh-CN`

Default locale:

- `ja`

Fallback locale:

- `en`

User-facing strings that become part of stable operator workflows should move to
semantic translation keys before the repository publishes a stable CLI surface.

## Consequences

- future CLI and report messages must be designed for externalization
- translations must preserve the difference between derived, validated,
  preview-only, matched, accepted, missing, and unsupported states
- localization tests become part of acceptance for operator-facing surfaces

## Non-goals

This ADR does not:

- require immediate translation of every existing document
- require locale plumbing before a public CLI exists
- require translation of internal identifiers or developer-only names
