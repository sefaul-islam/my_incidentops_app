/**
 * IncidentOps Dashboard — Kanban board with real-time updates.
 * Enhanced version of the original Home.jsx, wired to live API + WebSocket.
 */
import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useIncidents } from '../hooks/useIncidents';
import { incidentsAPI } from '../api/incidents';
import { Sidebar } from '../components/ui/Sidebar';
import { Header } from '../components/ui/Header';
import { Badge } from '../components/ui/Badge';
import { Avatar } from '../components/ui/Avatar';
import { Modal } from '../components/ui/Modal';
import { timeAgo, getStatusLabel } from '../utils/helpers';

const BOARD_COLUMNS = [
  { status: 'DECLARED', title: 'Triage / Backlog', color: 'rose' },
  { status: 'ACKNOWLEDGED', title: 'Acknowledged', color: 'blue' },
  { status: 'INVESTIGATING', title: 'Investigating', color: 'violet' },
  { status: 'MITIGATING', title: 'Mitigating / Fixing', color: 'amber' },
  { status: 'RESOLVED', title: 'Resolved', color: 'emerald' },
];

export default function IncidentOpsHome() {
  const navigate = useNavigate();
  const { isResponder, user } = useAuth();
  const { groupedByStatus, loading, error, isConnected, refetch } = useIncidents();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [newIncident, setNewIncident] = useState({
    title: '', description: '', severity: 'SEV2', assignee: '',
  });
  const [creating, setCreating] = useState(false);

  const handleCreateIncident = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const payload = { ...newIncident };
      if (!payload.assignee) delete payload.assignee;
      await incidentsAPI.create(payload);
      setShowCreateModal(false);
      setNewIncident({ title: '', description: '', severity: 'SEV2', assignee: '' });
      refetch();
    } catch (err) {
      console.error('Create incident failed:', err);
    } finally {
      setCreating(false);
    }
  };

  const filterIncidents = useCallback((incidents) => {
    if (!searchQuery.trim()) return incidents;
    const q = searchQuery.toLowerCase();
    return incidents.filter(i =>
      i.title?.toLowerCase().includes(q) ||
      i.incident_id?.toLowerCase().includes(q) ||
      i.assignee_name?.toLowerCase().includes(q)
    );
  }, [searchQuery]);

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />

      <main className="flex-1 flex flex-col overflow-hidden">
        <Header
          title="Active Incidents"
          subtitle={`${Object.values(groupedByStatus).flat().length} total`}
          isConnected={isConnected}
        >
          {/* Search */}
          <div className="relative hidden sm:block">
            <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search incidents..."
              className="pl-9 pr-4 py-2 w-64 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          {/* Create Button */}
          {isResponder && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-violet-600 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all duration-200 hover:scale-105"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Declare Incident
            </button>
          )}
        </Header>

        {/* Kanban Board */}
        <div className="flex-1 overflow-x-auto overflow-y-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <svg className="animate-spin h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-rose-400 mb-2">{error}</p>
                <button onClick={refetch} className="text-blue-400 hover:text-blue-300 text-sm">
                  Try again
                </button>
              </div>
            </div>
          ) : (
            <div className="inline-flex h-full p-6 gap-4 items-start">
              {BOARD_COLUMNS.map((column) => {
                const incidents = filterIncidents(groupedByStatus[column.status] || []);
                return (
                  <div
                    key={column.status}
                    className="w-80 flex-shrink-0 flex flex-col max-h-full rounded-xl bg-slate-900/30 border border-white/5 backdrop-blur-sm"
                  >
                    {/* Column Header */}
                    <div className="p-3.5 flex items-center justify-between border-b border-white/5">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full bg-${column.color}-400`} />
                        <h2 className="text-sm font-semibold text-slate-200">{column.title}</h2>
                      </div>
                      <span className="text-xs font-medium text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">
                        {incidents.length}
                      </span>
                    </div>

                    {/* Column Cards */}
                    <div className="p-2 overflow-y-auto space-y-2 flex-1 scrollbar-thin scrollbar-thumb-slate-700">
                      {incidents.map((incident) => (
                        <div
                          key={incident.id || incident.incident_id}
                          onClick={() => navigate(`/incidents/${incident.id}`)}
                          className="bg-slate-800/50 p-3.5 rounded-lg border border-white/5 hover:border-blue-500/30 hover:bg-slate-800/80 cursor-pointer transition-all duration-200 group"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-mono text-slate-500 group-hover:text-blue-400 transition-colors">
                              {incident.incident_id}
                            </span>
                            <Badge
                              type="severity"
                              value={incident.severity}
                              size="xs"
                              pulse={incident.severity === 'SEV1' && incident.status === 'DECLARED'}
                            />
                          </div>
                          <p className="text-sm font-medium text-slate-200 leading-snug mb-3 group-hover:text-white transition-colors">
                            {incident.title}
                          </p>
                          <div className="flex items-center justify-between pt-2 border-t border-white/5">
                            <div className="flex items-center text-xs text-slate-500">
                              <svg className="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {timeAgo(incident.created_at)}
                            </div>
                            <div className="flex items-center gap-1.5">
                              {incident.assignee_name === 'Unassigned' ? (
                                <span className="text-xs text-slate-600 italic">Unassigned</span>
                              ) : (
                                <>
                                  <span className="text-xs text-slate-400 font-medium">
                                    {incident.assignee_name}
                                  </span>
                                  <Avatar name={incident.assignee_name} size="xs" />
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}

                      {incidents.length === 0 && (
                        <div className="text-center py-8">
                          <p className="text-xs text-slate-600">No incidents</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Create Incident Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Declare New Incident"
        size="md"
      >
        <form onSubmit={handleCreateIncident} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Title</label>
            <input
              type="text"
              value={newIncident.title}
              onChange={(e) => setNewIncident(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
              placeholder="Brief incident title"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Description</label>
            <textarea
              value={newIncident.description}
              onChange={(e) => setNewIncident(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all resize-none"
              placeholder="Describe the incident..."
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Severity</label>
            <select
              value={newIncident.severity}
              onChange={(e) => setNewIncident(prev => ({ ...prev, severity: e.target.value }))}
              className="w-full px-4 py-2.5 bg-slate-800 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
            >
              <option value="SEV1">Sev-1 (Critical)</option>
              <option value="SEV2">Sev-2 (High)</option>
              <option value="SEV3">Sev-3 (Medium)</option>
              <option value="SEV4">Sev-4 (Low)</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creating || !newIncident.title.trim()}
              className="px-5 py-2 bg-gradient-to-r from-blue-500 to-violet-600 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-500/20 transition-all duration-200 disabled:opacity-50 hover:scale-105"
            >
              {creating ? 'Creating...' : 'Declare Incident'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}