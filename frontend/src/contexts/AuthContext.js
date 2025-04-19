import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Safely access the backend URL from environment variables
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          const response = await axios.get(`${BACKEND_URL}/me`, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          
          setCurrentUser(response.data);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Error fetching user:', error);
          logout();
        }
      }
      setLoading(false);
    };

    fetchUser();
  }, [token]);

  const login = async (email, password) => {
    try {
      setLoading(true);
      console.log('Login request to:', `${BACKEND_URL}/login`, { email, password });
      const response = await axios.post(`${BACKEND_URL}/login`, { email, password });
      console.log('Login response:', response.data);
      const token = response.data.access_token;
      localStorage.setItem('token', token);
      setToken(token);
      await fetchUserData();
      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      console.error('Login error details:', error.response?.data, error.response?.status);
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Login failed. Please check your credentials.'
      };
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (googleToken) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/google-login`, {
        token: googleToken
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      return true;
    } catch (error) {
      console.error('Google login error:', error);
      throw error;
    }
  };

  // Fetch user data (profile)
  const fetchUserData = async () => {
    try {
      if (!token) {
        console.log('No token available for fetchUserData');
        return null;
      }
      
      console.log('Fetching user data from:', `${BACKEND_URL}/me`);
      const response = await axios.get(`${BACKEND_URL}/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('User data response:', response.data);
      setUser(response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching user data:', error);
      console.error('Error details:', error.response?.data, error.response?.status);
      // If the error is 401 Unauthorized, the token might be invalid or expired
      if (error.response && error.response.status === 401) {
        logout();
      }
      return null;
    }
  };

  const register = async (email, password, fullName) => {
    try {
      console.log('Register request to:', `${BACKEND_URL}/register`, { email, password, full_name: fullName });
      const response = await axios.post(`${BACKEND_URL}/register`, {
        email,
        password,
        full_name: fullName
      });
      
      console.log('Register response:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Registration error:', error);
      console.error('Registration error details:', error.response?.data, error.response?.status);
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Registration failed. Please try again.'
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setCurrentUser(null);
    setIsAuthenticated(false);
  };

  const resetPassword = async (email) => {
    try {
      await axios.post(`${BACKEND_URL}/reset-password`, { email });
      return true;
    } catch (error) {
      console.error('Password reset error:', error);
      throw error;
    }
  };

  const setNewPassword = async (token, password) => {
    try {
      await axios.post(`${BACKEND_URL}/set-new-password`, { token, password });
      return true;
    } catch (error) {
      console.error('Set new password error:', error);
      throw error;
    }
  };

  const value = {
    currentUser,
    token,
    isAuthenticated,
    loading,
    login,
    loginWithGoogle,
    register,
    logout,
    resetPassword,
    setNewPassword
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
