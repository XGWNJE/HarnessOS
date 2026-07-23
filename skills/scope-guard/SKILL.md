---
version: 1.0.0
name: scope-guard
description: Use when SCOPE_GUARD_PENDING appears, or whenever an Agent action has a semantic failure involving a violated assumption, wrong target, wrong path, or wrong scope.
---

# Scope Guard

## Capture mode

Use this mode for every recognized semantic Agent failure in the current task. The store decides when the same root reaches two occurrences, counting the main Agent and all subagents together.

1. Do not interrupt, pause, warn, or reroute the current user conversation because of Scope Guard.
2. Build a short root-cause key and a redacted factual summary. Do not include prompts, full tool output, credentials, tokens, cookies, or secret URLs.
3. Read `SCOPE_GUARD_SESSION_ID` and optional `SCOPE_GUARD_AGENT_ID` from developer context.
4. Run the installed `record-semantic` command once for this occurrence. Use the same root-cause key for later same-root occurrences; each occurrence must be recorded, while the store triggers only when the count reaches two.
5. Continue the user's task normally.

## Review mode

Use this mode when `SCOPE_GUARD_PENDING` appears in developer context.

Read `SCOPE_GUARD_IN_MAINTENANCE_PROJECT` and `SCOPE_GUARD_MAINTENANCE_ROOT` before doing any analysis.

### Outside the maintenance project

When `SCOPE_GUARD_IN_MAINTENANCE_PROJECT=false`:

1. Tell the user which prior repeated failure triggered Scope Guard and show the maintenance root.
2. Explain that this task can continue the original task normally.
3. Do not perform defense analysis, do not run `classify`, and do not modify the current or source project for Scope Guard maintenance.
4. Leave the presented incident in the centralized maintenance queue for later recovery.

### Inside the maintenance project

When `SCOPE_GUARD_IN_MAINTENANCE_PROJECT=true`:

1. Run `maintenance-list` to recover every presented incident awaiting maintenance.
2. Perform read-only fact checks for source project, cwd, repo, branch, target, evidence, Agent actions, and whether the failures really share one root cause.
3. Keep source projects read-only until the user confirms an exact source-project write.
4. Classify the durable defense as `project`, `global`, or `uncertain`, then run `classify` for the incident.
5. Choose the smallest effective defense and state evidence, confidence, missing evidence, and recommendation.
6. Do not permanently modify any project or global rule until the user confirms.
7. After the confirmed defense is implemented and verified, run `resolve`. If evidence proves the incident is a false positive or the user decides not to maintain it, run `dismiss`.

If the maintenance configuration is unavailable, show the stable configuration error and do not fall back to maintenance in the current project.

## Installed command

Use PowerShell with the exact installed wrapper and state directory:

`py -3 "C:\Users\Administrator\.codex\scope-guard\app\scope_guard_hook.py" --state-dir "C:\Users\Administrator\.codex\scope-guard\data" <command>`
