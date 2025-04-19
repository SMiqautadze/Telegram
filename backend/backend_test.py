import unittest
import requests
import os
from datetime import datetime

class TestTelegramScraperAPI(unittest.TestCase):
    def setUp(self):
        self.base_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        self.test_user = {
            "email": "test2@example.com",
            "password": "Test@123",
            "full_name": "Test User"
        }
        self.token = None

    def test_01_register(self):
        """Test user registration"""
        response = requests.post(
            f"{self.base_url}/api/register",
            json=self.test_user
        )
        print(f"Register response: {response.status_code}")
        print(f"Register response body: {response.json() if response.ok else response.text}")
        
        if response.status_code == 400 and "Email already registered" in response.text:
            print("User already exists, proceeding with login")
            return
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.test_user["email"])

    def test_02_login(self):
        """Test user login"""
        response = requests.post(
            f"{self.base_url}/api/login",
            json={
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
        )
        print(f"Login response: {response.status_code}")
        print(f"Login response body: {response.json() if response.ok else response.text}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.token = data["access_token"]

    def test_03_get_user_profile(self):
        """Test getting user profile"""
        if not self.token:
            self.test_02_login()
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/api/me",
            headers=headers
        )
        print(f"Profile response: {response.status_code}")
        print(f"Profile response body: {response.json() if response.ok else response.text}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.test_user["email"])

if __name__ == '__main__':
    unittest.main()