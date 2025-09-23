# Testing Strategy

- Unit tests cover wavelength conversions, air↔vacuum provenance, resolution kernel accuracy,
  differential suppression, ASCII dedupe, export manifest replay, line scaling, and resolver fixture.
- Hypothesis reserved for future property tests (framework installed via optional deps).
- CI executes ruff, black, mypy, pytest, and custom verifiers via GitHub workflow.
- Tooling: `tools/verifiers` ensure atlas, brains, patch notes, handoff compliance and UI contract.
