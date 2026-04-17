import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import api, { gmail } from './utils/api';
import AuthForm from './components/AuthForm';
import EmailForm from './components/EmailForm';
import HistoryViewer from './components/HistoryViewer';
import OAuthCallback from './components/OAuthCallback';
import ModelRegistry from './components/ModelRegistry';
import 'react-toastify/dist/ReactToastify.css';
import './styles/tailwind.css';

// Layout components
const Navigation = ({ onLogout }) => {
  const [gmailStatus, setGmailStatus] = useState({ connected: false, email: null });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;
    let mounted = true;
    gmail.status()
      .then(resp => {
        if (!mounted) return;
        const data = resp.data || {};
        setGmailStatus({ connected: !!data.connected, email: data.email || null });
      })
      .catch(() => {
        if (!mounted) return;
        setGmailStatus({ connected: false, email: null });
      });
    return () => { mounted = false; };
  }, []);

  const handleConnect = async () => {
    try {
      const resp = await gmail.start();
      const url = resp.data?.auth_url;
      if (url) window.location.href = url;
    } catch (err) {
      console.error('Failed to start Gmail OAuth', err);
    }
  };

  const handleDisconnect = async () => {
    try {
      await gmail.disconnect();
      setGmailStatus({ connected: false, email: null });
    } catch (err) {
      console.error('Failed to disconnect Gmail', err);
    }
  };

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-indigo-600">AI Email Assistant</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <a
                href="/email"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                Compose
              </a>
              <a
                href="/history"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                History
              </a>
              <a
                href="/models"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                Models
              </a>
            </div>
          </div>
          <div className="flex items-center">
            {gmailStatus.connected ? (
              <div className="flex items-center mr-4">
                <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">{gmailStatus.email || 'Gmail'}</span>
                <button onClick={handleDisconnect} className="ml-2 text-xs text-red-600">Disconnect</button>
              </div>
            ) : (
              <button onClick={handleConnect} className="mr-4 inline-flex items-center px-3 py-1 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">Connect Gmail</button>
            )}

            <button
              onClick={onLogout}
              className="border-transparent text-gray-500 hover:text-gray-700 inline-flex items-center px-4 py-2 border text-sm font-medium rounded-md"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

const ProtectedLayout = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = () => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
    setLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation onLogout={handleLogout} />
      <main className="py-10">
        <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
};

const PublicOnlyRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  
  if (token) {
    return <Navigate to="/email" replace />;
  }

  return children;
};

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route
            path="/auth"
            element={
              <PublicOnlyRoute>
                <div className="min-h-screen bg-gray-50">
                  <AuthForm />
                </div>
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/email"
            element={
              <ProtectedLayout>
                <EmailForm />
              </ProtectedLayout>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedLayout>
                <HistoryViewer />
              </ProtectedLayout>
            }
          />
          <Route
            path="/oauth/callback"
            element={<OAuthCallback />}
          />
          <Route
            path="/models"
            element={
              <ProtectedLayout>
                <ModelRegistry />
              </ProtectedLayout>
            }
          />
          <Route path="/" element={<Navigate to="/email" replace />} />
        </Routes>
        <ToastContainer
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="light"
        />
      </div>
    </Router>
  );
};

export default App;
