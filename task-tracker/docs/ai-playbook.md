# Personal AI Coding Playbook

## When I reach for AI first
- The due-date/overdue design: AI got the Pydantic ISO parsing and the read-only computed-field call right (`docs/midcourse/reflection.md:6`).
- Docker and CI. I don't do these often enough to have my own instincts, so I lean on AI more here than anywhere else in this project.
- Listing edge cases before I write tests: blank titles, trailing Z, naive vs. tz-aware dates.

## When I do not reach for AI first
- Business rules: the VALID_TRANSITIONS allow-list is my decision, not a derivable fact.
- Architecture trade-offs that go in the ADR — in-memory vs. JSON vs. database, and the three feature suggestions (stored overdue flag, ORM/database layer, threaded comments) I turned down as out of scope (`docs/midcourse/mini-adr.md:30-45`).
- Grading AI's own review comments. When I ran the code review on this project, I graded every finding myself — Useful, Noise, Wrong. That judgment doesn't get outsourced back to the thing being judged.

## My non-negotiables
- .env never goes in a prompt; `.env.example` only.
- `backend/app/` only touched with explicit approval and a shown diff first, per `AGENTS.md:21` — that's how the null-status bug fix actually went: two options shown, I picked one, then it was applied.
- Every repo claim cites a file, or it's marked not confirmed (`AGENTS.md:24`, `:100`). I hold AI to this as hard as I'd hold myself.
- I don't commit code I can't explain line by line.

## My review rules
- Docs vs. code: the app description still claims JSON-file storage; `storage.py` is dicts.
- Anything suspicious gets rejected outright, not edited around.
- A claim about another file doesn't count until I've read that file myself. An AI review comment once cited "the README documents cascade delete" — the README actually said the opposite (`README.md:184`); the stale claim was really in `docs/midcourse/mini-adr.md:26`.
- Contract behavior: unset vs. None, blank-after-strip, 404 vs. 422 — and what the diff touched that I didn't ask for.

## What I am still figuring out
- I always doubt whether the answer is correct, even after a citation or a passing test.
- Whether AI-written tests are real coverage or just restate the implementation.
- When a known gap (orphaned comments on delete) should be fixed vs. documented.

## Decision Card
- **New feature:** scope comes from the user story, not from what AI offers to add.
- **Code review:** AI finds it, I verify it against the running app or the actual file before it counts.
- **Debugging:** list edge cases first, then test. If AI can't isolate a specific failing input, I trace it myself (`docs/midcourse/reflection.md:9`).
- **Infrastructure:** still thin — I don't have a settled rule here yet beyond "I reach for AI first." Needs more of my own experience before I can write a real rule.
- **Never-paste:** .env, secrets, credentials — no exceptions.
- **One rule:** I don't commit code I can't explain line by line.

I will re-read this playbook on 2026-09-11.
