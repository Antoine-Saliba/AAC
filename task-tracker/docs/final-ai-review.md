# Final AI Review

Branch: final-project

## AGENTS.md guardrails

Checked against the real `task-tracker/AGENTS.md`.

1. **Read-first / cite-before-claiming guardrail present?** Yes — `AGENTS.md:24`: "Before making a repository claim, inspect and cite the relevant file(s). If a fact is not visible, write **not confirmed** rather than inferring it." Reinforced at `AGENTS.md:100`: "Use read-only inspection before proposing changes. Cite the file(s) inspected for all repository findings."
2. **`app/`/`frontend/` protected, with exceptions requiring documentation in `docs/final-ai-review.md`?** Yes — `AGENTS.md:21`: "`backend/app/` and `frontend/` are both protected. Do not modify either unless the user explicitly approves one specific minimal fix. Any accepted change to either must be documented in `docs/final-ai-review.md`."
3. **Never-paste rule covers secrets/.env/tokens/production logs/personal data?** Yes — `AGENTS.md:98`: "Never paste, log, commit, or expose secrets, credentials, tokens, local `.env` contents, production logs, or personal data."

## AI code review mini-log

Diff reviewed: `task-tracker/backend/app/main.py`, `master...final-project`. Pass 1 (unscoped) returned six comments, four of which were cosmetic and none of which touched runtime behaviour; the behaviour-scoped second pass (status codes, validation, error paths, request/response contract only) is what surfaced the null-status bug.

| # | AI comment | Grade | Reason | Verification or decision |
|---|---|---|---|---|
| 1 | `main.py:1-4` — module docstring says "CRUD endpoints are intentionally not implemented yet"; this diff adds full CRUD. | Useful | "Docstring says CRUD is not implemented; the same diff implements it. Stale doc contradicting its own file." | Read `main.py:1-4` (docstring) and `main.py:105-281` (task CRUD + comment endpoints added in the same diff). |
| 2 | `main.py:76-80` — new `_require_task()` helper has no docstring, unlike every other function in the file; called from 5 endpoints. | Useful (minor) | "Private helper, but it owns a 404 contract used by five endpoints and every other function in the file is documented." | Read `main.py:76-80` (no docstring); confirmed call sites at lines 120, 164, 224, 249, 274. |
| 3 | `main.py:76,82` — missing blank-line spacing around the new `_require_task` helper vs. the rest of the file. | Noise | "Blank-line counts are a formatter's job, not a reviewer's. `ruff format` settles it with no human decision involved." | Read `main.py:75-82`. |
| 4 | `main.py:163-167` — `update_task` fetches the task twice (once via `_require_task` for validation, once inside `storage.update_task`); framed as a TOCTOU corruption risk. | Useful, severity downgraded | "I confirmed handlers are sync and threadpool-dispatched, so concurrency is possible. I also confirmed storage.update_task writes payload.status and never reads existing.status, so there is no corruption path. Real exposure is a narrow validation-bypass window with no I/O in it and no reproducer in this repo. Accepted the mechanism, rejected the original framing." | Confirmed all route handlers are `def`, not `async def` (FastAPI dispatches sync routes via a thread pool, so concurrent execution is real). Read `storage.py:85-100` (`update_task`), confirming it writes `payload.status` directly and never reads `existing.status`. |
| 5 | `main.py:182-184` — `delete_task`'s new docstring documents that comments are orphaned rather than cascade-deleted, "despite the README documenting cascade delete," without fixing it. | Useful | "Highest-value finding in the set: documented contract violation that also contradicts the README." | Read `main.py:182-184` (docstring claim). Re-read `README.md:184` directly — it already states comments do **not** cascade-delete ("that has not been implemented"), so there is no current contradiction in the README. Traced the stale "cascade" claim instead to `docs/midcourse/mini-adr.md:26` ("Cascade — deleting a task removes its comments, so none are orphaned") and to `main.py`'s own docstring wording. The original premise about the README was wrong; corrected on re-verification, grade and reason left as given. |
| 6 | `main.py:200-203` — four blank lines between `delete_task` and the new `/comments` route block, vs. two elsewhere in the file. | Noise | "Same class as #3, and it is the same finding counted twice." | Read `main.py:199-204`. |
| 7 | `main.py:163` (pre-fix) — `PATCH /tasks/{id}` with `{"status": null}` skips `validate_status_transition` (the `payload.status is not None` guard treats explicit-null the same as omitted) and persists `status: null`. | Useful, and the most serious finding in either pass | "Live reproducer, invalid state persists, validate_status_transition is silently skipped." | Live curl reproducer: created a probe task, `PATCH /tasks/{id}` `{"status": null}` → HTTP 200, body `status:null`; follow-up `GET /tasks/{id}` → `status:null` persisted. Fixed at `main.py:163-168` (see Protected-directory exception below). Regression test added: `tests/test_tasks.py::test_patch_explicit_null_status_returns_422_and_leaves_status_unchanged`. Full suite: 43 passed, 2 warnings in 0.70s. |
| 8 | `main.py:234` — `POST /tasks/{id}/comments`: task-existence 404 is only reached when the body is valid; an invalid body always returns 422 first, even for a nonexistent task. | Noise | "Accurate, but it describes standard FastAPI ordering — body validation always runs before the handler. There's no auth boundary in this app, so task enumeration isn't a threat worth restructuring for." | Live curl: `POST /tasks/00000000.../comments` with `{"text":"hello"}` (nonexistent task, valid body) → 404 "Task ... not found"; same URL with `{"text":""}` (nonexistent task, invalid body) → 422 blank-text validation error. |
| 9 | `main.py:228-233` — `POST /tasks/{id}/comments` returns 201 with no `Location` header; no single-comment `GET` endpoint exists to point one at. | Noise, out of scope | "The finding notes there's no single-comment GET to point a Location header at, so a correct fix means adding an endpoint. That's a new feature and the project rules forbid it." | Live `curl -i` on `POST /tasks/{id}/comments` — confirmed 201 response headers (date, server, content-length, content-type only, no `Location`). Confirmed no `GET /tasks/{task_id}/comments/{comment_id}` route exists anywhere in `main.py` (only `list_comments`, `create_comment`, `delete_comment`). |

## AI security mini-review

Scope: read-only review of `task-tracker/` covering dependency/version risk, input validation, error handling, CORS/auth, secret handling, `Dockerfile`, and `.github/workflows/ci.yml`. No files were edited during the review. Grading below was done by the AI reviewer itself, at the user's explicit direction for this pass (the code-review mini-log above was graded by the user; this table was not).

| # | Finding | Grade | Reason | Next action |
|---|---|---|---|---|
| 1 | `main.py:36-42` — CORS is fully open (`allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`) and no route in the file (lines 82-281) checks any credential or token. | Noise | Technically accurate, but it restates a limitation the project already documents and accepts — README.md §9 and AGENTS.md both explicitly call out "no authentication" and wide-open CORS as known, intended scope for a local learning project. Not new information. | None. Already documented; no doc or code change needed. |
| 2 | `models.py:86,89` (`TaskCreate`) and `:116,119` (`TaskUpdate`) — `description` and `assignee` have no length validator, unlike `title` (200-char cap, `:109-110`) and `Comment.text` (2000-char cap, `:217-218`); no request body size limit exists anywhere in the stack. | Valid | Real, specific, and not previously documented anywhere in the repo — an actual inconsistency (two fields got a length cap, two didn't) with a concrete mechanism (unbounded in-memory storage, `storage.py:16-17`, never evicted). | Add a length validator to `description` and `assignee` mirroring the pattern already used for `title`/`text`. Not applied — `models.py` is protected and this wasn't pre-approved as a fix in this session. |
| 3 | `Dockerfile:4,14` — `FROM python:3.11-slim` is a floating tag, not pinned to a digest. | Noise | Accurate, but digest-pinning trades away automatic base-image security patches for reproducibility, and this project has no production deployment where that tradeoff matters. Standard checklist item, low real stakes here. | None for now. Worth a one-line note in the Dockerfile if this project is ever deployed anywhere non-local. |
| 4 | `.github/workflows/ci.yml:14,16` — `actions/checkout@v4` and `actions/setup-python@v5` are pinned to version tags, not commit SHAs. | Noise | Accurate, but both are first-party GitHub actions (not a random third-party action), which is the case where tag-vs-SHA pinning matters least in practice. | None. |
| 5 | `.github/workflows/ci.yml` (whole file) — no `permissions:` key anywhere, so `GITHUB_TOKEN` gets the repo/org default rather than least-privilege, even though this workflow only checks out code and runs `pytest`. | Valid | Real gap with a free fix — the workflow does nothing today that needs elevated token permissions, so scoping it down costs nothing and closes off a footgun for whoever adds a step later without thinking about it. | Add `permissions:\n  contents: read` at the workflow or job level. Not applied — `.github/workflows/ci.yml` is not app/frontend, but no edit was pre-approved in this review task. |
| 6 | `main.py:22` — `load_dotenv()` loads `.env` unconditionally. | Noise | Self-assessed as likely noise at finding time: `.env` is gitignored, untracked, and currently holds only `APP_ENV`/`PORT` — no secret currently flows through this line. | None currently. Revisit if `.env` ever holds a real credential. |
| 7 | No rate limiting or request throttling anywhere in the stack (`main.py`, `Dockerfile` CMD, no reverse proxy config). | Noise | Self-assessed as likely irrelevant at finding time: explicitly a local, single-user learning app with no deployment/production configuration (README §9). Flagged only because "input validation" and "Docker/CI behaviour" were named review areas. | None. |

## Manual security check

Manual, read-only check of whether `.dockerignore`'s exclusions hold up in the actual built image (separate from the AI security mini-review above). Run by the user, not the AI. Commands as given earlier in this session.

**1. Build the image**
```
$ docker build -t task-tracker-api .
```
```
[+] Building 3.1s (19/19) FINISHED                                                                                                                                                                      docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                                    0.0s
 => => transferring dockerfile: 937B                                                                                                                                                                                    0.0s
 => resolve image config for docker-image://docker.io/docker/dockerfile:1                                                                                                                                               1.3s
 => [auth] docker/dockerfile:pull token for registry-1.docker.io                                                                                                                                                        0.0s
 => CACHED docker-image://docker.io/docker/dockerfile:1@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89                                                                                         0.0s
 => => resolve docker.io/docker/dockerfile:1@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89                                                                                                    0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                                                                                                                                                     0.9s
 => [auth] library/python:pull token for registry-1.docker.io                                                                                                                                                           0.0s
 => [internal] load .dockerignore                                                                                                                                                                                       0.0s
 => => transferring context: 449B                                                                                                                                                                                       0.0s
 => [internal] load build context                                                                                                                                                                                       0.0s
 => => transferring context: 9.33kB                                                                                                                                                                                     0.0s
 => [builder 1/4] FROM docker.io/library/python:3.11-slim@sha256:90744cff8f32887f075c47d747a173ff333e9e98801667af93c357fa9f5e28ff                                                                                       0.0s
 => => resolve docker.io/library/python:3.11-slim@sha256:90744cff8f32887f075c47d747a173ff333e9e98801667af93c357fa9f5e28ff                                                                                               0.0s
 => CACHED [runtime 2/7] RUN useradd --create-home --uid 1000 app                                                                                                                                                       0.0s
 => CACHED [runtime 3/7] WORKDIR /app                                                                                                                                                                                   0.0s
 => CACHED [builder 2/4] WORKDIR /build                                                                                                                                                                                 0.0s
 => CACHED [builder 3/4] COPY backend/requirements.txt .                                                                                                                                                                0.0s
 => CACHED [builder 4/4] RUN pip install --no-cache-dir --no-compile --user -r requirements.txt                                                                                                                         0.0s
 => CACHED [runtime 4/7] COPY --from=builder --chown=app:app /root/.local /home/app/.local                                                                                                                              0.0s
 => [runtime 5/7] COPY --chown=app:app backend/app ./backend/app                                                                                                                                                        0.0s
 => [runtime 6/7] COPY --chown=app:app frontend ./frontend                                                                                                                                                              0.0s
 => [runtime 7/7] WORKDIR /app/backend                                                                                                                                                                                  0.1s
 => exporting to image                                                                                                                                                                                                  0.3s
 => => exporting layers                                                                                                                                                                                                 0.1s
 => => exporting manifest sha256:d80f0c274fe19a08249be6b4595e14e22e70cdd58ba234245567952391328186                                                                                                                       0.0s
 => => exporting config sha256:9ef6a9f64a7229072d73bc6a823b8676edaadb672b002fa1e16314bb99fc50a4                                                                                                                         0.0s
 => => exporting attestation manifest sha256:1bcddeb1a03a7b7b99beb9de097a4f04e03cbec75036f6bb453674e280af02de                                                                                                           0.0s
 => => exporting manifest list sha256:0f21c8dc463859f9dbf87433d6e01f966df20a8856d71e185d0c4e66df520adb                                                                                                                  0.0s
 => => naming to docker.io/library/task-tracker-api:latest                                                                                                                                                              0.0s
 => => unpacking to docker.io/library/task-tracker-api:latest                                                                                                                                                           0.1s
```

**2. List the image's filesystem at the app directory, including hidden files**
```
$ docker run --rm task-tracker-api find /app -mindepth 1
$ docker run --rm task-tracker-api ls -la /app /app/backend /app/backend/app /app/frontend
```
```
/app/frontend
/app/frontend/index.html
/app/backend
/app/backend/app
/app/backend/app/routes.py
/app/backend/app/schemas.py
/app/backend/app/main.py
/app/backend/app/storage.py
/app/backend/app/business_rules.py
/app/backend/app/models.py
/app/backend/app/__init__.py
/app:
total 16
drwxr-xr-x 1 root root 4096 Aug 12 08:27 .
drwxr-xr-x 1 root root 4096 Aug 12 08:29 ..
drwxr-xr-x 3 app  app  4096 Aug 12 08:27 backend
drwxr-xr-x 2 app  app  4096 Jul 27 16:29 frontend

/app/backend:
total 12
drwxr-xr-x 3 app  app  4096 Aug 12 08:27 .
drwxr-xr-x 1 root root 4096 Aug 12 08:27 ..
drwxr-xr-x 2 app  app  4096 Aug 12 08:27 app

/app/backend/app:
total 48
drwxr-xr-x 2 app app 4096 Aug 12 08:27 .
drwxr-xr-x 3 app app 4096 Aug 12 08:27 ..
-rwxr-xr-x 1 app app    0 Jul 23 14:58 __init__.py
-rwxr-xr-x 1 app app 1523 Aug 11 17:28 business_rules.py
-rwxr-xr-x 1 app app 8853 Aug 12 08:11 main.py
-rwxr-xr-x 1 app app 7994 Aug 11 17:28 models.py
-rwxr-xr-x 1 app app  309 Jul 27 20:07 routes.py
-rwxr-xr-x 1 app app  629 Jul 23 19:10 schemas.py
-rwxr-xr-x 1 app app 6220 Aug 11 17:28 storage.py

/app/frontend:
total 36
drwxr-xr-x 2 app  app   4096 Jul 27 16:29 .
drwxr-xr-x 1 root root  4096 Aug 12 08:27 ..
-rwxr-xr-x 1 app  app  26307 Jul 27 20:42 index.html
```

docker inspect task-tracker-api --format "User: {{.Config.User}}"
>> docker history task-tracker-api
User: app
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
0f21c8dc4638   20 minutes ago   CMD ["uvicorn" "app.main:app" "--host" "0.0.…   0B        buildkit.dockerfile.v0
<missing>      20 minutes ago   EXPOSE [8000/tcp]                               0B        buildkit.dockerfile.v0
<missing>      20 minutes ago   WORKDIR /app/backend                            4.1kB     buildkit.dockerfile.v0
<missing>      20 minutes ago   USER app                                        0B        buildkit.dockerfile.v0
<missing>      20 minutes ago   ENV PATH=/home/app/.local/bin:/usr/local/bin…   0B        buildkit.dockerfile.v0
<missing>      20 minutes ago   COPY --chown=app:app frontend ./frontend # b…   41kB      buildkit.dockerfile.v0
<missing>      20 minutes ago   COPY --chown=app:app backend/app ./backend/a…   57.3kB    buildkit.dockerfile.v0
<missing>      16 hours ago     COPY --chown=app:app /root/.local /home/app/…   26.3MB    buildkit.dockerfile.v0
<missing>      16 hours ago     WORKDIR /app                                    8.19kB    buildkit.dockerfile.v0
<missing>      16 hours ago     RUN /bin/sh -c useradd --create-home --uid 1…   69.6kB    buildkit.dockerfile.v0
<missing>      7 days ago       CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      7 days ago       RUN /bin/sh -c set -eux;  for src in idle3 p…   16.4kB    buildkit.dockerfile.v0
<missing>      7 days ago       RUN /bin/sh -c set -eux;   savedAptMark="$(a…   48.8MB    buildkit.dockerfile.v0
<missing>      7 days ago       ENV PYTHON_SHA256=272179ddd9a2e41a0fc8e42e33…   0B        buildkit.dockerfile.v0
<missing>      7 days ago       ENV PYTHON_VERSION=3.11.15                      0B        buildkit.dockerfile.v0
<missing>      7 days ago       ENV GPG_KEY=A035C8C19219BA821ECEA86B64E628F8…   0B        buildkit.dockerfile.v0
<missing>      7 days ago       RUN /bin/sh -c set -eux;  apt-get update;  a…   4.94MB    buildkit.dockerfile.v0
<missing>      7 days ago       ENV LANG=C.UTF-8                                0B        buildkit.dockerfile.v0
<missing>      7 days ago       ENV PATH=/usr/local/bin:/usr/local/sbin:/usr…   0B        buildkit.dockerfile.v0
<missing>      9 days ago       # debian.sh --arch 'amd64' out/ 'trixie' '@1…   87.4MB    debuerreotype 0.17

## One AI output I rejected or corrected

**What AI claimed:** the double-fetch in `update_task` (`main.py:163-167`) was a TOCTOU race in which "`existing.status` used for validation... isn't the same read that performs the update," framed as a risk that a corrupted or stale status could get written.

**What was verified independently:** confirmed every route handler in this diff is a sync `def` function, and FastAPI dispatches sync path operations to a thread pool — so concurrent execution across requests is real, not theoretical, even in this single-process, no-`--workers` setup. Also read `storage.py`'s `update_task` and confirmed it writes `payload.status` (the target value) directly and never reads `existing.status` — so there is no path by which this code writes a corrupted value.

**Conclusion:** the real exposure is a narrow validation-bypass window (business-rule enforcement could in theory be bypassed under precise thread interleaving, in a window with no I/O in it), not data corruption — and there is no reproducer for it anywhere in this repo.

**Action taken:** accepted the mechanism (concurrency is real, the double-fetch is real), rejected the original failure-mode framing (corruption), made no code change. Logged as a known limitation.

## Protected-directory exception

`backend/app/` is protected per `AGENTS.md:21`. One exception was made this session, per the process that rule requires (explicit approval on an exact diff before any edit).

**The bug:** `PATCH /tasks/{id}` accepted an explicit `{"status": null}` body. `main.py:163`'s guard (`if payload.status is not None:`) treated "status explicitly set to null" the same as "status omitted," so `business_rules.validate_status_transition` was silently skipped, and `status: null` — a value outside the `TaskStatus` enum — was persisted to storage.

**Live reproducer (before fix):**
```
$ curl -s -X POST http://127.0.0.1:8000/tasks -d '{"title":"probe task"}'
→ id fad2f481-47e9-492c-b957-8cef09c41511

$ curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X PATCH http://127.0.0.1:8000/tasks/fad2f481-47e9-492c-b957-8cef09c41511 -d '{"status": null}'
{"due_date":null,"id":"fad2f481-...","title":"probe task","description":"","status":null,"priority":"Medium","assignee":null,"created_at":"2026-08-12T08:08:30.384172Z","updated_at":"2026-08-12T08:08:30.647597Z","overdue":false}
HTTP_STATUS:200

$ curl http://127.0.0.1:8000/tasks/fad2f481-47e9-492c-b957-8cef09c41511
{"...,"status":null,...}   # persisted on follow-up GET
```

**Applied diff** (`main.py:163-165`, only lines changed):
```diff
-    if payload.status is not None:
+    if "status" in payload.model_fields_set:
+        if payload.status is None:
+            raise HTTPException(
+                status_code=422,
+                detail="status cannot be explicitly set to null",
+            )
         existing = _require_task(task_id)
         validate_status_transition(existing.status, payload.status)
```
Two options were shown before applying: reject explicit null with 422 (chosen), or silently treat it as a no-op. No-op was rejected because it swallows the same request silently — the client would believe the update succeeded when part of it was discarded, and it would have relied on Pydantic's private `__pydantic_fields_set__` attribute rather than a documented API.

**Regression test added:** `tests/test_tasks.py::test_patch_explicit_null_status_returns_422_and_leaves_status_unchanged` — asserts `PATCH {"status": null}` returns 422 and a follow-up `GET` shows the task's status unchanged.

**Test suite after fix:** `pytest -v` → `43 passed, 2 warnings in 0.70s`.

**Why this qualified as a small bug fix, not a feature change:** the change is confined to one existing function (`update_task`), is a single added conditional (6 lines), and adds no new route, model field, or business rule — it closes a gap in an existing validation check, verified with a reproducible live bug and real HTTP evidence, not a hypothetical.

## Three AI usage rules

1. Stop and show the exact diff before touching `app/` or `frontend/` — never fix-and-report. Followed this session: the null-status bug was reproduced live, two fix options were shown with tradeoffs, and nothing was applied until a choice was made.
2. Don't trust a docstring's claim about another file — re-read the file. Pass-1 comment #5 took `main.py`'s new docstring at its word ("despite the README documenting cascade delete") instead of checking `README.md` directly. `README.md:184` already said the opposite; the stale claim was actually in `mini-adr.md:26` and in `main.py`'s own new docstring.
3. An unscoped review pass under-finds real bugs; a behaviour-scoped pass finds them. Pass 1 (unscoped) produced six comments, four cosmetic, zero touching runtime behaviour. Restricting pass 2 to status codes / validation / error paths only is what surfaced the null-status bug — the highest-severity finding in either pass.

## Ownership statement

I ran the pytest suite, Docker build, and CI workflow myself and checked the results rather than trusting them. I graded 4 of 9 AI review comments as Noise: pass 1 #3/#6 were blank-line spacing — a formatter's job, and the same finding twice; pass 2 #2 was standard FastAPI body-validation ordering with no auth boundary, and #3 was out of scope since fixing it meant adding an endpoint the project rules forbid. On the TOCTOU finding I accepted the mechanism but rejected the framing: storage.update_task writes payload.status directly and never reads existing.status, so there's no corruption path — only a narrow validation-bypass window with no reproducer, which I logged as a known limitation rather than changing code for. The one change inside app/ was main.py:163-165. I can explain every line in this branch because my process was to inspect, run, test, and refine rather than accept output as-is.
