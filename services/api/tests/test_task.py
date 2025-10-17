def test_tasks_crud(client):
    r0 = client.get("/tasks/all")
    assert r0.status_code == 200
    assert r0.json()["total"] == 0

    payload = {"name": "Teste", "description": "Primeira", "date": "2025-10-14"}
    r1 = client.post("/tasks/task", json=payload)
    assert r1.status_code in (200, 201), r1.text

    r2 = client.get("/tasks/all")
    assert r2.status_code == 200
    tasks = r2.json()["tasks"]
    assert len(tasks) == 1
    task_id = tasks[0]["id"]

    r3 = client.patch(f"/tasks/{task_id}", json={"state": "ANDAMENTO"})
    assert r3.status_code == 200

    r4 = client.get("/tasks/all")
    st = next(t for t in r4.json()["tasks"] if t["id"] == task_id)
    assert st["state"] == "ANDAMENTO"

    r5 = client.delete(f"/tasks/{task_id}")
    assert r5.status_code in (200, 204), r5.text

    r6 = client.get("/tasks/all")
    assert r6.status_code == 200
    assert r6.json()["total"] == 0
