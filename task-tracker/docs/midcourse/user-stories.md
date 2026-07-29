# Feature 1 (Due dates + overdue filter)

**Story #1:** As a team member, I want to set a due date when creating a task so that I can plan when work needs to be finished.

*Acceptance Criteria:*
- Due date is optional; a task can be created without one.
- A valid due date is accepted and stored in ISO format (YYYY-MM-DD).
- An invalid date format returns HTTP 422.
- A created task with a due date appears in the task list showing its due date.

**Story #2:** As a team member, I want to update a task's due date so that I can adjust deadlines when plans change.

*Acceptance Criteria:*
- An existing task's due date can be changed to a new valid date.
- The due date can be cleared (set back to empty) without error.
- An invalid date format on update returns HTTP 422.
- Updating the due date does not change the task's title, status, priority, or assignee.

**Story #3:** As a team member, I want to see whether a task is overdue so that I can prioritize late work.

*Acceptance Criteria:*
- A task with a due date earlier than today and a status that is not Done is marked overdue.
- A task with a due date of today or later is not marked overdue.
- A task without a due date is never marked overdue.
- An overdue task displays a clear visual indicator (overdue pill) on its card.

**Story #4:** As a team member, I want to filter the board to show only overdue tasks so that I can focus on what is behind schedule.

*Acceptance Criteria:*
- An overdue filter returns only tasks that are currently overdue.
- When no tasks are overdue, the filter returns HTTP 200 with an empty list.
- Removing the filter restores the full task list.
- The filter does not modify or delete any tasks.

**Story #5:** As a team member, I want the system to reject an unreadable due date so that bad data does not enter the board.

*Acceptance Criteria:*
- A due date such as "2026-13-45" or "next Tuesday" returns HTTP 422.
- The error response identifies the due date field as the problem.
- The task is not created or updated when the due date is invalid.
- Valid tasks submitted afterward are unaffected by the earlier rejection.

## The story with the potential error (before correction):

**Story:** As a team member, I want to see whether a task is overdue so that I can prioritize late work.

*Acceptance Criteria:*
- A task with a due date earlier than today is marked overdue.
- An overdue task displays a clear visual indicator on its card.

## Prompt used:

> Review the overdue user story below against correct overdue logic. A task should only be considered overdue when its due date has passed and the work is still outstanding.  Prompt Library
>
> Task:
> - Identify any acceptance criterion that incorrectly marks a task as overdue. The current criteria flag any task with a past due date as overdue, which is wrong because a task that is already Done should not be flagged as overdue.
> - Rewrite only the affected criterion so that only tasks that are not Done can be overdue.
> - Add a new criterion stating that tasks without a due date are never overdue.
> - Preserve the original story format and acceptance criteria format.
>
> Output format: Return a table with columns: Original issue, Why it is incorrect, Revised version.
>
> User story: [PASTE OVERDUE STORY HERE]

## The corrected story

**Story:** As a team member, I want to see whether a task is overdue so that I can prioritize late work.

*Acceptance Criteria:*
- A task with a due date earlier than today and a status that is not Done is marked overdue.
- A task with a due date of today or later is not marked overdue.
- A task without a due date is never marked overdue.
- An overdue task displays a clear visual indicator (overdue pill) on its card.

# Feature 2 (Task Comments)

## Task Comments — User Stories

**Story:** As a team member, I want to add a comment to a task so that I can record notes, questions, or updates against the work.

*Acceptance Criteria:*
- A comment is submitted with a text field on the task's comment endpoint.
- Comment text is trimmed before it is stored.
- A successful add returns HTTP 201 with the created comment (id, task_id, text, created_at).
- The comment's id and created_at are assigned by the server, not the client.
- New comments appear in the task's comment list after they are added.

**Story:** As a team member, I want blank comments rejected so that comment data stays meaningful.

*Acceptance Criteria:*
- Submitting empty or whitespace-only text returns HTTP 422 with the text field identified.
- A comment exceeding the maximum length returns HTTP 422 with the offending field identified.
- No comment is created when validation fails.
- Sending server-assigned fields (id or created_at) in the body is rejected.

**Story:** As a team member, I want to list the comments on a task so that I can read its full history.

*Acceptance Criteria:*
- Requesting a task's comments returns them in chronological order (oldest first).
- A task with no comments returns an empty list, not an error.
- Requesting comments for a task that does not exist returns HTTP 404.
- Each returned comment includes its id, text, and created_at.

**Story:** As a team member, I want to delete a comment so that I can remove notes that are no longer relevant.

*Acceptance Criteria:*
- Deleting an existing comment removes only that comment and returns a success status.
- Deleting a comment that does not exist returns HTTP 404.
- Deleting a comment through a task it does not belong to returns HTTP 404.
- Other comments on the same task are unaffected by the deletion.

**Story:** As a team member, I want a task's comments removed when the task itself is deleted so that no orphaned comments remain.

*Acceptance Criteria:*
- Deleting a task also removes all comments attached to that task.
- No deleted task's comments remain retrievable afterward.
- Deleting a task does not affect comments belonging to other tasks