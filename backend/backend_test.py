import pytest
import httpx
import os
from datetime import datetime

# Get the backend URL from environment variable
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')

class TestTelegramScraperAPI:
    def setup_method(self):
        self.client = httpx.Client(base_url=BACKEND_URL)
        self.test_user = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        self.telegram_credentials = {
            "api_id": 20223845,
            "api_hash": "2d9943c0c4b2b37998a6868f385f3f32",
            "phone": "+1234567890"
        }
        self.token = None

    def test_01_register(self):
        try:
            response = self.client.post("/api/register", json=self.test_user)
            assert response.status_code in [200, 400], f"Registration failed with status {response.status_code}"
            if response.status_code == 400:
                assert "Email already registered" in response.json()["detail"]
            else:
                assert "id" in response.json()
                assert response.json()["email"] == self.test_user["email"]
        except Exception as e:
            pytest.fail(f"Registration test failed: {str(e)}")

    def test_02_login(self):
        try:
            response = self.client.post("/api/login", json={
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            })
            assert response.status_code == 200, f"Login failed with status {response.status_code}"
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            self.token = data["access_token"]
        except Exception as e:
            pytest.fail(f"Login test failed: {str(e)}")

    def test_03_get_user_profile(self):
        try:
            assert self.token is not None, "No authentication token available"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get("/api/me", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == self.test_user["email"]
            assert data["full_name"] == self.test_user["full_name"]
        except Exception as e:
            pytest.fail(f"Get profile test failed: {str(e)}")

    def test_04_set_telegram_credentials(self):
        try:
            assert self.token is not None, "No authentication token available"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.post(
                "/api/telegram-credentials",
                json=self.telegram_credentials,
                headers=headers
            )
            assert response.status_code == 200
            assert "message" in response.json()
        except Exception as e:
            pytest.fail(f"Set Telegram credentials test failed: {str(e)}")

    def test_05_get_telegram_credentials(self):
        try:
            assert self.token is not None, "No authentication token available"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get("/api/telegram-credentials", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["api_id"] == self.telegram_credentials["api_id"]
            assert data["api_hash"] == self.telegram_credentials["api_hash"]
            assert data["phone"] == self.telegram_credentials["phone"]
        except Exception as e:
            pytest.fail(f"Get Telegram credentials test failed: {str(e)}")

    def test_06_channel_management(self):
        try:
            assert self.token is not None, "No authentication token available"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Add a test channel
            test_channel = {"channel_id": "-1001234567890", "last_message_id": 0}
            response = self.client.post("/api/channels", json=test_channel, headers=headers)
            assert response.status_code == 200
            
            # Get channels list
            response = self.client.get("/api/channels", headers=headers)
            assert response.status_code == 200
            channels = response.json()["channels"]
            assert test_channel["channel_id"] in channels
            
            # Remove channel
            response = self.client.delete(f"/api/channels/{test_channel['channel_id']}", headers=headers)
            assert response.status_code == 200
            
            # Verify channel was removed
            response = self.client.get("/api/channels", headers=headers)
            assert response.status_code == 200
            channels = response.json()["channels"]
            assert test_channel["channel_id"] not in channels
        except Exception as e:
            pytest.fail(f"Channel management test failed: {str(e)}")

    def test_07_scrape_settings(self):
        try:
            assert self.token is not None, "No authentication token available"
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get default settings
            response = self.client.get("/api/scrape-settings", headers=headers)
            assert response.status_code == 200
            assert "scrape_media" in response.json()
            
            # Update settings
            new_settings = {"scrape_media": False}
            response = self.client.post("/api/scrape-settings", json=new_settings, headers=headers)
            assert response.status_code == 200
            
            # Verify settings were updated
            response = self.client.get("/api/scrape-settings", headers=headers)
            assert response.status_code == 200
            assert response.json()["scrape_media"] == new_settings["scrape_media"]
        except Exception as e:
            pytest.fail(f"Scrape settings test failed: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])