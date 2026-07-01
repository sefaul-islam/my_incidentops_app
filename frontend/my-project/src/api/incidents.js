/**
 * Incidents API service.
 */
import client from './client';

export const incidentsAPI = {
  /**
   * List all incidents with optional filters.
   */
  list(params = {}) {
    return client.get('/incidents/', { params });
  },

  /**
   * Get incident detail with timeline.
   */
  get(id) {
    return client.get(`/incidents/${id}/`);
  },

  /**
   * Create a new incident.
   */
  create(data) {
    return client.post('/incidents/', data);
  },

  /**
   * Update an incident.
   */
  update(id, data) {
    return client.patch(`/incidents/${id}/`, data);
  },

  /**
   * Acknowledge an incident.
   */
  acknowledge(id, message = '') {
    return client.post(`/incidents/${id}/acknowledge/`, { message });
  },

  /**
   * Move incident to investigating.
   */
  investigate(id, message = '') {
    return client.post(`/incidents/${id}/investigate/`, { message });
  },

  /**
   * Move incident to mitigating.
   */
  mitigate(id, message = '') {
    return client.post(`/incidents/${id}/mitigate/`, { message });
  },

  /**
   * Resolve an incident.
   */
  resolve(id, message = '') {
    return client.post(`/incidents/${id}/resolve/`, { message });
  },

  /**
   * Add a comment to an incident.
   */
  comment(id, message) {
    return client.post(`/incidents/${id}/comment/`, { message });
  },

  /**
   * Generate or get a post-mortem for an incident.
   */
  getPostMortem(id) {
    return client.get(`/incidents/${id}/generate_postmortem/`);
  },

  generatePostMortem(id) {
    return client.post(`/incidents/${id}/generate_postmortem/`);
  },

  /**
   * List all post-mortems.
   */
  listPostMortems() {
    return client.get('/postmortems/');
  },
};
