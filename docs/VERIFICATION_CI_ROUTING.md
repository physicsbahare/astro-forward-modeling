# Verification CI routing, 2026-09-03

The empirical-transfer commit `88f3fb6` launched the selected experiment plus
many historical gate workflows. This was not a new request to repeat all
those experiments. Inspection of their triggers identifies cumulative
pull-request path matching: GitHub uses a three-dot PR diff, so old files
added anywhere in long-lived draft PR #5 keep matching on every update.
Two Gate-B workflows also had unconditional branch-push triggers.

The documented built-in controls are sufficient; no new scheduler, action
dependency, token permission or cancellation service is needed:

- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#git-diff-comparisons
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions

The routing-only repair preserves every test command, package pin, parameter,
bound, acceptance check, artifact instruction and historical result.

1. Existing PR workflows skip jobs on **draft PR #5 only**. Other PRs and
   non-draft #5 retain their original execution. The original PR event types
   are retained and `ready_for_review` is added, so leaving draft triggers a
   real review-time replay. This task must not change PR #5 out of draft.
2. The full ordinary verification suite still runs on **every branch push**,
   including the C5e commit. Only its duplicate draft-PR copy is skipped.
3. Gate-B core and STPSF pushes use explicit crosscode/verification/dependency/
   workflow paths. Their scientific job bodies are unchanged. Existing
   path-filtered pushes and manual dispatch remain available elsewhere.
4. To install the routing repair without that repair itself replaying every
   modified historical workflow, there is a **one-parent bootstrap guard**:
   a push to `verification-v0.1` whose `before` SHA is exactly
   `88f3fb646a0b89e6cb9b8b8ee1aacae377edca56` and whose message contains
   `[C5e isolated]` skips the legacy jobs. The NEW C5e workflow and the full
   verification-suite push have no such guard. This is not GitHub's global
   `[skip ci]` mechanism. It cannot suppress subsequent-parent push runs.

The bootstrap commit contains only the new frozen C5e implementation/tests/
requirements, review records, and routing-only workflow changes. No existing
science implementation, shared dependency file, bounds or test command is
modified. Before pushing, compare every historical workflow with the parent
and verify only routing keys changed. Do not reuse this marker for changes
to historical science or shared numerical dependencies.

Skipped jobs are **not** evidence of a new experiment succeeding, even if
GitHub's aggregate check presentation says success. Always inspect the
selected workflow's actual jobs/steps/artifacts before advancing science.
Already-running historical jobs are left intact, not cancelled. Their earlier
verified runs remain the scientific provenance. If an existing PR-only
benchmark later needs a repair, dispatch it explicitly or add a narrow push
trigger for that affected benchmark; do not depend on draft-PR replay.

The mechanical before/after audit is recorded in
`benchmarks/zhuang_shen_2024/ci_routing_20260903.json`.
