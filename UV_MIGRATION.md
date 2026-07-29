# UV + Ruff Migration Status (ska-mid)

Purpose: record the current migration state and only the remaining future work.

Reference:
- https://developer.skao.int/en/latest/howto/poetry-to-uv-ruff-migration.html#one-shot-ai-migration-prompt

## Current State

### Root Repository

- uv lock/sync workflow is active.
- CI Python template include uses `python-uv`.
- `DEPLOY_IMAGE` points to a uv-capable engineering-tools dev image.
- uv bootstrap guards have been removed from root CI jobs.
- k8s test/publish sync profile has been leanified to:
  - `uv sync --frozen --no-default-groups`
- deploy-oriented sync profile remains:
  - `uv sync --frozen --no-default-groups --group engineering-tools`

### engineering-tools Dependency

- engineering-tools migration work is available and consumed via dev image.
- Stable non-dev release adoption is still pending.

## Remaining Future Work

1. Remove residual Poetry references in in-scope root scripts/docs.
2. Consolidate root lint stack to Ruff-only active path.
3. Validate MR/default/tag pipelines after the guard-removal and sync-profile updates.
4. Adopt a stable non-dev uv-capable engineering-tools image tag and keep `DEPLOY_IMAGE` pinned to it.
5. Optional CI performance follow-up:
   - add uv cache persistence in root CI jobs
   - evaluate a dedicated minimal CI dependency group only if timing data justifies it

## Tracking Checklist

- [x] Root pyproject metadata uv-compatible
- [x] Root uv lock/sync workflow active
- [x] Root CI include switched to python-uv template
- [x] New engineering-tools uv-capable image published
- [x] Root DEPLOY_IMAGE bumped to new engineering-tools image
- [x] Root uv bootstrap guards removed
- [ ] Root residual Poetry references removed in all in-scope scripts/docs
- [ ] Root lint stack fully consolidated to Ruff-only active path
- [ ] Full MR/default/tag pipeline validation completed
- [ ] Stable engineering-tools release tag adopted (non-dev)

## Risks and Mitigations

Risk: jobs fail if a runner resolves an older image without uv.
Mitigation: keep a small rollback commit ready to restore guard lines and verify image tags per pipeline.

Risk: mixed lint behavior while legacy lint dependencies remain.
Mitigation: remove legacy lint dependencies/config only after Ruff path is fully validated in CI.

Risk: performance gains do not materialize after sync-scope changes.
Mitigation: add uv cache first, then re-measure before introducing further dependency-group splits.

## Deferred Scope

- images/ska-mid-eda-grafana-connector/Dockerfile
  - External cloned project still has its own migration lifecycle.
- .make/.gitlab-ci.yml and shared .make internals
  - Shared template infrastructure managed upstream.
- .engineering-tools/.gitlab/ci/check-dependencies/.pipeline.yaml and related submodule CI files
  - Owned by engineering-tools project workflow.
