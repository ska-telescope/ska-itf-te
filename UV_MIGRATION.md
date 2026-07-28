# UV + Ruff Migration Plan (ska-mid and engineering-tools)

Purpose: align this repository with the SKAO one-shot Poetry -> uv(+ruff) migration guidance, complete remaining root-repo actions now, and track what is still blocked on the engineering-tools submodule/image lifecycle.

Reference:
- https://developer.skao.int/en/latest/howto/poetry-to-uv-ruff-migration.html#one-shot-ai-migration-prompt

## Scope

This document covers:
- Root repository migration status and remaining work.
- engineering-tools migration follow-up required in the submodule/upstream project.
- CI template and pipeline alignment to python-uv.

This document does not cover:
- Updating upstream shared template internals in .make.
- Migrating external projects pulled during image builds.

## Decision: Ruff Migration

This repository is migrating with Ruff enabled as the target lint/format toolchain, in line with the one-shot prompt. Legacy tools may remain temporarily as compatibility dependencies until all lint paths are fully consolidated.

## One-Shot Migration Contract and Status

### 0) Confirm linting strategy (Ruff vs legacy)

Target from SKAO guidance:
- Decide whether to migrate to Ruff.
- If not migrating to Ruff, keep legacy lint via python-uv.mk overrides.

Status:
- Done (Ruff path selected).
- Root pyproject includes Ruff in dev dependencies.

### 1) Convert pyproject metadata to standards

Target from SKAO guidance:
- Use [project], [dependency-groups], [build-system], [[tool.uv.index]].
- Set requires-python explicitly.

Status:
- Done in root repository.
- Root pyproject is already uv-compatible.

### 2) Replace lock/dependency flow

Target from SKAO guidance:
- Use uv.lock and uv sync flows.
- Remove poetry.lock when full migration is complete.

Status:
- Done in root repository.
- uv.lock flow is active.
- engineering-tools submodule still requires its own dedicated lock/flow migration upstream.

### 3) Replace command execution paths

Target from SKAO guidance:
- Replace poetry run with uv run across scripts, make targets, docs, CI.

Status:
- Mostly done in root paths.
- Remaining Poetry references exist in deferred/out-of-scope areas (see Deferred References).

### 4) Migrate lint/format to Ruff

Target from SKAO guidance:
- Use ruff format and ruff check as active path.
- Keep config in pyproject.

Status:
- Partially done.
- Ruff is present, but legacy lint tool configuration/dependencies still exist and should be cleaned after CI parity confirmation.

### 5) Keep formatting churn isolated

Target from SKAO guidance:
- Keep mechanical formatting changes separate from functional migration changes.

Status:
- Ongoing practice.

### 6) Update CI/CD templates and jobs to uv-aware paths

Target from SKAO guidance:
- Switch Python include to python-uv template.
- Remove Poetry-era leftovers once safe.

Status:
- Done now for root pipeline template include.
- Root .gitlab-ci.yml now uses:
  - gitlab-ci/includes/python-uv.gitlab-ci.yml
- Done in local engineering-tools working tree; upstream publication still pending.

### 7) Update Docker build/install path to uv

Target from SKAO guidance:
- Use uv sync in Docker build dependency layers.

Status:
- Partially done.
- Root repository still depends on engineering-tools image capability for uv-first behavior.
- engineering-tools Dockerfile migration is still required upstream.

### 8) Update docs and contributor paths

Target from SKAO guidance:
- README and helper docs should teach uv/ruff as the single path.

Status:
- Partially done.
- Some docs/scripts still mention Poetry and need targeted cleanup.

### 9) Validate end-to-end under uv + ruff

Target from SKAO guidance:
- Validate sync, lint, tests, build and fix discovered issues.

Status:
- Partially done.
- Root local workflows are uv-based; full pipeline validation remains tied to engineering-tools image/template updates.

### 10) Final quality gate

Target from SKAO guidance:
- Confirm Poetry is no longer the active path in code, CI, Docker, and docs.

Status:
- Not yet complete globally due engineering-tools and deferred references.

## High-Value Delta Applied in This Change

- Root pipeline Python template include updated from python-lint to python-uv in .gitlab-ci.yml.

Why this matters:
- Aligns pipeline machinery with the uv-native template path prescribed by SKAO migration guidance.
- Removes a key migration gap previously identified in this repository.

## Command Mapping (Validated Target)

- poetry install -> uv sync
- poetry install --with dev -> uv sync --all-groups
- poetry install --only <group> -> uv sync --group <group>
- poetry run <cmd> -> uv run <cmd>
- poetry export -> avoid by default; generate requirements only when a consumer requires it

## Remaining Work Plan

### A) Root repository (can proceed here)

1. Audit and remove residual Poetry command usage in root scripts/docs where in scope.
2. Rationalize lint stack:
   - promote Ruff commands as the single active lint/format path
   - remove legacy lint deps/config once no jobs rely on them
3. Keep uv bootstrap guards only until new engineering-tools image is confirmed uv-capable in all used jobs.
4. After image switch and green pipelines, remove bootstrap guards from:
   - .gitlab/ci/.ansible.yml
   - .gitlab/ci/.jobs.yaml
   - .gitlab/ci/za-itf/ci-ska-mid-itf-commit-ref/.pipeline.yaml
   - .gitlab/ci/za-itf/ci-ska-mid-sut-skaXXX-commit-ref/.pipeline.yaml
   - .gitlab/ci/za-itf/dish-lmc-skaXXX/.pipeline.yaml

### B) engineering-tools upstream/submodule (blocked here, must be done in submodule project)

1. Switch .engineering-tools/.gitlab-ci.yml include:
   - gitlab-ci/includes/python.gitlab-ci.yml -> gitlab-ci/includes/python-uv.gitlab-ci.yml
2. Update .engineering-tools Dockerfile to install/use uv for dependency sync.
3. Replace Poetry command usage in .engineering-tools CI and helper pipelines.
4. Publish new engineering-tools image tag with uv available by default.
5. Bump root DEPLOY_IMAGE to that new tag and then remove temporary uv bootstrap guards.

## Risks and Mitigations

Risk: jobs fail if uv missing in older deploy image.
Mitigation: keep temporary bootstrap guard lines until image migration is published and adopted.

Risk: mixed linting behavior while legacy dependencies remain.
Mitigation: keep Ruff as active path in CI templates, then remove legacy tools in one focused cleanup change.

Risk: submodule/root drift during staggered migration.
Mitigation: track explicit handoff items above and gate bootstrap-removal on image verification.

## Deferred References (Intentional)

- images/ska-mid-eda-grafana-connector/Dockerfile
Reason: builds an external cloned project that is still Poetry-based; out of root migration scope.

- .make/.gitlab-ci.yml and shared .make internals
Reason: shared template infrastructure; must be changed upstream, not in this repository.

- .engineering-tools/.gitlab/ci/check-dependencies/.pipeline.yaml and related submodule CI files
Reason: owned by engineering-tools project; migrate in upstream submodule workflow.

## Rollback Plan

If root pipeline CI include change causes regressions:
1. Revert root .gitlab-ci.yml include back to previous template include.
2. Re-run lint/test pipeline jobs.
3. Re-apply after validating required template job compatibility.

If failures occur after future bootstrap-guard removal:
1. Restore guard lines quickly in affected root CI files.
2. Confirm deploy image uv availability.
3. Retry cleanup only after image validation.

## Tracking Checklist

- [x] Root pyproject metadata uv-compatible
- [x] Root uv lock/sync workflow active
- [x] Root CI include switched to python-uv template
- [ ] Root residual Poetry references removed in all in-scope scripts/docs
- [ ] Root lint stack fully consolidated to Ruff-only active path
- [ ] engineering-tools pyproject/lock/CI/Docker migrated upstream
- [ ] New engineering-tools uv-capable image published
- [ ] Root DEPLOY_IMAGE bumped to new engineering-tools image
- [ ] Root uv bootstrap guards removed
- [ ] Full MR/default/tag pipeline validation completed

## Notes To Future Self

Keep changes small and reversible.
Do not remove runtime uv bootstrap guards until the uv-capable engineering-tools image is proven in CI.
Prioritize CI parity over local convenience.

## MR-Ready Summary (2026-07-28)

### Changes Applied in This Workspace

Root repository:
- .gitlab-ci.yml
   - Switched Python CI template include from python-lint to python-uv.
- resources/ansible-playbooks/testing/test.sh
   - Replaced poetry run ansible-playbook with uv run ansible-playbook.
- resources/ansible-playbooks/README.md
   - Reviewed for Poetry references; no Poetry references found.

engineering-tools submodule working tree:
- .engineering-tools/.gitlab-ci.yml
   - Switched Python CI template include from python to python-uv.

### Deferred / Follow-Up Items

- Keep uv bootstrap guards in root CI until a uv-capable engineering-tools image is published and confirmed in MR/default pipelines.
- Complete engineering-tools upstream migration items (Docker dependency path, remaining Poetry command usage in submodule-owned CI/jobs).
- Consolidate root lint path to Ruff-only once all jobs/scripts are confirmed not to depend on legacy lint tooling.
- TODO: Upstream .make/python-uv.mk should honor PYTHON_LINE_LENGTH in python-do-format and python-do-lint so local Makefile overrides can be dropped.

### Quality Gate Snapshot

Build: NOT RUN in this change set.
Lint/Typecheck: NOT RUN in this change set.
Tests: NOT RUN in this change set.

Poetry Active Path Status:
- Root CI template path: switched to python-uv.
- Root ansible playbook test helper: switched to uv run.
- Global repository status: Poetry is not yet fully eliminated due deferred and out-of-scope areas listed above.
