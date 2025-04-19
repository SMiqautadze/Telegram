import unittest
import requests
import uuid
from datetime import datetime

class TestAuthAPI(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://backend-7443.cloud.serverless.com/api"  # Using public endpoint
        self.test_user = {
            "email": f"test_{uuid.uuid4()}@test.com",
            "password": "Test@123",
            "full_name": "Test User"
        }
        
    def test_1_register(self):
        """Test user registration"""
        print("\nTesting user registration...")
        response = requests.post(
            f"{self.base_url}/register",
            json=self.test_user
        )
        print(f"Registration response: {response.status_code}")
        print(f"Response body: {response.json()}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.test_user["email"])
        self.assertEqual(data["full_name"], self.test_user["full_name"])
        print("✅ Registration test passed")

    def test_2_login(self):
        """Test user login"""
        print("\nTesting user login...")
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
        )
        print(f"Login response: {response.status_code}")
        print(f"Response body: {response.json()}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        print("✅ Login test passed")

    def test_3_invalid_login(self):
        """Test invalid login credentials"""
        print("\nTesting invalid login...")
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.test_user["email"],
                "password": "wrongpassword"
            }
        )
        print(f"Invalid login response: {response.status_code}")
        self.assertEqual(response.status_code, 401)
        print("✅ Invalid login test passed")

if __name__ == '__main__':
    unittest.main(verbosity=2)
