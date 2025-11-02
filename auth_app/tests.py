from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework import status
from django.urls import reverse

class AuthAPITests(APITestCase):
    """
    Test suite for the Authentication API endpoints.
    """

    def setUp(self):
        """
        Set up test data and URLs.
        """
        # URLs
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.logout_url = reverse('logout')
        self.refresh_url = reverse('token_refresh')

        # Test user data
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        # Create a user for login tests
        self.user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )

    # =================================================================
    # == Registration Tests (/api/register/)
    # =================================================================
    def test_register_success(self):
        """
        Ensure a new user can be registered successfully.
        """
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123",
            "confirmed_password": "newpassword123"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"detail": "User created successfully!"})
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        """
        Ensure registration fails if passwords do not match.
        """
        data = {
            "username": "anotheruser",
            "email": "another@example.com",
            "password": "password1",
            "confirmed_password": "password2"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =================================================================
    # == Login Tests (/api/login/)
    # =================================================================
    def test_login_success(self):
        """
        Ensure a user can log in and receive the correct response and cookies.
        """
        data = {
            "username": self.user_data['username'],
            "password": self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_response = {
            "detail": "Login successfully!",
            "user": {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email
            }
        }
        self.assertEqual(response.data, expected_response)
        
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_invalid_credentials(self):
        """
        Ensure login fails with invalid credentials.
        """
        data = {
            "username": self.user_data['username'],
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # =================================================================
    # == Logout Tests (/api/logout/)
    # =================================================================
    def test_logout_success(self):
        """
        Ensure a logged-in user can log out successfully.
        """
        # First, log in to set the cookies
        self.client.post(self.login_url, {
            "username": self.user_data['username'],
            "password": self.user_data['password']
        }, format='json')

        # Now, attempt to log out
        response = self.client.post(self.logout_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
        })
        
        # Check if cookies are cleared
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_logout_not_authenticated(self):
        """
        Ensure a non-authenticated user cannot log out.
        """
        response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # =================================================================
    # == Token Refresh Tests (/api/token/refresh/)
    # =================================================================
    def test_token_refresh_success(self):
        """
        Ensure the access token can be refreshed successfully.
        """
        login_response = self.client.post(self.login_url, {
            "username": self.user_data['username'],
            "password": self.user_data['password']
        }, format='json')
        
        # Ensure login was successful and we have a cookie
        self.assertIn('refresh_token', login_response.cookies)

        # Attempt to refresh the token
        refresh_response = self.client.post(self.refresh_url, {}, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertEqual(refresh_response.data['detail'], "Token refreshed")
        self.assertIn('access', refresh_response.data)
        self.assertIn('access_token', refresh_response.cookies)

    def test_token_refresh_no_token(self):
        """
        Ensure token refresh fails if no refresh token is provided.
        """
        response = self.client.post(self.refresh_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
