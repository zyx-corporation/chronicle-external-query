# Runtime Boundary

Chronicle Stack remains the record layer. This repository is responsible for
external query execution concerns that should stay outside Chronicle core.

## In Scope

- bundle ingest
- graph/vector retrieval
- ranking and answer synthesis
- runtime-specific dependencies and serving concerns

## Out of Scope

- changing Chronicle primary records directly
- embedding a hosted query engine back into Chronicle Stack
- treating Chronicle-derived exports as authoritative source records
