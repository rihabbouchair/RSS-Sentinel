import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Subscribe from './pages/Subscribe';
import DiscoverFeeds from './pages/DiscoverFeeds';
import Login from './pages/Login';
import Register from './pages/Register';
import Landing from './pages/Landing';

function AppContent() {
  const [selectedTopic, setSelectedTopic] = useState(null);
  const { token } = useAuth();

  const AppLayout = ({ children }) => (
    <>
      <div className="mesh" aria-hidden="true">
        <div className="mesh-orb m1"></div>
        <div className="mesh-orb m2"></div>
        <div className="mesh-orb m3"></div>
      </div>
      <div className="app-shell" style={{ display: 'flex', height: '100vh', background: 'transparent', color: 'var(--text-primary)' }}>
        <Sidebar selectedTopic={selectedTopic} onTopicSelect={setSelectedTopic} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <Navbar />
          {children}
        </div>
      </div>
    </>
  );

  return (
    <Routes>
      <Route path="/" element={token ? (
        <ProtectedRoute>
          <AppLayout><Dashboard selectedTopic={selectedTopic} /></AppLayout>
        </ProtectedRoute>
      ) : <Landing />} />
      <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/register" element={token ? <Navigate to="/" replace /> : <Register />} />
      <Route path="/settings" element={
        <ProtectedRoute>
          <AppLayout><Subscribe /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/discover" element={
        <ProtectedRoute>
          <AppLayout><DiscoverFeeds /></AppLayout>
        </ProtectedRoute>
      } />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider><AppContent /></AuthProvider>
    </BrowserRouter>
  );
}
