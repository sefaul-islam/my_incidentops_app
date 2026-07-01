/**
 * Authentication API service.
 */
import client from './client';

export const authAPI = {
  /**
   * Register a new user.
   */
  register(data) {
    return client.post('/auth/register/', data);
  },

  /**
   * Login with email and password.
   */
  login(email, password) {
    return client.post('/auth/login/', { email, password });
  },

  /**
   * Refresh JWT access token.
   */
  refreshToken(refreshToken) {
    return client.post('/auth/token/refresh/', { refresh: refreshToken });
  },

  /**
   * Get current user profile.
   */
  getMe() {
    return client.get('/auth/me/');
  },

  /**
   * Update current user profile.
   */
  updateMe(data) {
    return client.patch('/auth/me/', data);
  },

  /**
   * Exchange OAuth2 code for JWT tokens.
   */
  oauthCallback(provider, code) {
    return client.post('/auth/oauth/callback/', { provider, code });
  },

  /**
   * List all users (admin).
   */
  listUsers() {
    return client.get('/auth/users/');
  },

  /**
   * Update a user's role (admin).
   */
  updateUserRole(userId, role) {
    return client.patch(`/auth/users/${userId}/role/`, { role });
  },
};
