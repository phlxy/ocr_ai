import pytest
from fastapi.testclient import TestClient
from api.api_handler import app

client = TestClient(app)

def test_create_and_get_annotation():
    # ทดสอบ POST เพื่อสร้าง annotation
    payload = {"x": 10, "y": 20, "width": 30, "height": 40, "label": "Test"}
    response = client.post("/annotations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["x"] == 10
    assert data["label"] == "Test"
    
    # ทดสอบ GET เพื่อดึงข้อมูล annotation ทั้งหมด
    response = client.get("/annotations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_export_endpoints():
    # สร้าง annotation ก่อนทดสอบ export
    payload = {"x": 5, "y": 5, "width": 15, "height": 15, "label": "A"}
    client.post("/annotations", json=payload)
    
    response = client.get("/export/json")
    assert response.status_code == 200
    data = response.json()
    # export แบบ JSON ควรได้ list
    assert isinstance(data, list)
    
    response = client.get("/export/layoutlm")
    assert response.status_code == 200
    data = response.json()
    assert "annotations" in data
    assert "metadata" in data

def test_validate_endpoint():
    response = client.get("/validate")
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert "message" in data
