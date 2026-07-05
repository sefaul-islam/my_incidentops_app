/**
 * Application router with auth-protected routes.
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';

import LandingPage from './LandingPage';
import IncidentOpsHome from './Home';
import LoginPage from './LoginPage';
import OAuthCallback from './OAuthCallback';
import IncidentDetail from './IncidentDetail';
import PostMortemView from './PostMortemView';
import SettingsPage from './SettingsPage';
import NotFoundPage from './NotFoundPage';

/**
 * Protected route wrapper — redirects to /login if not authenticated.
 */
function ProtectedRoute({ children, requireAdmin = false }) {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback/:provider" element={<OAuthCallback />} />

          {/* Protected routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute><IncidentOpsHome /></ProtectedRoute>
          } />
          <Route path="/incidents" element={
            <ProtectedRoute><IncidentOpsHome /></ProtectedRoute>
          } />
          <Route path="/incidents/:id" element={
            <ProtectedRoute><IncidentDetail /></ProtectedRoute>
          } />
          <Route path="/postmortems" element={
            <ProtectedRoute><IncidentOpsHome /></ProtectedRoute>
          } />
          <Route path="/postmortems/:id" element={
            <ProtectedRoute><PostMortemView /></ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute requireAdmin><SettingsPage /></ProtectedRoute>
          } />

          {/* Catch-all */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}