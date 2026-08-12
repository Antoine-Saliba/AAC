# Personal AI Coding Playbook

## 1. When I reach for AI first

- Patterns already in the repo: extending the comment endpoints from the task endpoints in main.py.
- Docstrings and README prose for code I already understand. [needs course evidence: ___]
- Listing edge cases before I write tests: blank titles, trailing Z, naive vs. tz-aware dates.

## 2. When I do not reach for AI

- Business rules: the VALID_TRANSITIONS allow-list is my decision, not a derivable fact.
- Architecture trade-offs that get written up in the ADR — in-memory vs. JSON vs. database.
- Anything touching secrets: .env never goes in a prompt; .env.example only.

## 3. My non-negotiables

- One bounded task per session, read-only by default, backend/app/ only with explicit approval. [needs course evidence: ___]
- Every repo claim cites a file, or it's marked not confirmed. [needs course evidence: ___]
- I don't commit code I can't explain line by line. [needs course evidence: ___]

## 4. My review rules

- Docs vs. code: the app description still claims JSON-file storage; storage.py is dicts.
- Imports and dead code: models.py has a _reset() referencing names that live in storage.py; routes.py is never imported.
- Contract behavior: unset vs. None, blank-after-strip, 404 vs. 422 — and what the diff touched that I didn't ask for.

## 5. What I am still figuring out

- How much context to paste — one function, whole file, or AGENTS.md every time.
- Whether AI-written tests are real coverage or just restate the implementation.
- When a known gap (orphaned comments on delete) should be fixed vs. documented.

I will re-read this playbook on September 11, 2026.

AI-Assisted Coding - Module 5 Prompt Library - For a new feature I reach for: existing repo patterns, such as task endpoints in main.py - For a code review I reach for: docs-versus-code, dead-code, and contract checks - For debugging I reach for: edge-case listing before tests - For infrastructure I reach for: an ADR for the trade-off - I will never paste secrets from .env into an AI tool. - My one rule is: I don't commit code I can't explain line by line.
