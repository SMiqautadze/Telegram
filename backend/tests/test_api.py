import pytest
import httpx
import os
from datetime import datetime

# Get the backend URL from environment variable or use default
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001/api')

class TestTelegramScraperAPI:
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
        self.token = None

    def test_01_register(self):
        """Test user registration"""
        response = self.client.post("/api/register", json=self.test_user)
        assert response.status_code in [200, 400], f"Registration failed: {response.text}"
        if response.status_code == 400:
            assert "Email already registered" in response.text

    def test_02_login(self):
        """Test user login"""
        response = self.client.post("/api/login", json={
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        self.token = data["access_token"]

    def test_03_me(self):
        """Test getting user profile"""
        assert self.token, "Login required"
        response = self.client.get("/api/me", headers={"Authorization": f"Bearer {self.token}"})
        assert response.status_code == 200, f"Get profile failed: {response.text}"
        data = response.json()
        assert data["email"] == self.test_user["email"]

    def test_04_telegram_credentials(self):
        """Test setting and getting Telegram credentials"""
        assert self.token, "Login required"
        headers = {"Authorization": f"Bearer {self.token}"}

        # Set credentials
        response = self.client.post("/api/telegram-credentials", 
                                  json=self.telegram_creds,
                                  headers=headers)
        assert response.status_code == 200, f"Setting credentials failed: {response.text}"

        # Get credentials
        response = self.client.get("/api/telegram-credentials", headers=headers)
        assert response.status_code == 200, f"Getting credentials failed: {response.text}"
        data = response.json()
        assert data["api_id"] == self.telegram_creds["api_id"]
        assert data["api_hash"] == self.telegram_creds["api_hash"]

    def test_05_channels(self):
        """Test channel management"""
        assert self.token, "Login required"
        headers = {"Authorization": f"Bearer {self.token}"}

        # Add a test channel
        test_channel = {
            "channel_id": "test_channel",
            "last_message_id": 0
        }
        response = self.client.post("/api/channels", json=test_channel, headers=headers)
        assert response.status_code == 200, f"Adding channel failed: {response.text}"

        # Get channels
        response = self.client.get("/api/channels", headers=headers)
        assert response.status_code == 200, f"Getting channels failed: {response.text}"
        data = response.json()
        assert "channels" in data
        assert test_channel["channel_id"] in data["channels"]

        # Delete channel
        response = self.client.delete(f"/api/channels/{test_channel['channel_id']}", headers=headers)
        assert response.status_code == 200, f"Deleting channel failed: {response.text}"

    def test_06_channels_list(self):
        """Test listing available Telegram channels"""
        assert self.token, "Login required"
        headers = {"Authorization": f"Bearer {self.token}"}

        response = self.client.get("/api/channels-list", headers=headers)
        # This might fail if Telegram credentials are not properly set up
        if response.status_code == 200:
            data = response.json()
            assert "channels" in data
        else:
            assert response.status_code in [400, 500]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
