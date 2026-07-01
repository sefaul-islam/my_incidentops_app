/**
 * Settings page for admin user/team management.
 */
import React, { useState, useEffect } from 'react';
import { authAPI } from '../api/auth';
import { useAuth } from '../context/AuthContext';
import { Sidebar } from '../components/ui/Sidebar';
import { Header } from '../components/ui/Header';
import { Avatar } from '../components/ui/Avatar';
import { Badge } from '../components/ui/Badge';

export default function SettingsPage() {
  const { user: currentUser, isAdmin } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authAPI.listUsers()
      .then(({ data }) => setUsers(data.results || data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    try {
      await authAPI.updateUserRole(userId, newRole);
      setUsers(prev =>
        prev.map(u => u.id === userId ? { ...u, role: newRole } : u)
      );
    } catch (err) {
      console.error('Role update failed:', err);
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header title="Settings" subtitle="Team & User Management" />

        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-6">

            {/* User Management */}
            <div className="bg-slate-900/50 border border-white/5 rounded-xl backdrop-blur-sm">
              <div className="px-6 py-4 border-b border-white/5">
                <h2 className="text-lg font-semibold text-white">Team Members</h2>
                <p className="text-sm text-slate-400 mt-1">Manage user roles and permissions.</p>
              </div>

              {loading ? (
                <div className="p-8 text-center">
                  <svg className="animate-spin h-6 w-6 text-blue-400 mx-auto" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {users.map(u => (
                    <div key={u.id} className="px-6 py-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors">
                      <div className="flex items-center gap-3">
                        <Avatar name={u.full_name || u.username} avatarUrl={u.avatar_url} size="md" />
                        <div>
                          <p className="text-sm font-medium text-white">{u.full_name || u.username}</p>
                          <p className="text-xs text-slate-500">{u.email}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {u.is_on_call && (
                          <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                            On-Call
                          </span>
                        )}
                        {isAdmin && u.id !== currentUser?.id ? (
                          <select
                            value={u.role}
                            onChange={(e) => handleRoleChange(u.id, e.target.value)}
                            className="bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                          >
                            <option value="ADMIN">Admin</option>
                            <option value="RESPONDER">Responder</option>
                            <option value="VIEWER">Viewer</option>
                          </select>
                        ) : (
                          <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                            u.role === 'ADMIN' ? 'bg-violet-500/20 text-violet-300' :
                            u.role === 'RESPONDER' ? 'bg-blue-500/20 text-blue-300' :
                            'bg-slate-500/20 text-slate-300'
                          }`}>
                            {u.role}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* RBAC Info */}
            <div className="bg-slate-900/50 border border-white/5 rounded-xl p-6 backdrop-blur-sm">
              <h3 className="text-lg font-semibold text-white mb-4">Role Permissions</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-2 pr-4 text-slate-400 font-medium">Permission</th>
                      <th className="text-center py-2 px-4 text-violet-400 font-medium">Admin</th>
                      <th className="text-center py-2 px-4 text-blue-400 font-medium">Responder</th>
                      <th className="text-center py-2 px-4 text-slate-400 font-medium">Viewer</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-300">
                    {[
                      ['Create Incidents', true, true, false],
                      ['Acknowledge/Update', true, true, false],
                      ['Resolve Incidents', true, true, false],
                      ['View Incidents', true, true, true],
                      ['Generate Post-Mortem', true, true, false],
                      ['Manage Users', true, false, false],
                      ['View Analytics', true, true, true],
                      ['Configure On-Call', true, false, false],
                    ].map(([perm, admin, resp, viewer], idx) => (
                      <tr key={idx} className="border-b border-white/5">
                        <td className="py-2.5 pr-4">{perm}</td>
                        <td className="text-center py-2.5">{admin ? '✅' : '❌'}</td>
                        <td className="text-center py-2.5">{resp ? '✅' : '❌'}</td>
                        <td className="text-center py-2.5">{viewer ? '✅' : '❌'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
