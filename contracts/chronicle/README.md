# Chronicle Contracts

Place Chronicle-side schemas or copied contract references here when they become
stable enough to vendor into this repository.

Current reference material:

- [Query-Engine Bundle Contract Notes](query-engine-bundle-contract-notes.md)
- [Query-Engine Bundle Contract Source Map](query-engine-bundle-contract-source-map.md)

The loader now validates against observed real bundle structure and versioned
contract notes rather than file presence alone.

Vendored files in this directory stay intentionally small. When a fuller payload
or implementation detail is needed, the source map points back to the relevant
Chronicle Stack doc or source file.
