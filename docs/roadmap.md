# Roadmap

This roadmap records the recommended sequencing for `chronicle-external-query`
as a downstream derived consumer of Chronicle Stack.

## Guiding Boundary

- Chronicle `.chronicle/chronicle.jsonl` remains the primary record
- this repository consumes derived exports, not source records
- hosted query runtime, graph runtime, and vector runtime concerns live here
- no implicit write-back into Chronicle primary records is allowed

## Current Position

The repository currently has a working early scaffold for:

- Chronicle handoff bundle loading
- required-file and contract-version validation
- graph export loading
- graph-only and hybrid retrieval provenance scaffolding
- provider-neutral local vector fixtures for deterministic hybrid evaluation
- answer composition, result serialization, and markdown trial-report rendering
- local CLI entrypoints for bundle validation, bundle inspection, query execution,
  artifact comparison, and artifact report rendering

This means Milestone A is underway with real bundle fixtures and validation
coverage in place, and Milestone B has started its shared provenance contract
work. Milestone C has entered local evaluation artifact shaping, and Milestone D
now has a broader standalone CLI surface plus CI smoke coverage for validation,
bundle inspection, graph queries, and hybrid fixture-backed queries.

## Milestone Sequence

### Milestone A: Contract Ingest Hardening

Goal:
Make Chronicle handoff bundles safe and explicit to ingest before retrieval or
runtime work expands.

Scope:

- validate bundle structure against required files and object shapes
- add contract version checks for `query_engine_handoff.json` and `graph.json`
- vendor or reference Chronicle-side schema and contract notes under `contracts/`
- add fixture bundles captured from real Chronicle output
- expose clear import-validation errors for contract drift

Detailed Work Packages:

1. Fixture capture and reduction
   - collect one or more real Chronicle-generated bundle examples
   - reduce or sanitize fixtures so they can live in-repo
   - document fixture provenance and known limitations
2. Structural validation hardening
   - validate top-level object shapes for manifest, handoff, and graph payloads
   - detect missing required keys and incompatible types
   - standardize import-validation error categories
3. Version and compatibility checks
   - compare handoff contract version against supported versions
   - compare graph export version against supported versions
   - define unsupported-version behavior and messaging
4. Contract reference material
   - vendor stable schema fragments or contract notes under `contracts/chronicle/`
   - link each validation rule back to its Chronicle-side contract source
5. Test expansion
   - add fixture-driven contract tests
   - cover malformed JSON, missing files, missing keys, and version drift

Deliverables:

- real or sanitized Chronicle bundle fixtures
- explicit import-validation rules and error taxonomy
- contract/version validation in the ingest path
- contract tests proving drift detection

Exit Criteria:

- real Chronicle bundle fixtures load locally
- contract mismatch fails fast with readable error output
- test coverage proves missing-file, malformed-json, and version-drift behavior

Dependencies:

- Chronicle-side handoff and graph export contracts remain inspectable
- at least one representative bundle can be captured from Chronicle output

Risks:

- overfitting validation to a single fixture bundle
- baking unstable Chronicle-side details into this repo too early

Definition of Done:

- a new contributor can run fixture-based validation locally and understand why a
  bundle fails without reading the code first

### Milestone B: Retrieval Provenance and Hybrid Expansion

Goal:
Move from graph-only scaffolding to retrieval flows that are useful for real
local evaluation and downstream runtime comparison.

Scope:

- enrich graph retrieval scoring and matched-node metadata
- add retrieval provenance summaries to every query result
- define a vector-retrieval adapter interface without binding to a single vendor
- compose graph and vector retrieval into a stable hybrid read path
- add evaluation fixtures for overlap, insufficiency, and empty-result cases

Detailed Work Packages:

1. Provenance contract design
   - define a shared retrieval result payload used by graph-only and hybrid paths
   - separate source-authored identifiers from downstream-derived scores
   - define insufficiency and no-match markers
2. Graph retrieval hardening
   - improve graph matching heuristics and tie-breaking rules
   - expose matched-node metadata and evidence summary fields
   - make scoring behavior testable and documented
3. Vector adapter seam
   - define a provider-neutral vector retrieval interface
   - support a no-provider local fallback for deterministic tests
   - document what is adapter responsibility vs runtime responsibility
4. Hybrid composition
   - merge graph and vector matches into one stable payload
   - define overlap, supplement, and empty-result handling
   - preserve mode-specific provenance
5. Retrieval evaluation fixtures
   - create deterministic cases for graph-only, hybrid, overlap, and no-match
   - add regression tests for provenance loss or ordering drift

Deliverables:

- structured retrieval provenance payload
- hardened graph retriever behavior
- vector adapter interface and local fallback
- hybrid retrieval result contract
- retrieval-focused fixtures and regression tests

Exit Criteria:

- graph-only and hybrid retrieval both return structured provenance
- retrieval outputs are stable enough to compare across repeated runs
- tests cover graph-only, hybrid, and no-match scenarios

Dependencies:

- Milestone A validation path is stable enough to trust input bundles
- a retrieval provenance contract is accepted before hybrid logic expands

Risks:

- hiding provider assumptions inside a supposedly neutral vector interface
- returning scores without enough provenance context to interpret them safely

Definition of Done:

- retrieval payloads can be inspected by humans and compared by tests without
  guessing which fields came from Chronicle exports and which came from the
  downstream runtime

### Milestone C: Runtime Answering and Evaluation Loop

Goal:
Turn retrieval output into repeatable runtime answers and reviewable evaluation
artifacts.

Scope:

- add answer composition beyond prompt scaffolding
- define runtime response metadata for traceability
- serialize evaluation artifacts for trial runs
- compare runtime outcomes across queries and bundle versions
- align output shape with Chronicle-side trial review expectations

Detailed Work Packages:

1. Runtime response contract
   - define answer payload fields, metadata fields, and provenance attachment
   - distinguish query execution mode, retrieval coverage, and uncertainty state
2. Answer composition
   - move from prompt scaffolding to structured answer assembly
   - keep no-provider fallback deterministic where possible
   - preserve the difference between answer text and runtime metadata
3. Evaluation artifact shape
   - serialize local trial outputs in a stable reviewable format
   - include bundle identity, query, retrieval mode, and insufficiency markers
   - define how repeated runs are compared
4. Chronicle alignment
   - map local evaluation artifacts to Chronicle-side trial review expectations
   - avoid implying that local evaluation equals Chronicle acceptance
5. Runtime regression coverage
   - add tests for no-match, partial-match, and repeated-run behavior
   - add tests for metadata stability and insufficiency wording

Deliverables:

- stable runtime answer contract
- structured evaluation artifact format
- comparison-ready local trial outputs
- runtime metadata and insufficiency tests

Exit Criteria:

- runtime answers include query, provenance, and response metadata
- trial outputs can be saved and reviewed locally
- evaluation tests cover repeated-run stability and insufficiency reporting

Dependencies:

- Milestone B retrieval payload is stable enough to feed answer composition
- wording boundaries from the i18n strategy are respected in operator-facing
  outputs

Risks:

- collapsing runtime inference and source provenance into one output layer
- producing evaluation artifacts that are hard to compare across runs

Definition of Done:

- local runtime outputs are reviewable artifacts rather than opaque debug logs

### Milestone D: Operational Packaging

Goal:
Make the repository easy to run, validate, and iterate on as a standalone
runtime implementation surface.

Scope:

- add local CLI entrypoints for bundle validation and query execution
- define CI checks for tests and contract fixtures
- document environment configuration and optional provider integration points
- add example workflows for local-only evaluation runs

Detailed Work Packages:

1. CLI surface
   - add commands for bundle validation and query execution
   - define operator-facing argument and exit-code behavior
   - keep locale and provider options explicit
2. CI and automation
   - run tests on every PR
   - add contract-fixture verification to CI
   - optionally gate provider-specific tests behind explicit markers
3. Operator documentation
   - document environment variables and optional provider setup
   - add end-to-end local run examples
   - document expected outputs and failure modes
4. Packaging and reproducibility
   - make a fresh checkout installable and runnable from documented steps
   - ensure deterministic local validation paths remain available without a
     hosted provider

Deliverables:

- public local CLI commands
- CI workflow covering tests and contract checks
- operator runbook for validation and query execution
- reproducible setup instructions from clean checkout

Exit Criteria:

- a new checkout can validate a bundle and run a query from documented commands
- CI verifies the main contract and test path
- local operator setup is documented end to end

Dependencies:

- Milestones A-C have stabilized the contracts those commands expose

Risks:

- exposing a CLI before contract and wording boundaries are stable
- making provider-backed flows the only realistic way to validate the repo

Definition of Done:

- an operator can clone the repo, install it, validate a bundle, and run at
  least one local query path without tribal knowledge

## Recommended Execution Order

1. Finish Milestone A before taking any provider-specific runtime dependency.
2. Use Milestone B to stabilize retrieval semantics and provenance.
3. Build Milestone C only after retrieval outputs are trustworthy enough to
   compare across runs.
4. Use Milestone D to package the validated behavior without changing the
   Chronicle boundary.

## Near-Term Focus

The next safe slice is:

1. capture one or more real Chronicle bundle fixtures
2. add explicit contract-version validation
3. define the retrieval provenance payload that Milestones B and C will share

## Suggested Issue Breakdown

Recommended first issue set:

1. `Milestone A`: add sanitized real-bundle fixtures and fixture-loading tests
2. `Milestone A`: implement handoff/graph/manifest version validation
3. `Milestone A`: define import-validation error taxonomy
4. `Milestone B`: define retrieval provenance payload contract
5. `Milestone B`: harden graph retrieval scoring and ordering behavior
