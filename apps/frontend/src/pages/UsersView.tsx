import React, { useEffect, useState } from 'react';
import { Users, UserPlus, ShieldAlert } from 'lucide-react';

export default function UsersView() {
  const [role, setRole] = useState<string>('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payloadBase64 = token.split('.')[1];
        const decodedJson = JSON.parse(atob(payloadBase64));
        setRole(decodedJson.role || '');
      } catch (e) {
        console.error("Token decode error");
      }
    }
  }, []);

  if (role !== 'SUPER_ADMIN' && role !== 'ADMIN') {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '64px 0' }}>
        <ShieldAlert size={48} color="var(--danger)" style={{ margin: '0 auto 16px' }} />
        <h2 style={{ color: 'var(--danger)' }}>Access Denied</h2>
        <p style={{ color: 'var(--text-secondary)' }}>You do not have permission to view User Management.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h2>User Management</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Manage Admins and Employees.</p>
        </div>
        <button style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          <UserPlus size={18} /> Invite User
        </button>
      </div>

      <div className="glass-panel">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Name</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Email</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Role</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {/* Mock Data for Phase 1 UI */}
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '16px' }}>John Admin</td>
              <td style={{ padding: '16px' }}>admin@vensora.com</td>
              <td style={{ padding: '16px' }}><span className="badge high">SUPER_ADMIN</span></td>
              <td style={{ padding: '16px' }}>Active</td>
            </tr>
            <tr>
              <td style={{ padding: '16px' }}>Alice Worker</td>
              <td style={{ padding: '16px' }}>alice@vensora.com</td>
              <td style={{ padding: '16px' }}><span className="badge ringing">EMPLOYEE</span></td>
              <td style={{ padding: '16px' }}>Active</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
