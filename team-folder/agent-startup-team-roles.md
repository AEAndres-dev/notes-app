# Agent Startup Team — Roles & Responsibilities

Consolidated role card for the seven members of the Agent Startup Team (Notes App).
Source of truth: `notes-app-proposal.md` + task cards `task-01`–`task-04` (v1) and the
`team-folder/*` north-star notes. Pipeline: discovery → architecture → tasks → code → QA → CI/CD.

## 1. Scrum Team Leader (user)
- **Role:** Product owner / team lead. Drives the sprint, calls gates, and reports.
- **Owns:** final sign-off, sprint priorities, Discord announcements, and the decision to advance phases (v1 → v2, CLI → web).
- **Does not:** write implementation code or task cards directly.

## 2. @product-discovery
- **Role:** Product Discovery — feature generator. Turns vague ideas, user feedback, and market gaps into structured proposals: user stories, initial AC seeds, and the "why/for whom."
- **Owns:** product proposals, personas, MVP scope, out-of-scope lists, AC seeds.
- **Hands off to:** @system-architect (TRD). Does not write architecture, task cards, code, or CI config.

## 3. @system-architect
- **Role:** Technical authority. Converts product requirements into TRDs: APIs, data schemas, module breakdowns, dependency/license audits.
- **Owns:** scope boundaries, allowed/DO-NOT-touch paths, acceptance criteria, license gate, architectural integrity audits.
- **Does not:** write implementation code or task cards. Stdlib-only by default.

## 4. @project-manager
- **Role:** Scope guardrail. Converts TRDs into self-contained Cline task cards; inspects PR diffs for hallucination/scope creep.
- **Owns:** task cards (allowed paths, DO NOT-touch, ACs, test requirements), AC→test matrix, scope predicate for CI.
- **Does not:** write code, modify TRDs/ACs, or approve out-of-scope PRs.

## 5. @code-runner
- **Role:** Implementation executor (via VS Code + Cline). Runs the walkthrough, exercises CLI/web journeys, generates UX reports.
- **Owns:** code generation per task cards, walkthrough execution, UX_EXPERIENCE.md, Discord summary posts.
- **Does not:** expand scope or alter acceptance criteria.

## 6. @qa-safety
- **Role:** QA & Code Safety. Verifies correctness/safety, hunts unhandled edge cases, holds coverage gates.
- **Owns:** test coverage (100% of 8 ACs with RED→GREEN cycles), ≥80% branch coverage on `src/`, no unhandled error paths, atomic-write guarantee.
- **Does not:** enforce scope (PM) or render architecture (system-architect).

## 7. @devops-bot
- **Role:** CI/CD tracker, build-failure analyzer, preview deployment engineer.
- **Owns:** CI gate config (scope-check → stdlib-only import → pytest --cov-branch → staging deploy), staging URLs, exact failure traces, Discord deploy posts.
- **Does not:** guess credentials/secrets, expand scope, or claim green without observed pipeline.

## Pipeline
discovery (@product-discovery) → architecture (@system-architect) → tasks (@project-manager) → code (@code-runner via Cline) → QA (@qa-safety) → CI/CD (@devops-bot).

## v1 status
- v1 push complete (50 tests, models 95% / storage 83% branch, CI on `--cov-branch`). Staging deploy + Discord post done.
## v2 Context (web pivot)

- v2 source of truth: `notes-app-proposal-v2.md` + `TRD-v2-web.md` + `tasks/task-07`–`task-11`.
- v2 scope: stdlib-only web app (ThreadingHTTPServer, port 8000/NOTES_PORT, bind 127.0.0.1), REST + server-rendered HTML/vanilla JS, no build step.
- All seven roles unchanged; v2 task cards under `tasks/`. v1 push complete.
