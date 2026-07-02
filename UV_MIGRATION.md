# UV Migration Plan (engineering-tools)

Purpose: record a practical, low-risk path to migrate the engineering-tools project from Poetry to uv, then remove temporary uv bootstrap logic in this repository once a uv-capable image is published.

## Scope

This document covers:
- Migration work inside .engineering-tools.
- Publishing a new engineering-tools container image that has uv available.
- Follow-up cleanup in this repository to remove CI bootstrap guards that install uv at runtime.

This document does not cover:
- Converting every historical template or external include that still mentions Poetry.
- Broad refactors unrelated to dependency and CI tooling migration.

## Current State Snapshot

- Root repository has already migrated to uv in pyproject.toml and local workflows.
- Root CI currently uses uv sync in several jobs.
- To avoid failures on images without uv, CI includes temporary guard commands:
  - command -v uv >/dev/null 2>&1 || python3 -m pip install uv
- .engineering-tools Dockerfile still uses Poetry and does not explicitly install uv.

## Desired End State

- .engineering-tools project is uv-native for install/sync workflows.
- .engineering-tools Docker image installs and uses uv during image build.
- Root CI runs uv commands without runtime bootstrap guards.
- Pipelines remain stable across merge requests, default branch, and tag flows.

## Migration Strategy

### Phase 1: Inventory and Design (engineering-tools)

1. Identify Poetry entry points in .engineering-tools:
   - Dockerfile
   - Makefile
   - .gitlab-ci.yml and local includes
   - scripts relying on poetry run, poetry env, or poetry export
2. Decide target uv model:
   - PEP 621 metadata in pyproject.toml
   - dependency-groups for docs/dev/test or existing optional sets
   - lockfile managed with uv lock
3. Preserve behavior parity:
   - same dependency sets in CI jobs
   - same command entry points for users where possible
   - minimal command surface changes

Deliverable:
- A short mapping table in this file from old Poetry command to new uv command before any large edits.

### Phase 2: engineering-tools Packaging Migration

1. Update .engineering-tools pyproject.toml to uv-compatible structure.
2. Generate uv.lock in .engineering-tools.
3. Remove reliance on poetry.lock in operational paths.
4. Keep compatibility notes for any private index or source mappings.

Acceptance checks:
- uv lock succeeds.
- uv sync succeeds for default use and docs/test groups where relevant.
- Existing lint/test/doc commands still execute.

### Phase 3: engineering-tools CI and Docker Migration

1. Update .engineering-tools Dockerfile:
   - Install uv explicitly.
   - Replace Poetry install step with uv sync command(s).
2. Update .engineering-tools CI definitions to uv commands.
3. Build and publish a new image tag.

Acceptance checks:
- Docker build succeeds.
- Image contains uv and expected Python tooling.
- engineering-tools pipeline green on MR and default branch.

### Phase 4: Consume New Image in Root Repo

1. Bump DEPLOY_IMAGE in root .gitlab-ci.yml to the new engineering-tools image tag.
2. Validate root pipeline jobs that use uv sync.
3. Remove temporary uv bootstrap guards from root CI files:
   - .gitlab/ci/.ansible.yml
   - .gitlab/ci/.jobs.yaml
   - .gitlab/ci/za-itf/ci-ska-mid-itf-commit-ref/.pipeline.yaml
   - .gitlab/ci/za-itf/ci-ska-mid-sut-skaXXX-commit-ref/.pipeline.yaml
   - .gitlab/ci/za-itf/dish-lmc-skaXXX/.pipeline.yaml

Acceptance checks:
- No command -v uv bootstrap lines remain in root CI.
- Pipelines remain green with the new image.

## Command Mapping Draft

- poetry install -> uv sync
- poetry install --only <group> -> uv sync --group <group>
- poetry install --with <group> --no-root -> uv sync --group <group>
- poetry run <cmd> -> uv run <cmd>
- poetry export -> prefer uv-native install/sync flow; only generate requirements if a consumer strictly needs it

Note: verify exact group semantics and lock behavior in .engineering-tools before applying in bulk.

## Risks and Mitigations

Risk: CI image mismatch, uv missing at runtime.
Mitigation: keep bootstrap guards until new image is published and adopted.

Risk: dependency resolution differences between Poetry and uv.
Mitigation: migrate incrementally, lock early, and validate each dependency group separately.

Risk: private index/source resolution regressions.
Mitigation: explicitly configure uv sources and test in clean CI environment.

Risk: behavior drift in scripts expecting Poetry virtualenv layout.
Mitigation: search and patch scripts; prefer uv run and stable executable paths.

## Rollback Plan

If failures occur after engineering-tools migration:
1. Revert engineering-tools branch changes.
2. Re-publish previous known-good image tag or pin back to it.
3. Keep root CI bootstrap guard lines in place until stable uv image exists.

If failures occur after root cleanup:
1. Restore bootstrap lines in root CI quickly.
2. Re-run failed jobs to confirm uv availability issue.
3. Retry cleanup after image verification.

## Tracking Checklist

- [ ] Phase 1 inventory complete in .engineering-tools
- [ ] Command mapping validated against real jobs/scripts
- [ ] .engineering-tools pyproject migrated
- [ ] .engineering-tools uv.lock committed
- [ ] .engineering-tools CI migrated to uv
- [ ] .engineering-tools Dockerfile migrated and image published
- [ ] Root DEPLOY_IMAGE bumped
- [ ] Root uv bootstrap guards removed
- [ ] Root pipelines validated on MR and default branch

## Notes To Future Self

Keep changes small and reversible.
Do not remove runtime uv bootstrap guards until the new image is proven in CI.
Prefer CI parity over local convenience: if CI requires a specific group, encode it explicitly.
