/**
 * Incident detail page with timeline, actions, and real-time updates.
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { incidentsAPI } from '../api/incidents';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { Badge } from '../components/ui/Badge';
import { Avatar } from '../components/ui/Avatar';
import { Modal } from '../components/ui/Modal';
import { Sidebar } from '../components/ui/Sidebar';
import { Header } from '../components/ui/Header';
import { timeAgo, formatDuration, getStatusLabel } from '../utils/helpers';

export default function IncidentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isResponder } = useAuth();
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [actionLoading, setActionLoading] = useState('');
  const [showPostMortemModal, setShowPostMortemModal] = useState(false);
  const { lastMessage, isConnected, subscribeToIncident } = useWebSocket();

  // Fetch incident
  useEffect(() => {
    incidentsAPI.get(id)
      .then(({ data }) => {
        setIncident(data);
        subscribeToIncident(data.incident_id);
      })
      .catch(() => navigate('/'))
      .finally(() => setLoading(false));
  }, [id, navigate, subscribeToIncident]);

  // Handle real-time updates
  useEffect(() => {
    if (!lastMessage || !incident) return;
    if (lastMessage.type === 'incident_updated' && lastMessage.incident?.id === incident.id) {
      // Refetch full detail
      incidentsAPI.get(id).then(({ data }) => setIncident(data));
    }
    if (lastMessage.type === 'incident_comment' && lastMessage.incident_id === incident.incident_id) {
      incidentsAPI.get(id).then(({ data }) => setIncident(data));
    }
  }, [lastMessage, incident, id]);

  const handleAction = async (action) => {
    setActionLoading(action);
    try {
      let response;
      switch (action) {
        case 'acknowledge': response = await incidentsAPI.acknowledge(id); break;
        case 'investigate': response = await incidentsAPI.investigate(id); break;
        case 'mitigate': response = await incidentsAPI.mitigate(id); break;
        case 'resolve': response = await incidentsAPI.resolve(id); break;
        default: return;
      }
      setIncident(response.data);
    } catch (err) {
      console.error(`Action ${action} failed:`, err);
    } finally {
      setActionLoading('');
    }
  };

  const handleComment = async (e) => {
    e.preventDefault();
    if (!comment.trim()) return;
    try {
      await incidentsAPI.comment(id, comment);
      setComment('');
      const { data } = await incidentsAPI.get(id);
      setIncident(data);
    } catch (err) {
      console.error('Comment failed:', err);
    }
  };

  const handleGeneratePostMortem = async () => {
    try {
      const { data } = await incidentsAPI.generatePostMortem(id);
      navigate(`/postmortems/${data.id}`);
    } catch (err) {
      console.error('Post-mortem generation failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-slate-950">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <svg className="animate-spin h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      </div>
    );
  }

  if (!incident) return null;

  const nextActions = {
    DECLARED: [{ key: 'acknowledge', label: 'Acknowledge', color: 'from-blue-500 to-blue-600' }],
    ACKNOWLEDGED: [{ key: 'investigate', label: 'Start Investigation', color: 'from-violet-500 to-violet-600' }],
    INVESTIGATING: [{ key: 'mitigate', label: 'Begin Mitigation', color: 'from-amber-500 to-amber-600' }],
    MITIGATING: [{ key: 'resolve', label: 'Mark Resolved', color: 'from-emerald-500 to-emerald-600' }],
    RESOLVED: [],
    POST_MORTEM: [],
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header title={incident.incident_id} subtitle={incident.title} isConnected={isConnected}>
          <Link
            to="/"
            className="text-sm text-slate-400 hover:text-white transition-colors"
          >
            ← Back to Board
          </Link>
        </Header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Incident Header Card */}
          <div className="bg-slate-900/50 border border-white/5 rounded-xl p-6 backdrop-blur-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-white mb-2">{incident.title}</h2>
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <Badge type="severity" value={incident.severity} pulse={incident.severity === 'SEV1' && incident.status !== 'RESOLVED'} />
                  <Badge type="status" value={incident.status} />
                </div>
                {incident.description && (
                  <p className="text-slate-400 text-sm leading-relaxed">{incident.description}</p>
                )}
              </div>

              <div className="flex flex-col gap-2 text-sm text-slate-400">
                <div>Created: <span className="text-white">{timeAgo(incident.created_at)}</span></div>
                {incident.acknowledged_at && (
                  <div>Acknowledged: <span className="text-white">{timeAgo(incident.acknowledged_at)}</span></div>
                )}
                {incident.resolved_at && (
                  <div>Resolved: <span className="text-white">{timeAgo(incident.resolved_at)}</span></div>
                )}
                {incident.resolved_at && incident.created_at && (
                  <div>Duration: <span className="text-white font-semibold">{formatDuration(incident.created_at, incident.resolved_at)}</span></div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            {isResponder && (
              <div className="flex flex-wrap gap-3 mt-6 pt-4 border-t border-white/5">
                {(nextActions[incident.status] || []).map(action => (
                  <button
                    key={action.key}
                    onClick={() => handleAction(action.key)}
                    disabled={actionLoading === action.key}
                    className={`px-4 py-2 bg-gradient-to-r ${action.color} text-white font-medium rounded-lg shadow-lg transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:hover:scale-100`}
                  >
                    {actionLoading === action.key ? 'Processing...' : action.label}
                  </button>
                ))}
                {incident.status === 'RESOLVED' && (
                  <button
                    onClick={handleGeneratePostMortem}
                    className="px-4 py-2 bg-gradient-to-r from-slate-600 to-slate-700 text-white font-medium rounded-lg shadow-lg transition-all duration-200 hover:scale-105"
                  >
                    Generate Post-Mortem
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="bg-slate-900/50 border border-white/5 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold text-white mb-4">Timeline</h3>

            {/* Comment Input */}
            {isResponder && (
              <form onSubmit={handleComment} className="mb-6 flex gap-3">
                <input
                  type="text"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Add a comment..."
                  className="flex-1 px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                />
                <button
                  type="submit"
                  disabled={!comment.trim()}
                  className="px-4 py-2.5 bg-blue-500/20 text-blue-400 font-medium rounded-xl hover:bg-blue-500/30 transition-all disabled:opacity-30"
                >
                  Send
                </button>
              </form>
            )}

            {/* Timeline Entries */}
            <div className="space-y-4">
              {(incident.updates || []).map((update, idx) => (
                <div key={update.id || idx} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full mt-1.5 ${
                      update.update_type === 'STATUS_CHANGE' ? 'bg-blue-400' :
                      update.update_type === 'ESCALATION' ? 'bg-rose-400' :
                      'bg-slate-600'
                    }`} />
                    {idx < incident.updates.length - 1 && (
                      <div className="w-px flex-1 bg-white/5 mt-1" />
                    )}
                  </div>
                  <div className="flex-1 pb-4">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-white">
                        {update.author_name || 'System'}
                      </span>
                      <span className="text-xs text-slate-500">{timeAgo(update.created_at)}</span>
                      {update.update_type === 'STATUS_CHANGE' && (
                        <span className="text-xs text-blue-400 bg-blue-400/10 px-1.5 py-0.5 rounded">
                          {getStatusLabel(update.old_status)} → {getStatusLabel(update.new_status)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-300">{update.message}</p>
                  </div>
                </div>
              ))}
              {(!incident.updates || incident.updates.length === 0) && (
                <p className="text-sm text-slate-500 text-center py-4">No timeline entries yet.</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
