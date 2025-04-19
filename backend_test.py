import unittest
import requests
import json
from datetime import datetime

class TelegramScraperAPITest(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8001/api"
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
        print("\nTesting user registration...")
        response = requests.post(
            f"{self.base_url}/register",
            json=self.test_user
        )
        print(f"Registration response: {response.status_code}")
        if response.status_code == 400:
            print("User already exists, proceeding with login")
        else:
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["email"], self.test_user["email"])

    def test_02_login(self):
        """Test user login"""
        print("\nTesting user login...")
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.token = data["access_token"]
        print("Login successful")

    def test_03_set_telegram_credentials(self):
        """Test setting Telegram credentials"""
        print("\nTesting Telegram credentials setup...")
        if not self.token:
            self.test_02_login()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/telegram-credentials",
            json=self.telegram_creds,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("Telegram credentials set successfully")

    def test_04_get_telegram_credentials(self):
        """Test getting Telegram credentials"""
        print("\nTesting get Telegram credentials...")
        if not self.token:
            self.test_02_login()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/telegram-credentials",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["api_id"], self.telegram_creds["api_id"])
        print("Retrieved Telegram credentials successfully")

    def test_05_channel_management(self):
        """Test channel management"""
        print("\nTesting channel management...")
        if not self.token:
            self.test_02_login()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Add a test channel
        test_channel = {
            "channel_id": "test_channel_1",
            "last_message_id": 0
        }
        
        # Add channel
        response = requests.post(
            f"{self.base_url}/channels",
            json=test_channel,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("Added channel successfully")

        # Get channels
        response = requests.get(
            f"{self.base_url}/channels",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(test_channel["channel_id"], data["channels"])
        print("Retrieved channels successfully")

        # Remove channel
        response = requests.delete(
            f"{self.base_url}/channels/{test_channel['channel_id']}",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("Removed channel successfully")

    def test_06_scrape_settings(self):
        """Test scrape settings"""
        print("\nTesting scrape settings...")
        if not self.token:
            self.test_02_login()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get default settings
        response = requests.get(
            f"{self.base_url}/scrape-settings",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("Retrieved scrape settings successfully")

        # Update settings
        new_settings = {"scrape_media": False}
        response = requests.post(
            f"{self.base_url}/scrape-settings",
            json=new_settings,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("Updated scrape settings successfully")

if __name__ == '__main__':
    unittest.main(verbosity=2)
