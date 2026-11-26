from fastapi.testclient import TestClient

from app.main import app


def register(client, email):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "StrongPassword!42"},
    )
    assert response.status_code == 201
    return response.json()


def test_ingest_is_idempotent_and_cross_user_scan_is_404():
    with TestClient(app) as client:
        first = register(client, "scan-user@example.com")
        headers = {"Authorization": f"Bearer {first['access_token']}"}
        payload = {
            "client_id": "phone-1",
            "model_name": "resnet50",
            "model_version": "test",
            "result": {
                "top3": [
                    {"class_name": "Tomato___healthy", "probability": 0.8},
                    {"class_name": "Tomato___Early_blight", "probability": 0.1},
                ],
                "top_class": "Tomato___healthy",
                "unsure": False,
            },
        }
        ingested = client.post("/scans/ingest", json=payload, headers=headers)
        assert ingested.status_code == 200
        scan_id = ingested.json()["id"]
        duplicate = client.post("/scans/ingest", json=payload, headers=headers)
        assert duplicate.status_code == 200
        assert duplicate.json()["id"] == scan_id

        second = register(client, "other-user@example.com")
        other_headers = {"Authorization": f"Bearer {second['access_token']}"}
        assert client.get(f"/scans/{scan_id}", headers=other_headers).status_code == 404
        assert client.delete(f"/scans/{scan_id}", headers=other_headers).status_code == 404


def test_ingest_rejects_invalid_probability():
    with TestClient(app) as client:
        auth = register(client, "invalid-result@example.com")
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        payload = {
            "client_id": "invalid-1",
            "model_name": "resnet50",
            "model_version": "test",
            "result": {
                "top3": [{"class_name": "Tomato___healthy", "probability": 1.2}],
                "top_class": "Tomato___healthy",
            },
        }
        response = client.post("/scans/ingest", json=payload, headers=headers)
        assert response.status_code == 422


def test_corrupt_upload_is_rejected():
    with TestClient(app) as client:
        auth = register(client, "corrupt-upload@example.com")
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        response = client.post(
            "/scans",
            data={"model": "resnet50", "segment": "false"},
            files={"file": ("bad.jpg", b"not an image", "image/jpeg")},
            headers=headers,
        )
        assert response.status_code == 400


def test_scan_pagination_and_delete():
    with TestClient(app) as client:
        auth = register(client, "pagination@example.com")
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        ids = []
        for index in range(23):
            payload = {
                "client_id": f"page-{index}",
                "model_name": "resnet50",
                "model_version": "test",
                "result": {
                    "top3": [{"class_name": "Tomato___healthy", "probability": 0.9}],
                    "top_class": "Tomato___healthy",
                },
            }
            response = client.post("/scans/ingest", json=payload, headers=headers)
            ids.append(response.json()["id"])

        first = client.get("/scans?limit=20", headers=headers)
        assert first.status_code == 200
        assert len(first.json()["items"]) == 20
        assert first.json()["next_cursor"]

        second = client.get(
            f"/scans?cursor={first.json()['next_cursor']}",
            headers=headers,
        )
        assert second.status_code == 200
        assert len(second.json()["items"]) == 3

        deleted = client.delete(f"/scans/{ids[0]}", headers=headers)
        assert deleted.status_code == 204
        assert client.get(f"/scans/{ids[0]}", headers=headers).status_code == 404


def test_create_scan_classifies_and_segments():
    import io
    from PIL import Image

    image = Image.new("RGB", (256, 256), "green")
    buffer = io.BytesIO()
    image.save(buffer, "JPEG")

    with TestClient(app) as client:
        auth = register(client, "create-scan@example.com")
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        response = client.post(
            "/scans",
            data={"model": "resnet50", "segment": "true"},
            files={"file": ("leaf.jpg", buffer.getvalue(), "image/jpeg")},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["model_name"] == "resnet50"
        assert len(body["top3"]) == 3
        assert body["lesion_area_frac"] is not None
        assert body["mask_url"] is not None


def test_list_models_includes_classifiers_and_segmenters():
    with TestClient(app) as client:
        response = client.get("/models")
        assert response.status_code == 200
        models = response.json()["models"]
        assert {(m["name"], m["task"]) for m in models} >= {
            ("resnet50", "classifier"),
            ("resnet50", "segmenter"),
            ("mobilenet", "segmenter"),
        }
