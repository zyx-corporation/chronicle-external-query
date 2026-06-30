# Runtime Answer Contract

This document records the current local runtime answer contract for
`chronicle-external-query`.

## Goals

- produce reviewable local runtime outputs instead of opaque prompt dumps
- keep retrieval provenance attached to every answer
- preserve the difference between answer text, runtime status, and source-backed
  evidence

## Runtime Answer Fields

Current top-level fields:

- `query`
- `status`
- `answer_text`
- `prompt`
- `graph_matches`
- `provenance`
- `metadata`

## Status Values

Current statuses:

- `answered`
- `insufficient_context`

These are downstream runtime statuses only. They do not imply Chronicle review,
acceptance, or authoritative truth.

## Metadata Expectations

Current metadata includes:

- `status`
- `retrieval_mode`
- `match_count`
- `sources`
- `source_match_counts`
- `overlap_source_record_ids`
- `insufficiency_reasons`
- `top_match_source_record_ids`
- `top_match_sources`
- `coverage_summary`
- `answer_generator`
- `answer_generator_mode`
- `answer_generator_fallback_used`

When the baseline deterministic path is used:

- `answer_generator: deterministic_baseline`
- `answer_generator_mode: builtin`

When the local `gemma4` plugin is used:

- `answer_generator: gemma4`
- `answer_generator_mode: local_plugin`
- `answer_generator_model`
- `answer_generator_base_url`

## Evaluation Artifact Alignment

Runtime answers are serialized into local evaluation artifacts that preserve:

- artifact version
- query
- runtime status
- retrieval mode
- answer text
- metadata
- provenance
- matches

This supports repeated-run comparison without implying Chronicle-side trial
acceptance.

Rendered markdown trial reports should preserve at least:

- bundle contract versions
- retrieval source counts
- overlap source record ids
- insufficiency reasons when present

Representative-bundle runtime regression should also prove:

- the same query stays comparable across repeated local runs
- hybrid answers preserve overlap context without hiding graph-only evidence
- plugin-backed answers still serialize into the same artifact shape
