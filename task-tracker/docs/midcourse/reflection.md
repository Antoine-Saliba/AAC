# Working with AI on the Due-Date and Comments Features

I used two AI tools on this project: GitHub Copilot and Claude. Copilot handled fast inline suggestions while I was typing in the editor, and Claude did the heavier lifting — turning vague requests into precise, constraint-heavy prompts and generating the model and route changes for the due-date, overdue, and comment features. I stayed the reviewer, deciding what to accept, edit, or reject.

# One moment AI helped: 
The strongest contribution was the computed overdue flag. Claude correctly leaned on Pydantic to parse the ISO date and raise a 422 on bad input, and exposed overdue as a read-only computed field rather than a stored value. Compute-on-read was the right call — a stored flag would have gone stale the moment server time passed the due date. That saved me a whole class of consistency bugs.

# One moment AI slowed me down:
 The AI couldn't target one specific issue: the due_date field wasn't supported properly, so the request threw an "extra input" error (Pydantic's extra="forbid" rejecting it). It kept circling without isolating the cause, so I traced it myself and fixed it faster than the back-and-forth would have taken.

# One place my review changed the result: \
On the update route, the first pass treated an omitted due_date and an explicit null the same way. I switched it to exclude_unset, so absent means unchanged and null means clear — satisfying the "clear without error" requirement.