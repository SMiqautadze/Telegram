import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ChannelManager from './pages/ChannelManager';
import ChannelData from './pages/ChannelData';
import TelegramSetup from './pages/TelegramSetup';
import PasswordReset from './pages/PasswordReset';
import NewPassword from './pages/NewPassword';
import LoadingSpinner from './components/LoadingSpinner';

// Contexts
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return children;
};

function AppContent() {
  const { isAuthenticated } = useAuth();

  return (
    <Router>
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} />
            <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} />
            <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} />
            <Route path="/reset-password" element={<PasswordReset />} />
            <Route path="/new-password" element={<NewPassword />} />
            
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/channel-manager" element={
              <ProtectedRoute>
                <ChannelManager />
              </ProtectedRoute>
            } />
            
            <Route path="/channel-data/:channelId" element={
              <ProtectedRoute>
                <ChannelData />
              </ProtectedRoute>
            } />
            
            <Route path="/telegram-setup" element={
              <ProtectedRoute>
                <TelegramSetup />
              </ProtectedRoute>
            } />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
