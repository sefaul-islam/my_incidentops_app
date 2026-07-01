/**
 * Post-mortem viewer with XAI insight cards and anomaly visualizations.
 */
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { incidentsAPI } from '../api/incidents';
import { Sidebar } from '../components/ui/Sidebar';
import { Header } from '../components/ui/Header';
import { Badge } from '../components/ui/Badge';
import { timeAgo } from '../utils/helpers';

export default function PostMortemView() {
  const { id } = useParams();
  const [postmortem, setPostmortem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    incidentsAPI.listPostMortems()
      .then(({ data }) => {
        const results = data.results || data;
        const pm = results.find(p => String(p.id) === String(id));
        setPostmortem(pm);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

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

  if (!postmortem) {
    return (
      <div className="flex h-screen bg-slate-950">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center text-slate-400">
          Post-mortem not found.
        </div>
      </div>
    );
  }

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'insights', label: `XAI Insights (${(postmortem.anomalies || []).length})` },
    { key: 'timeline', label: 'Timeline' },
    { key: 'logs', label: 'Log Highlights' },
    { key: 'actions', label: 'Action Items' },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header title={`Post-Mortem: ${postmortem.incident_id}`}>
          <Link to="/" className="text-sm text-slate-400 hover:text-white transition-colors">
            ← Back
          </Link>
        </Header>

        <div className="flex-1 overflow-y-auto">
          {/* Confidence Banner */}
          {postmortem.xai_confidence != null && (
            <div className="mx-6 mt-6 bg-gradient-to-r from-blue-500/10 via-violet-500/10 to-blue-500/10 border border-blue-500/20 rounded-xl p-4 flex items-center gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400">
                  {(postmortem.xai_confidence * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-slate-400">XAI Confidence</div>
              </div>
              <div className="flex-1">
                <div className="w-full bg-slate-700 rounded-full h-2.5">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-violet-500 h-2.5 rounded-full transition-all duration-1000"
                    style={{ width: `${(postmortem.xai_confidence * 100).toFixed(0)}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="px-6 mt-6 border-b border-white/5">
            <div className="flex gap-1">
              {tabs.map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all ${
                    activeTab === tab.key
                      ? 'bg-slate-800/50 text-white border-b-2 border-blue-500'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-6 space-y-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <>
                <Section title="Summary">
                  <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{postmortem.summary}</p>
                </Section>
                <Section title="Root Cause">
                  <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{postmortem.root_cause}</p>
                </Section>
                <Section title="Impact">
                  <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{postmortem.impact}</p>
                </Section>
              </>
            )}

            {/* XAI Insights Tab */}
            {activeTab === 'insights' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {(postmortem.anomalies || []).map((card, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-900/50 border border-white/5 rounded-xl p-5 hover:border-white/10 transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="text-sm font-semibold text-white">{card.title}</h4>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                        card.severity === 'critical' ? 'bg-rose-500/20 text-rose-300' :
                        card.severity === 'warning' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-slate-500/20 text-slate-300'
                      }`}>
                        {card.confidence_label}
                      </span>
                    </div>

                    {/* Confidence Bar */}
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-slate-500 mb-1">
                        <span>Confidence</span>
                        <span>{(card.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-700 ${
                            card.confidence > 0.7 ? 'bg-rose-500' :
                            card.confidence > 0.4 ? 'bg-amber-500' :
                            'bg-blue-500'
                          }`}
                          style={{ width: `${(card.confidence * 100).toFixed(0)}%` }}
                        />
                      </div>
                    </div>

                    <p className="text-sm text-slate-400 mb-3">{card.description}</p>

                    {/* Feature Importance */}
                    {card.features && card.features.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-white/5">
                        <p className="text-xs text-slate-500 mb-2 font-medium">Contributing Factors</p>
                        {card.features.map((feat, fidx) => (
                          <div key={fidx} className="flex items-center gap-2 mb-1">
                            <div className="w-20 bg-slate-700 rounded-full h-1">
                              <div
                                className="bg-blue-400 h-1 rounded-full"
                                style={{ width: `${(feat.importance * 100).toFixed(0)}%` }}
                              />
                            </div>
                            <span className="text-xs text-slate-400 truncate">{feat.description}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {card.recommendation && (
                      <div className="mt-3 pt-3 border-t border-white/5">
                        <p className="text-xs text-emerald-400">
                          💡 {card.recommendation}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
                {(!postmortem.anomalies || postmortem.anomalies.length === 0) && (
                  <p className="text-sm text-slate-500 col-span-2 text-center py-8">
                    No XAI insights available.
                  </p>
                )}
              </div>
            )}

            {/* Timeline Tab */}
            {activeTab === 'timeline' && (
              <Section title="Incident Timeline">
                <div className="space-y-3">
                  {(postmortem.timeline_data || []).map((entry, idx) => (
                    <div key={idx} className="flex gap-3 items-start">
                      <div className="flex flex-col items-center">
                        <div className={`w-2.5 h-2.5 rounded-full mt-1.5 ${
                          entry.type === 'INCIDENT_DECLARED' ? 'bg-rose-400' :
                          entry.type === 'INCIDENT_RESOLVED' ? 'bg-emerald-400' :
                          entry.type === 'STATUS_CHANGE' ? 'bg-blue-400' :
                          'bg-slate-600'
                        }`} />
                        {idx < (postmortem.timeline_data || []).length - 1 && (
                          <div className="w-px flex-1 bg-white/5 mt-1" />
                        )}
                      </div>
                      <div className="flex-1 pb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500 font-mono">
                            {new Date(entry.timestamp).toLocaleString()}
                          </span>
                          <span className="text-xs text-slate-400">{entry.author}</span>
                        </div>
                        <p className="text-sm text-slate-300 mt-0.5">{entry.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Log Highlights Tab */}
            {activeTab === 'logs' && (
              <Section title="Log Highlights">
                <div className="space-y-2">
                  {(postmortem.log_highlights || []).map((log, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-900/80 border border-white/5 rounded-lg p-3 font-mono text-xs"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          log.category === 'crash' || log.category === 'memory'
                            ? 'bg-rose-500/20 text-rose-300'
                            : log.category === 'timeout' || log.category === 'error'
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-slate-500/20 text-slate-300'
                        }`}>
                          {log.category?.toUpperCase()}
                        </span>
                        <span className="text-slate-500">Line {log.line_number}</span>
                      </div>
                      <p className="text-slate-300 break-all">{log.line}</p>
                    </div>
                  ))}
                  {(!postmortem.log_highlights || postmortem.log_highlights.length === 0) && (
                    <p className="text-sm text-slate-500 text-center py-8">No log highlights available.</p>
                  )}
                </div>
              </Section>
            )}

            {/* Action Items Tab */}
            {activeTab === 'actions' && (
              <Section title="Action Items">
                <div className="space-y-3">
                  {(postmortem.action_items || []).map((item, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-900/50 border border-white/5 rounded-lg p-4 flex items-start gap-3"
                    >
                      <span className={`text-xs px-2 py-0.5 rounded font-bold mt-0.5 ${
                        item.priority === 'P1'
                          ? 'bg-rose-500/20 text-rose-300'
                          : 'bg-amber-500/20 text-amber-300'
                      }`}>
                        {item.priority}
                      </span>
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-white">{item.title}</h4>
                        <p className="text-sm text-slate-400 mt-1">{item.action}</p>
                      </div>
                      <span className="text-xs text-slate-500 bg-slate-700/50 px-2 py-0.5 rounded">
                        {item.status}
                      </span>
                    </div>
                  ))}
                  {(!postmortem.action_items || postmortem.action_items.length === 0) && (
                    <p className="text-sm text-slate-500 text-center py-8">No action items generated.</p>
                  )}
                </div>
              </Section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-slate-900/50 border border-white/5 rounded-xl p-5 backdrop-blur-sm">
      <h3 className="text-base font-semibold text-white mb-3">{title}</h3>
      {children}
    </div>
  );
}
