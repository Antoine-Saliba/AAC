# Decision Note: Due-Date/Overdue and Task Comments

I added two features to the Task Tracker: an optional due date with a
server-computed `overdue` flag, and task comments (list, add, delete).

## Due date and overdue

I added an optional `due_date` field to the task models, accepted as an ISO 8601
string and normalized to UTC inside a validator before it's stored. The key
decision was computing `overdue` on the **backend** rather than in the frontend.
I exposed it as a read-only computed field on each task response, using a single
`is_task_overdue` helper: a task is overdue when its due date is set, is in the
past relative to server time, and its status isn't `Done`. The
`?overdue=true|false` list filter calls that same helper, so the filter and the
displayed flag can't drift apart.

## Comments

I added a `Comment` model and a `CommentCreate` input model, stored in a separate
in-memory dictionary keyed by comment id, with each comment holding its
`task_id`. I added three endpoints for list, add, and delete:

- **Validation** — text is checked non-blank by stripping whitespace and
  rejecting empty input with a `422` that names the field.
- **Not-found handling** — missing tasks or comments return `404`.
- **Cascade** — deleting a task removes its comments, so none are orphaned.
- **Server-assigned fields** — `id` and `created_at` are set by the server and
  rejected if a client tries to send them.

## Alternatives the AI suggested, and what I rejected

The AI offered several fuller designs that I turned down as too complex or
outside the assignment's scope:

- **Persisting `overdue` as a stored field.** Rejected because it would go stale
  as soon as server time passed the due date without another write. Computing it
  on read guarantees every client sees a consistent answer with no scheduled job
  to keep it fresh.
- **A dedicated comments table or an ORM/database layer.** Out of scope — this
  project uses JSON/in-memory storage by design, so I matched the existing
  task-storage pattern instead of introducing new infrastructure.
- **Threaded replies, comment editing, and author/user fields.** The user story
  only asked for list, add, and delete with non-blank validation, so I left these
  out. Adding them would have expanded the data model and API surface well past
  the requirement.

## What I kept deliberately minimal

I used UTC consistently for all date comparisons to avoid timezone ambiguity, and
I scoped the change to just the new field, its validation, the computed flag, the
query filter, and the comment model with its three endpoints. Existing status
values, response shapes, filters, sorting, and pagination were left untouched.