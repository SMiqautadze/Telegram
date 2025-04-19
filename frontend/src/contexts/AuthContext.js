import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
      const response = await axios.post(`${BACKEND_URL}/login`, {
        email,
        password
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      return true;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
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

  const register = async (email, password, fullName) => {
    try {
      await axios.post(`${BACKEND_URL}/register`, {
        email,
        password,
        full_name: fullName
      });
      
      return login(email, password);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
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
