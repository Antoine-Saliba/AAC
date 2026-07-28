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

# Feature 2 (Tags / labels)

## Tags / Labels — User Stories

**Story:** As a team member, I want to add tags to a task so that I can categorize and group related work.

*Acceptance Criteria:*
- Tags are entered as a list or comma-separated field and normalized (trimmed, deduplicated).
- Each tag value must be non-empty after trimming; whitespace-only tags are discarded.
- Created tags appear as chips on the task card.
- Tags persist and are returned with the task record.

**Story:** As a team member, I want empty or invalid tags rejected so that tag data stays clean.

*Acceptance Criteria:*
- Submitting a tag that is empty or whitespace-only returns HTTP 422.
- A tag exceeding the maximum length returns HTTP 422 with the offending value identified.
- Exceeding the maximum tag count per task returns HTTP 422.
- No task is created or updated when validation fails.

**Story:** As a team member, I want to update the tags on an existing task so that I can re-categorize it as work evolves.

*Acceptance Criteria:*
- Submitting a new tag list replaces the previous set after normalization.
- Removing all tags is allowed and leaves the task with zero tags.
- Duplicate tags in the submission are collapsed to a single value.
- The updated tag chips render on the card immediately after save.

**Story:** As a team member, I want to filter tasks by tag so that I can focus on one category at a time.

*Acceptance Criteria:*
- Selecting a tag shows only tasks containing that tag.
- Selecting multiple tags returns tasks matching all selected tags.
- Clearing the filter restores the full task list.
- A tag with no matching tasks returns an empty result, not an error.

**Story:** As a team member, I want my tags preserved when I update unrelated task fields so that categorization isn't lost.

*Acceptance Criteria:*
- Updating title, description, status, priority, or assignee leaves existing tags unchanged.
- Tags are only modified when the tag field is explicitly included in the request.
- Omitting the tag field from an update request does not clear existing tags.
- Tag chips remain rendered on the card after an unrelated update.