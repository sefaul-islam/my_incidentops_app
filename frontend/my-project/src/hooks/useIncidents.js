/**
 * Custom hook for incident data management.
 * Integrates API calls with WebSocket real-time updates.
 */
import { useState, useEffect, useCallback } from 'react';
import { incidentsAPI } from '../api/incidents';
import { useWebSocket } from './useWebSocket';

export function useIncidents(filters = {}) {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { lastMessage, isConnected } = useWebSocket();

  // Fetch incidents from API
  const fetchIncidents = useCallback(async () => {
    try {
      setLoading(true);
      const { data } = await incidentsAPI.list(filters);
      setIncidents(data.results || data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch incidents');
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  // Initial fetch
  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  // Handle real-time WebSocket updates
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === 'incident_created') {
      setIncidents(prev => [lastMessage.incident, ...prev]);
    } else if (lastMessage.type === 'incident_updated') {
      setIncidents(prev =>
        prev.map(inc =>
          inc.id === lastMessage.incident.id ? lastMessage.incident : inc,
        ),
      );
    }
  }, [lastMessage]);

  // Group incidents by status (for Kanban view)
  const groupedByStatus = {
    DECLARED: incidents.filter(i => i.status === 'DECLARED'),
    ACKNOWLEDGED: incidents.filter(i => i.status === 'ACKNOWLEDGED'),
    INVESTIGATING: incidents.filter(i => i.status === 'INVESTIGATING'),
    MITIGATING: incidents.filter(i => i.status === 'MITIGATING'),
    RESOLVED: incidents.filter(i => i.status === 'RESOLVED'),
    POST_MORTEM: incidents.filter(i => i.status === 'POST_MORTEM'),
  };

  return {
    incidents,
    groupedByStatus,
    loading,
    error,
    isConnected,
    refetch: fetchIncidents,
  };
}
