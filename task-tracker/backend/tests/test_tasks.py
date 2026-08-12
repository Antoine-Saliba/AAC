def test_create_task_valid_returns_201_with_full_body(client):
    payload = {
        "title": "Full task",
        "description": "A description",
        "status": "ToDo",
        "priority": "High",
        "assignee": "alice",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Full task"
    assert body["description"] == "A description"
    assert body["status"] == "ToDo"
    assert body["priority"] == "High"
    assert body["assignee"] == "alice"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks", json={"description": "no title"})
    assert response.status_code == 422


def test_create_task_blank_title_returns_422(client):
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "Valid title", "priority": "Urgent"})
    assert response.status_code == 422


def test_create_task_unknown_field_returns_422(client):
    response = client.post("/tasks", json={"title": "Valid title", "unknown": "value"})
    assert response.status_code == 422


def test_create_task_with_valid_due_date_returns_201_and_stores_due_date(client):
    response = client.post(
        "/tasks",
        json={"title": "Valid due date", "due_date": "2026-01-02"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] == "2026-01-02T00:00:00+00:00"


def test_create_task_with_invalid_due_date_returns_422(client):
    response = client.post("/tasks", json={"title": "Bad due date", "due_date": "not-a-date"})
    assert response.status_code == 422
    assert "due_date" in response.text

def test_update_task_can_clear_due_date_with_null(client):
    create = client.post("/tasks", json={"title": "Has a date", "due_date": "2026-01-01"})
    task = create.json()
    response = client.patch(f"/tasks/{task['id']}", json={"due_date": None})
    assert response.status_code == 200
    assert response.json()["due_date"] is None
    assert response.json()["overdue"] is False


def test_update_other_field_leaves_due_date_unchanged(client):
    create = client.post("/tasks", json={"title": "Keep date", "due_date": "2026-01-01"})
    task = create.json()
    response = client.patch(f"/tasks/{task['id']}", json={"title": "New title"})
    assert response.status_code == 200
    assert response.json()["due_date"] == "2026-01-01T00:00:00+00:00"


def test_task_without_due_date_is_never_overdue(client):
    response = client.post("/tasks", json={"title": "No date"})
    assert response.status_code == 201
    assert response.json()["overdue"] is False

def test_list_tasks_empty_returns_200_and_empty_list(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_status_no_match_returns_200_and_empty_list(client):
    client.post("/tasks", json={"title": "ToDo task"})
    response = client.get("/tasks", params={"status": "InProgress"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_priority_returns_only_matches(client):
    client.post("/tasks", json={"title": "High task", "priority": "High"})
    client.post("/tasks", json={"title": "Low task", "priority": "Low"})
    response = client.get("/tasks", params={"priority": "High"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "High task"
    assert tasks[0]["priority"] == "High"


def test_get_task_by_id_returns_task(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}")
    assert response.status_code == 200
    assert response.json() == created_task


def test_get_task_by_id_not_found_returns_404_with_detail(client):
    task_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {task_id} not found"


def test_patch_partial_update_keeps_other_fields(client):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original title",
            "description": "Original description",
            "status": "ToDo",
            "priority": "Low",
            "assignee": "bob",
        },
    )
    task = create_response.json()
    response = client.patch(f"/tasks/{task['id']}", json={"title": "Updated title"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated title"
    assert body["description"] == "Original description"
    assert body["status"] == "ToDo"
    assert body["priority"] == "Low"
    assert body["assignee"] == "bob"


def test_patch_not_found_returns_404(client):
    task_id = "00000000-0000-0000-0000-000000000000"
    response = client.patch(f"/tasks/{task_id}", json={"title": "Updated"})
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {task_id} not found"


def test_patch_valid_transition_todo_to_inprogress_returns_200(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": "InProgress"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"


def test_patch_invalid_transition_todo_to_done_returns_422(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": "Done"},
    )
    assert response.status_code == 422


def test_patch_explicit_null_status_returns_422_and_leaves_status_unchanged(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": None},
    )
    assert response.status_code == 422

    follow_up = client.get(f"/tasks/{created_task['id']}")
    assert follow_up.json()["status"] == created_task["status"]


def test_patch_same_status_is_allowed_noop_returns_200(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": "ToDo"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ToDo"


def test_patch_empty_json_body_leaves_task_unchanged_and_succeeds(client):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original title",
            "description": "Original description",
            "status": "ToDo",
            "priority": "Medium",
        },
    )
    task = create_response.json()

    response = client.patch(f"/tasks/{task['id']}", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == task["id"]
    assert body["title"] == "Original title"
    assert body["description"] == "Original description"
    assert body["status"] == "ToDo"
    assert body["priority"] == "Medium"


def test_due_date_on_past_non_done_task_is_overdue_and_done_task_is_not(client):
    create_response = client.post(
        "/tasks",
        json={"title": "Overdue task", "due_date": "2000-01-01", "status": "InProgress"},
    )
    task = create_response.json()
    assert task["overdue"] is True

    patch_response = client.patch(f"/tasks/{task['id']}", json={"status": "Done"})
    assert patch_response.status_code == 200
    assert patch_response.json()["overdue"] is False


def test_update_task_due_date_keeps_other_fields_unchanged(client):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original title",
            "status": "ToDo",
            "priority": "Low",
            "assignee": "bob",
            "due_date": "2026-01-01",
        },
    )
    task = create_response.json()

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"due_date": "2026-02-01"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["due_date"] == "2026-02-01T00:00:00+00:00"
    assert body["title"] == "Original title"
    assert body["status"] == "ToDo"
    assert body["priority"] == "Low"
    assert body["assignee"] == "bob"


def test_list_tasks_can_filter_by_overdue_flag(client):
    client.post("/tasks", json={"title": "Overdue task", "due_date": "2000-01-01"})
    client.post("/tasks", json={"title": "Future task", "due_date": "2099-01-01"})

    overdue_response = client.get("/tasks", params={"overdue": "true"})
    non_overdue_response = client.get("/tasks", params={"overdue": "false"})

    assert overdue_response.status_code == 200
    assert non_overdue_response.status_code == 200
    assert [task["title"] for task in overdue_response.json()] == ["Overdue task"]
    assert [task["title"] for task in non_overdue_response.json()] == ["Future task"]


def test_delete_existing_returns_204_no_body(client, created_task):
    response = client.delete(f"/tasks/{created_task['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_returns_404(client):
    task_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {task_id} not found"



# ---------- Comments: POST /tasks/{task_id}/comments ----------

def test_add_comment_valid_returns_201_with_body(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"text": "First comment"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "First comment"
    assert body["task_id"] == created_task["id"]
    assert "id" in body
    assert "created_at" in body


def test_add_comment_blank_text_returns_422(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"text": "   "},
    )
    assert response.status_code == 422


def test_add_comment_missing_text_returns_422(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={},
    )
    assert response.status_code == 422


def test_add_comment_to_missing_task_returns_404(client):
    task_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(f"/tasks/{task_id}/comments", json={"text": "Hi"})
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {task_id} not found"


def test_add_comment_rejects_client_supplied_id_returns_422(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"text": "Sneaky", "id": "abc"},
    )
    assert response.status_code == 422


def test_add_comment_rejects_client_supplied_created_at_returns_422(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"text": "Sneaky", "created_at": "2020-01-01T00:00:00+00:00"},
    )
    assert response.status_code == 422


# ---------- Comments: GET /tasks/{task_id}/comments ----------

def test_list_comments_empty_returns_200_and_empty_list(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}/comments")
    assert response.status_code == 200
    assert response.json() == []


def test_list_comments_returns_added_comments(client, created_task):
    client.post(f"/tasks/{created_task['id']}/comments", json={"text": "One"})
    client.post(f"/tasks/{created_task['id']}/comments", json={"text": "Two"})
    response = client.get(f"/tasks/{created_task['id']}/comments")
    assert response.status_code == 200
    texts = [c["text"] for c in response.json()]
    assert texts == ["One", "Two"]


def test_list_comments_ordered_by_created_at_ascending(client, created_task):
    client.post(f"/tasks/{created_task['id']}/comments", json={"text": "Oldest"})
    client.post(f"/tasks/{created_task['id']}/comments", json={"text": "Newest"})
    response = client.get(f"/tasks/{created_task['id']}/comments")
    body = response.json()
    assert [c["text"] for c in body] == ["Oldest", "Newest"]
    assert body[0]["created_at"] <= body[1]["created_at"]


def test_list_comments_for_missing_task_returns_404(client):
    task_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/tasks/{task_id}/comments")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {task_id} not found"


# ---------- Comments: DELETE /tasks/{task_id}/comments/{comment_id} ----------

def test_delete_comment_returns_204_no_body(client, created_task):
    create = client.post(
        f"/tasks/{created_task['id']}/comments", json={"text": "Delete me"}
    )
    comment_id = create.json()["id"]
    response = client.delete(f"/tasks/{created_task['id']}/comments/{comment_id}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_comment_actually_removes_it(client, created_task):
    create = client.post(
        f"/tasks/{created_task['id']}/comments", json={"text": "Gone soon"}
    )
    comment_id = create.json()["id"]
    client.delete(f"/tasks/{created_task['id']}/comments/{comment_id}")
    remaining = client.get(f"/tasks/{created_task['id']}/comments").json()
    assert all(c["id"] != comment_id for c in remaining)


def test_delete_missing_comment_returns_404(client, created_task):
    comment_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(
        f"/tasks/{created_task['id']}/comments/{comment_id}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"Comment with id {comment_id} not found"


def test_delete_comment_on_missing_task_returns_404(client):
    task_id = "00000000-0000-0000-0000-000000000000"
    comment_id = "11111111-1111-1111-1111-111111111111"
    response = client.delete(f"/tasks/{task_id}/comments/{comment_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {task_id} not found"


def test_delete_comment_via_wrong_task_returns_404(client, created_task):
    # comment belongs to created_task; try deleting it through a different task
    create = client.post(
        f"/tasks/{created_task['id']}/comments", json={"text": "Mine"}
    )
    comment_id = create.json()["id"]
    other = client.post("/tasks", json={"title": "Other task"})
    other_id = other.json()["id"]
    response = client.delete(f"/tasks/{other_id}/comments/{comment_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Comment with id {comment_id} not found"