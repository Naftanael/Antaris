# AGENTS.md

## Project overview

Jarvis is a frontend-generation and developer-interface platform built with Next.js, TypeScript, Tailwind CSS, and a strict design system.

## Repository expectations

- Prefer small, verifiable changes.
- Never introduce UI components outside the registry without explicit approval.
- Validate all page schemas with Zod before using them.
- Run lint, typecheck, unit tests, and visual tests before finalizing changes.

## Frontend rules

- Use App Router conventions.
- Reuse recipes before creating new layouts.
- Support loading, empty, and error states in all data-driven pages.
- Preserve keyboard accessibility and visible focus states.
- Avoid inline styles unless unavoidable.

## Design system rules

- Use only registered components and allowed variants.
- Do not create ad hoc visual patterns.
- Keep visual hierarchy clear and spacing consistent.
- Use semantic colors only for state communication.

## Validation rules

Before considering work done:
- run lint
- run typecheck
- run component tests
- run Playwright visual checks
- run accessibility checks

## Definition of done

A page is done only if:
- schema is valid
- code compiles
- tests pass
- no major a11y issue exists
- no horizontal overflow exists
- layout is consistent across supported breakpoints
