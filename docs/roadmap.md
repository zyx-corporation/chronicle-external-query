# Roadmap

This roadmap defines the path from the current working scaffold to an
operator-ready first completion state for `chronicle-external-query` as a
downstream derived consumer of Chronicle Stack.

## Guiding Boundary

- Chronicle `.chronicle/chronicle.jsonl` remains the primary record
- this repository consumes derived exports, not source records
- hosted query runtime, graph runtime, and vector runtime concerns live here
- no implicit write-back into Chronicle primary records is allowed

## What Completion Means

For this repository, "complete" does not mean feature exhaustion. It means the
first supported downstream runtime baseline is in place and can be handed to
another operator without tribal knowledge.

Completion for the current phase requires:

- a real or sanitized Chronicle handoff bundle can be validated locally
- graph and hybrid retrieval both produce reviewable provenance
- runtime answers and saved artifacts remain comparable across repeated runs
- a clean checkout can install, validate a bundle, run a query, and render
  reports from documented commands
- CI enforces the same local-first baseline that operators are expected to run

## Current Position

The repository already has a substantial working baseline:

- bundle ingest validation for required files, required keys, and contract
  versions
- graph export loading plus graph-only and hybrid retrieval scaffolding
- provider-neutral local vector fixtures for deterministic hybrid evaluation
- runtime answer assembly, evaluation artifact serialization, and markdown
  report rendering
- local CLI entrypoints for validation, bundle inspection, query execution,
  artifact inspection, artifact comparison, and report rendering
- CI smoke coverage for tests, validation, bundle inspection, graph queries,
  hybrid fixture-backed queries, and markdown report generation

This means the repo is past pure bootstrap. The remaining work is mostly
closure work: proving the baseline against representative Chronicle output,
tightening acceptance evidence, and closing the gap between "implemented" and
"ready to hand off."

## Milestone Sequence

### Milestone A: Contract Ingest Hardening

Status:
Complete for the first supported baseline. Representative sanitized Chronicle
bundle fixtures, traceable contract references, and drift-focused regression
coverage are now in place.

Goal:
Make Chronicle handoff bundles safe and explicit to ingest before retrieval or
runtime work expands.

Already in place:

- required-file validation for bundle contents
- required-key and top-level object-shape validation
- contract-version validation for manifest, handoff, graph, and adapter payloads
- import-validation error taxonomy for machine-readable CLI failures
- fixture-driven ingest tests with malformed and mismatch coverage

Remaining work:

1. expand fixture variety only when Chronicle-side contract shape changes
2. add new drift tests only when future contract revisions reveal new failure modes

Exit Criteria:

- at least one representative real Chronicle bundle fixture loads locally
- contract drift fails fast with readable and machine-readable output
- ingest validation rules are traceable to Chronicle-side contract material

Definition of Done:

- a new contributor can validate a representative bundle and understand why it
  fails without reading the code first

### Milestone B: Retrieval Provenance and Hybrid Expansion

Status:
Complete for the first supported baseline. Shared provenance, hybrid
composition, provider-neutral vector seams, and representative-bundle
regression coverage are now in place.

Goal:
Move from graph-only scaffolding to retrieval flows that are useful for real
local evaluation and downstream runtime comparison.

Already in place:

- shared retrieval provenance payload used across graph and hybrid paths
- graph retrieval with scoring and ordering behavior
- provider-neutral vector adapter seam with deterministic local fixture loading
- hybrid retrieval composition with overlap handling
- regression coverage for retrieval fixtures and provenance preservation

Remaining work:

1. expand retrieval fixtures only when Chronicle-side bundle shape or review
   needs change
2. refine scoring heuristics only when future acceptance runs reveal a concrete
   comparison problem

Exit Criteria:

- graph-only and hybrid outputs are stable enough to compare across runs
- provenance clearly distinguishes Chronicle-derived context from downstream
  scoring and merge behavior
- retrieval behavior has been reviewed against representative bundle content

Definition of Done:

- retrieval payloads can be inspected by a reviewer without guessing which
  fields are source-authored and which are downstream-derived

### Milestone C: Runtime Answering and Evaluation Loop

Status:
Complete for the first supported baseline. Runtime answer contracts, local
evaluation artifacts, Chronicle-aligned review mapping, and representative-query
regression coverage are now in place.

Goal:
Turn retrieval output into repeatable runtime answers and reviewable evaluation
artifacts.

Already in place:

- runtime answer contract and metadata model
- structured answer assembly with insufficiency handling
- evaluation artifact serialization and comparison support
- Chronicle trial alignment mapping for local downstream review
- markdown trial and comparison report rendering

Remaining work:

1. expand runtime regression fixtures only when future acceptance runs expose a
   concrete comparison problem
2. refine wording only when operator review needs change materially

Exit Criteria:

- runtime answers include query, provenance, and reviewable metadata
- local trial artifacts can be saved, inspected, compared, and rendered
- repeated-run behavior is stable enough for downstream review use

Definition of Done:

- local runtime outputs are reviewable artifacts rather than opaque debug logs

### Milestone D: Operational Packaging

Status:
Complete for the first supported baseline. A reproducible clean-checkout smoke
path, CI baseline, and operator documentation now point at the same local-only
verification flow.

Goal:
Make the repository easy to run, validate, and iterate on as a standalone
runtime implementation surface.

Already in place:

- public local CLI commands for validation, inspection, queries, and reports
- CI workflow covering tests and CLI smoke paths
- operator runbook, clean-checkout guide, and supporting docs
- deterministic local validation paths that do not require a hosted provider

Remaining work:

1. expand the smoke path only when new supported operator flows are added
2. document provider-backed paths separately if they ever become first-class
   supported options

Exit Criteria:

- a new checkout can install, validate a bundle, run a query, and render
  reports from documented commands
- CI verifies the same baseline path operators are expected to use
- operator setup no longer depends on repo-specific tribal knowledge

Definition of Done:

- an operator can clone the repo and complete the documented local-only flow
  without guesswork

### Milestone E: Completion and First Supported Trial Baseline

Status:
Complete for the first supported baseline. Completion evidence, deferrals, and
the release-ready handoff summary are now in place.

Goal:
Declare the first supported completion state for `chronicle-external-query`
without weakening the Chronicle boundary.

Scope:

- close or explicitly defer remaining A-D gaps
- run the documented path against representative Chronicle output
- capture acceptance evidence for validation, retrieval, runtime, and reporting
- confirm clean-checkout reproducibility and CI parity
- prepare a first release-ready handoff summary

Deliverables:

- completion checklist with pass/fail evidence
- representative-bundle acceptance run notes
- explicit defer list for anything intentionally left out of the first baseline
- release or handoff summary that states the supported local-first boundary

Exit Criteria:

- all blocking A-D work is closed or explicitly deferred
- representative Chronicle bundles pass the supported local workflow
- local verification and CI agree on the same supported baseline
- another operator can understand the supported scope from repo docs alone

Definition of Done:

- this repository can be handed off as the first supported local downstream
  runtime baseline for Chronicle-derived bundles

## Completion Artifacts

Release-closeout artifacts for the first supported baseline:

- [v0.2.0 Completion Checklist](releases/v0.2.0-completion-checklist.md)
- [v0.2.0 Deferred Items](releases/v0.2.0-defer-list.md)
- [v0.2.0 First Supported Baseline](releases/v0.2.0-first-supported-baseline.md)

Post-`v0.2.0` extension-release closeout artifacts:

- [v0.3.0 Completion Checklist](releases/v0.3.0-completion-checklist.md)
- [v0.3.0 Boundary Summary](releases/v0.3.0-boundary-summary.md)
- [v0.3.0 Release Notes](releases/v0.3.0-release-notes.md)
- [v0.3.0 Chronicle Stack Handoff](releases/v0.3.0-chronicle-stack-handoff.md)
