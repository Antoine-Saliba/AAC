# Due-Date and Overdue Feature

# Weak prompt

add due dates to my task app. let users set a due date and show if something is overdue. add a filter too.

# Enhanced Prompt:

# Prompt 1 — Due date field, validation, and computed overdue

You are a senior Python backend engineer. Modify my existing FastAPI models to add an optional due date and a computed overdue flag.

Context files: @app/main.py @app/models.py @app/storage.py

Generate ONLY the model changes for due date + overdue.

Exact specification:

Add to the task model an optional field: due_date: date | None = None
Accept due_date on create and update as an ISO date string (YYYY-MM-DD). Pydantic parses/validates it.
An unparseable value (e.g. "2026-13-45", "next Tuesday") must fail validation and produce a 422 identifying the due_date field. Do not write manual date parsing — let Pydantic raise.
On TaskResponse, add a computed read-only boolean overdue.
overdue is true when ALL of: due_date is not None, due_date < date.today(), and status != TaskStatus.done. Otherwise false.
overdue must be computed (e.g. @computed_field / property), never accepted from request input.

Imports to add only if missing:
from datetime import date
from pydantic import computed_field

DO NOT:

DO NOT make due_date required.
DO NOT reject past dates on write — a task may be created already overdue.
DO NOT accept overdue in any request body.
DO NOT change status values, priority, assignee, or other existing fields.
DO NOT add try/except around date parsing.
DO NOT modify any route.

Output only the changed model class(es) in one code block.

# Prompt 2 — Overdue query filter on GET /tasks

You are a senior Python backend engineer. Modify ONE existing route in my FastAPI app.

Context files: @app/main.py @app/models.py @app/storage.py

Generate ONLY the change to the existing GET /tasks list route to add an overdue filter.

Exact specification:

Route: GET /tasks (existing — extend it, do not create a second one)
Add one optional query param: overdue: bool | None = None
Keep existing params (status, priority) and existing behavior unchanged.
Behavior:
overdue=True → return only tasks where the computed overdue condition is true.
overdue=False → return only tasks where it is false.
overdue=None (omitted) → no overdue filtering; return all as before.
Overdue must use the SAME definition as the computed field: due_date is not None and due_date < date.today() and status != TaskStatus.done. Do not duplicate divergent logic — reuse the existing definition if a helper/property is available.
Empty result returns 200 with [].
The filter is read-only: it must not create, modify, or delete tasks.

Imports to add only if missing:
from datetime import date

DO NOT:

DO NOT return 404 for an empty list.
DO NOT manually validate the overdue value — FastAPI coerces the bool.
DO NOT add try/except around storage access.
DO NOT modify POST /tasks or any other route.
DO NOT change status values or the request body shape.

Output only the imports to add and the updated route function in one code block.



# Prompt 3:
You are a senior Python backend engineer. Modify ONE existing route in my FastAPI app.

Context files: @app/main.py @app/models.py @app/storage.py

Generate ONLY the change to the existing PATCH /tasks/{id} (or PUT /tasks/{id}) update route to support setting and clearing the due date.

Exact specification:

Route: existing update route for a single task — extend it, do not create a new one.
The update request model already allows partial updates; add due_date to it as date | None = None, accepted as an ISO date string (YYYY-MM-DD).
Setting behavior: a valid due_date replaces the task's current due date.
Clearing behavior: an explicit due_date: null in the body sets the task's due date back to empty (None) without error.
Untouched behavior: if due_date is omitted from the body entirely, the existing due date is left unchanged.
An unparseable value (e.g. "2026-13-45") fails validation with a 422 identifying the due_date field. Do not parse dates manually.
Updating due_date must not alter the task's title, status, priority, or assignee.
Return the updated task with status 200, including the computed overdue field.

Imports to add only if missing:
from datetime import date

DO NOT:

DO NOT treat an omitted due_date the same as an explicit null — omitted means unchanged, null means cleared.
DO NOT accept overdue in the request body.
DO NOT reject past dates on update.
DO NOT add try/except around storage access or date parsing.
DO NOT modify GET /tasks, POST /tasks, or any other route.
DO NOT change status values or the shape of other fields.

Output only the imports to add and the updated route function in one code block.




# Due-Date and Overdue Feature

## Prompt 1 — Due-date field, validation, and computed `overdue`

**What the AI returned.** It added an optional `due_date: date | None = None` to
the task model, leaned on Pydantic to parse the ISO `YYYY-MM-DD` string and raise
a `422` on unparseable input, and exposed `overdue` on `TaskResponse` as a
read-only `@computed_field` property. The overdue rule matched the spec: true
only when `due_date` is set, is before `date.today()`, and the status isn't
`Done`.

**Accepted.** The core shape — optional field, Pydantic-native validation, and a
computed rather than stored flag. Letting Pydantic raise on bad dates kept the
`422`-with-field-name behavior without any manual parsing.

**Edited.** I normalized the date/time comparison to UTC so the "past relative to
server time" check couldn't drift with the host timezone. I also pulled the
overdue condition into a single `is_task_overdue` helper rather than leaving the
logic inline in the property, so Prompt 2's filter could reuse the exact same
definition.

**Rejected.** The AI suggested persisting `overdue` as a stored field. I turned
this down because it would go stale the moment server time passed the due date
without another write; computing it on read guarantees every client sees a
consistent answer with no scheduled job to keep it fresh.

## Prompt 2 — Overdue query filter on `GET /tasks`

**What the AI returned.** It extended the existing `GET /tasks` route with one
optional `overdue: bool | None = None` param, kept the existing `status` and
`priority` params intact, and filtered on the same overdue condition: `True`
returns only overdue tasks, `False` only non-overdue, omitted returns all. Empty
results returned `200` with `[]`.

**Accepted.** The single-param extension of the existing route (not a second
route), the `None`-means-no-filter default, and the empty-list-is-`200`-not-`404`
behavior. FastAPI coercing the bool meant no manual validation was needed.

**Edited.** I made the filter call the shared `is_task_overdue` helper from
Prompt 1 instead of re-inlining the condition, so the filter and the displayed
flag can't drift apart — the single most important consistency guarantee in the
feature.

**Rejected.** An early version duplicated the overdue date-math directly inside
the route. I rejected that in favor of the shared helper for the reason above.

## Prompt 3 — Setting and clearing due date on update

**What the AI returned.** It extended the existing single-task update route,
added `due_date` to the partial-update request model, and returned the updated
task with `200` including the recomputed `overdue` field. A valid date replaced
the current one; an invalid date produced a `422` naming the field.

**Accepted.** Reusing the existing update route rather than adding one, and
returning the freshly computed `overdue` in the response so the client never has
to guess the new state.

**Edited.** The critical fix was the omitted-vs-`null` distinction. The first
pass treated a missing `due_date` and an explicit `due_date: null` the same way,
which would have made it impossible to clear a date without wiping other omitted
fields. I switched the update to use `exclude_unset` so "field absent" means
unchanged while an explicit `null` clears the date to `None` — satisfying the
"due date can be cleared without error" requirement.

**Rejected.** I declined to add past-date rejection on update; a task may
legitimately be edited to an already-overdue date, and blocking that would
contradict the compute-on-read model.





# Task comments


# Weak prompt

add a way to comment on tasks in my fastapi app

# Enhanced Prompt:


## Prompt 1 — POST /tasks/{task_id}/comments

You are a senior Python backend engineer. Add ONE route to my existing FastAPI app.
Context files: @app/main.py @app/models.py @app/storage.py

Generate ONLY the POST comment route. Exact specification:
- Route: POST /tasks/{task_id}/comments
- Status code: 201 (status.HTTP_201_CREATED)
- Tags: ["comments"]
- Path param: task_id: str
- Request body: payload: CommentCreate
- Response model: Comment
- Behavior:
  - If storage.get_task_by_id(task_id) is None, raise HTTPException(404, f"Task with id {task_id} not found")
  - Otherwise return storage.add_comment(task_id, payload)
- Non-blank validation is handled by CommentCreate (do not re-validate text here).

Imports to add only if missing:
from app.models import Comment, CommentCreate
from app import storage

DO NOT:
- DO NOT accept id or created_at from the body; CommentCreate uses extra="forbid".
- DO NOT manually strip or validate the text; the model does it.
- DO NOT add try/except around storage calls.
- DO NOT modify any existing task route.

Output only the imports to add and the new route function in one code block.


## Prompt 2 — GET /tasks/{task_id}/comments

You are a senior Python backend engineer. Add ONE route to my existing FastAPI app.
Context files: @app/main.py @app/models.py @app/storage.py

Generate ONLY the GET comment list route. Exact specification:
- Route: GET /tasks/{task_id}/comments
- Status code: 200 default is fine
- Tags: ["comments"]
- Path param: task_id: str
- Response model: list[Comment]
- Behavior:
  - If storage.get_task_by_id(task_id) is None, raise HTTPException(404, f"Task with id {task_id} not found")
  - Otherwise return storage.get_comments_for_task(task_id)
- A task with no comments returns 200 with [].
- Comments come back sorted by created_at ascending (storage handles ordering).

Imports to add only if missing:
from app.models import Comment
from app import storage

DO NOT:
- DO NOT return 404 for an empty comment list on an existing task.
- DO NOT sort or filter in the route; storage.get_comments_for_task does it.
- DO NOT add try/except around storage calls.
- DO NOT modify any existing task route.

Output only the imports to add and the new route function in one code block.




## Prompt 3 — DELETE /tasks/{task_id}/comments/{comment_id}

You are a senior Python backend engineer. Add ONE route to my existing FastAPI app.
Context files: @app/main.py @app/models.py @app/storage.py

Generate ONLY the DELETE comment route. Exact specification:
- Route: DELETE /tasks/{task_id}/comments/{comment_id}
- Status code: 204 (status.HTTP_204_NO_CONTENT)
- Tags: ["comments"]
- Path params: task_id: str, comment_id: str
- Response: None
- Behavior:
  - If storage.get_task_by_id(task_id) is None, raise HTTPException(404, f"Task with id {task_id} not found")
  - Fetch comment = storage.get_comment_by_id(comment_id)
  - If comment is None OR comment.task_id != task_id, raise HTTPException(404, f"Comment with id {comment_id} not found")
  - Otherwise call storage.delete_comment(comment_id)

Imports to add only if missing:
from app import storage

DO NOT:
- DO NOT return the deleted comment body; 204 has no content.
- DO NOT allow deleting a comment via a task_id it doesn't belong to (the task_id mismatch must 404).
- DO NOT add try/except around storage calls.
- DO NOT modify any existing task route.

Output only the imports to add and the new route function in one code block.




#  Task Comments

## Prompt 1 — POST /tasks/{task_id}/comments

**What the AI returned.** A single `201` route tagged `["comments"]` that takes a
`CommentCreate` body, `404`s when the parent task is missing, and otherwise
returns `storage.add_comment(task_id, payload)` as a `Comment`. Non-blank text
validation was left to the model rather than repeated in the route.

**Accepted.** The route shape, the `201` status, and pushing text validation and
`extra="forbid"` down into `CommentCreate` so the endpoint stays thin. Delegating
`id`/`created_at` rejection to the model matched the server-assigns-fields
decision.

**Edited.** I confirmed the `404` message format was consistent with the existing
task routes' error strings so clients see one convention across the API.

**Rejected.** An early draft re-stripped and re-checked the text inside the route.
I removed it — double validation invites the two checks drifting apart, and the
model is the single source of truth for non-blank enforcement.

## Prompt 2 — GET /tasks/{task_id}/comments

**What the AI returned.** A `200` list route returning `list[Comment]`, `404`ing
on a missing parent task, and otherwise returning
`storage.get_comments_for_task(task_id)`. A task with no comments returned `200`
with `[]`, and ordering by `created_at` ascending was handled in storage.

**Accepted.** The empty-list-is-`200`-not-`404` behavior (an existing task with
zero comments is a valid state, not an error) and keeping sort/filter logic in
storage rather than the route.

**Edited.** Nothing material — I verified the sort lived in
`get_comments_for_task` so the route stayed a pass-through, consistent with how
the task-list route delegates ordering.

**Rejected.** A version that sorted in the route. I moved ordering back to storage
so the route has no data logic and both list endpoints follow the same pattern.

## Prompt 3 — DELETE /tasks/{task_id}/comments/{comment_id}

**What the AI returned.** A `204` route with no response body, `404`ing when the
parent task is missing, then fetching the comment and `404`ing if it's missing or
if its `task_id` doesn't match the path — only then calling
`storage.delete_comment(comment_id)`.

**Accepted.** The `204`-no-content contract and the two-step existence check.

**Edited.** I made sure the mismatch case (`comment.task_id != task_id`) was
enforced exactly as written — this is the security-relevant guard.

**Rejected.** A simpler version that deleted by `comment_id` alone without
checking the comment actually belonged to the task in the path. I rejected it
because it would let a caller delete any comment through an unrelated task's URL;
the `task_id` mismatch must `404`.