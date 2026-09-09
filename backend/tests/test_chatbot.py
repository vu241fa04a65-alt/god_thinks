from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_chatbot_advice_endpoint_english():
    response = client.post(
        "/api/v1/chatbot/advice",
        json={
            "message": "My tomato leaf has brown concentric rings with yellow halo",
            "language": "en"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Early Blight" in data["data"]["disease_matched"]
    assert len(data["data"]["recommended_actions"]) > 0
    assert "safety_warning" in data["data"]


def test_chatbot_advice_endpoint_hindi():
    response = client.post(
        "/api/v1/chatbot/advice",
        json={
            "message": "टमाटर की पत्तियों पर धब्बे हैं",
            "language": "hi"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["language"] == "hi"
    assert "पहचाना गया रोग" in data["data"]["response_text"]


def test_chatbot_greeting():
    response = client.post(
        "/api/v1/chatbot/advice",
        json={
            "message": "Hello",
            "language": "en"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "crop type" in data["data"]["response_text"].lower()
