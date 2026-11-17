def test_create_and_get(client):
    resp = client.post("/api/notes", json={"title": "Hola", "body": "mundo"})
    assert resp.status_code == 201
    note = resp.get_json()
    assert note["title"] == "Hola"

    got = client.get(f"/api/notes/{note['id']}")
    assert got.status_code == 200
    assert got.get_json()["body"] == "mundo"


def test_list_is_newest_first_and_limited(client):
    for i in range(3):
        client.post("/api/notes", json={"title": f"n{i}"})
    data = client.get("/api/notes?limit=2").get_json()
    assert [n["title"] for n in data] == ["n2", "n1"]


def test_validation_error(client):
    resp = client.post("/api/notes", json={"title": "   "})
    assert resp.status_code == 422
    assert "title" in resp.get_json()["detail"]


def test_not_found_is_json(client):
    resp = client.get("/api/notes/999")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Not Found"


def test_delete(client):
    note_id = client.post("/api/notes", json={"title": "borrar"}).get_json()["id"]
    assert client.delete(f"/api/notes/{note_id}").status_code == 204
    assert client.get(f"/api/notes/{note_id}").status_code == 404
