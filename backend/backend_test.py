import pytest
import requests
import os
from datetime import datetime

class TestTelegramScraperAPI:
    BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://your-backend-url.com')
    TEST_USER = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
    TEST_TELEGRAM_CREDS = {
        "api_id": 20223845,
        "api_hash": "2d9943c0c4b2b37998a6868f385f3f32",
        "phone": "+1234567890"
    }
    TEST_CHANNEL = {
        "channel_id": "test_channel",
        "last_message_id": 0
    }

    def setup_method(self):
        self.token = None
        # Clean up any existing test user
        self.cleanup_test_user()

    def cleanup_test_user(self):
        """Helper method to clean up test user if exists"""
        try:
            # Try to login and delete if exists
            response = requests.post(
                f"{self.BASE_URL}/api/login",
                json={"email": self.TEST_USER["email"], "password": self.TEST_USER["password"]}
            )
            if response.status_code == 200:
                # Would need a delete user endpoint in production
                pass
        except:
            pass

    def test_01_register_user(self):
        """Test user registration"""
        response = requests.post(
            f"{self.BASE_URL}/api/register",
            json=self.TEST_USER
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["email"] == self.TEST_USER["email"]

    def test_02_login_user(self):
        """Test user login"""
        response = requests.post(
            f"{self.BASE_URL}/api/login",
            json={
                "email": self.TEST_USER["email"],
                "password": self.TEST_USER["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        self.token = data["access_token"]

    def test_03_get_user_profile(self):
        """Test getting user profile"""
        if not self.token:
            self.test_02_login_user()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.BASE_URL}/api/me",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == self.TEST_USER["email"]

    def test_04_set_telegram_credentials(self):
        """Test setting Telegram credentials"""
        if not self.token:
            self.test_02_login_user()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.BASE_URL}/api/telegram-credentials",
            headers=headers,
            json=self.TEST_TELEGRAM_CREDS
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_05_get_telegram_credentials(self):
        """Test getting Telegram credentials"""
        if not self.token:
            self.test_02_login_user()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.BASE_URL}/api/telegram-credentials",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["api_id"] == self.TEST_TELEGRAM_CREDS["api_id"]
        assert data["api_hash"] == self.TEST_TELEGRAM_CREDS["api_hash"]
        assert data["phone"] == self.TEST_TELEGRAM_CREDS["phone"]

    def test_06_add_channel(self):
        """Test adding a channel"""
        if not self.token:
            self.test_02_login_user()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.BASE_URL}/api/channels",
            headers=headers,
            json=self.TEST_CHANNEL
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_07_get_channels(self):
        """Test getting channels list"""
        if not self.token:
            self.test_02_login_user()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.BASE_URL}/api/channels",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert self.TEST_CHANNEL["channel_id"] in data["channels"]

    def test_08_remove_channel(self):
        """Test removing a channel"""
        if not self.token:
            self.test_02_login_user()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.delete(
            f"{self.BASE_URL}/api/channels/{self.TEST_CHANNEL['channel_id']}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
