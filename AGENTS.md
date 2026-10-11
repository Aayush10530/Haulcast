# AGENTS.md

Weather-aware truck routing app (React + Django).

Before any task, read in this order: `docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`, `docs/CODING_RULES.md`, `docs/FEATURE_LOG.md`. For frontend tasks, also read `docs/DESIGN.md`. The full master prompt is `docs/PROMPT.md` Part A.

Non-negotiable:
- Follow the current architecture. Do not change folder structure without approval.
- Frontend, API layer, services, domain, providers and infra stay separated. No business logic in UI.
- Third-party APIs sit behind provider interfaces. Domain code is pure.
- Reuse existing utilities and components. No duplicate logic. One coding style.
- Modules, not whole systems. Do only the task given. Nothing outside docs/FEATURE_LOG.md.
- Tests with the code. Show real lint, type-check and test output.
- Commit after every stable feature (Conventional Commits). Never commit secrets or `.env`.
- Update docs/FEATURE_LOG.md after every task. Update docs/PROJECT_CONTEXT.md and docs/ARCHITECTURE.md after major changes.
- If the spec or docs are ambiguous, or you want a new dependency or structure change: stop and ask.
