import React from 'react';
import { History, PlayCircle, Clock } from 'lucide-react';

export default function CallHistoryView() {
  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2>Call History & Recordings</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Review past interactions and listen to audio recordings.</p>
      </div>

      <div className="glass-panel">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Timestamp</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Caller ID</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Duration</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Routing</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Recording</th>
            </tr>
          </thead>
          <tbody>
            {/* Mock Data for Phase 1 UI */}
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '16px' }}>Today, 10:45 AM</td>
              <td style={{ padding: '16px', fontWeight: 500 }}>+1 (555) 019-2834</td>
              <td style={{ padding: '16px' }}><Clock size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }}/> 4m 12s</td>
              <td style={{ padding: '16px' }}><span className="badge high">AI Handled</span></td>
              <td style={{ padding: '16px' }}>
                <button style={{ width: 'auto', padding: '6px 12px', background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem' }}>
                  <PlayCircle size={16} /> Play
                </button>
              </td>
            </tr>
            <tr>
              <td style={{ padding: '16px' }}>Today, 09:12 AM</td>
              <td style={{ padding: '16px', fontWeight: 500 }}>+1 (555) 888-1122</td>
              <td style={{ padding: '16px' }}><Clock size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }}/> 1m 05s</td>
              <td style={{ padding: '16px' }}><span className="badge low">Escalated</span></td>
              <td style={{ padding: '16px' }}>
                <button style={{ width: 'auto', padding: '6px 12px', background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem' }}>
                  <PlayCircle size={16} /> Play
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
