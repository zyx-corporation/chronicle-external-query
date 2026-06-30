# Retrieval Contract

This document records the current retrieval result contract shared across
graph-only and hybrid paths.

## Goals

- keep source-authored Chronicle identifiers separate from downstream scoring
- make match explanations inspectable without reading implementation details
- support graph-only, vector-only, overlap, and no-match comparisons

## Result Shape

Core result fields:

- `query`
- `retrieval_mode`
- `matches`
- `provenance`

Each `match` includes:

- `source`: where the match came from, such as `graph`, `vector`, or `hybrid_overlap`
- `identifier`: downstream retrieval identifier
- `source_record_id`: Chronicle-facing record identifier
- `entity_type`
- `title`
- `summary`
- `score`
- `matched_terms`
- `metadata`

## Graph Match Metadata

Graph matches currently expose:

- `graph_node_metadata`: raw graph node metadata copied through for inspection
- `matched_fields`: which graph fields contributed to the score

Current weighted field preference:

- `title`: 3.0
- `summary`: 2.0
- `node_type`: 1.5
- `source_id`: 1.0
- `node_id`: 0.5

These weights are heuristic and downstream-derived. They do not change
Chronicle's authority over the underlying source records.

## Provenance Shape

`provenance` currently includes:

- `query`
- `retrieval_mode`
- `sources`
- `match_count`
- `graph_node_count`
- `graph_edge_count`
- `source_match_counts`
- `overlap_source_record_ids`
- `insufficiency_reasons`

## Boundary Notes

- retrieval scores are downstream interpretation, not Chronicle truth
- overlap reporting should explain where graph and vector results converge
- insufficiency reasons should remain explicit instead of pretending success
