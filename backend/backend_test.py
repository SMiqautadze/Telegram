import pytest
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the backend URL from environment variable
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')

class TestTelegramScraper:
    def setup_method(self):
        self.client = httpx.Client(base_url=BACKEND_URL)
        self.test_user = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        self.telegram_creds = {
            "api_id": 20223845,
            "api_hash": "2d9943c0c4b2b37998a6868f385f3f32",
            "phone": "+1234567890"
        }
        self.test_channel = {
            "channel_id": "test_channel",
            "last_message_id": 0
        }
        self.token = None

    def test_01_register(self):
        response = self.client.post("/api/register", json=self.test_user)
        assert response.status_code in [200, 201, 400], f"Registration failed: {response.text}"
        if response.status_code == 400:
            assert "Email already registered" in response.text

    def test_02_login(self):
        response = self.client.post("/api/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        self.token = data["access_token"]

    def test_03_set_telegram_credentials(self):
        assert self.token is not None, "No authentication token available"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.post(
            "/api/telegram-credentials",
            json=self.telegram_creds,
            headers=headers
        )
        assert response.status_code == 200, f"Setting Telegram credentials failed: {response.text}"

    def test_04_get_telegram_credentials(self):
        assert self.token is not None, "No authentication token available"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get("/api/telegram-credentials", headers=headers)
        assert response.status_code == 200, f"Getting Telegram credentials failed: {response.text}"
        data = response.json()
        assert data["api_id"] == self.telegram_creds["api_id"]
        assert data["api_hash"] == self.telegram_creds["api_hash"]
        assert data["phone"] == self.telegram_creds["phone"]

    def test_05_add_channel(self):
        assert self.token is not None, "No authentication token available"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.post(
            "/api/channels",
            json=self.test_channel,
            headers=headers
        )
        assert response.status_code == 200, f"Adding channel failed: {response.text}"

    def test_06_get_channels(self):
        assert self.token is not None, "No authentication token available"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get("/api/channels", headers=headers)
        assert response.status_code == 200, f"Getting channels failed: {response.text}"
        data = response.json()
        assert "channels" in data
        assert self.test_channel["channel_id"] in data["channels"]

    def test_07_remove_channel(self):
        assert self.token is not None, "No authentication token available"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.delete(
            f"/api/channels/{self.test_channel['channel_id']}",
            headers=headers
        )
        assert response.status_code == 200, f"Removing channel failed: {response.text}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
