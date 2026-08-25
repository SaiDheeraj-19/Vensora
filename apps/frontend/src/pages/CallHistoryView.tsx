import React, { useEffect, useState } from 'react';
import { History, PlayCircle, Clock } from 'lucide-react';

interface CallRecord {
  id: string;
  caller_id: string;
  duration: number;
  status: string;
  timestamp: string | null;
  recording_url: string | null;
}

export default function CallHistoryView() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/calls/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    .then(res => res.json())
    .then(data => {
      setCalls(data);
      setLoading(false);
    })
    .catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const formatTimestamp = (ts: string | null) => {
    if (!ts) return "Unknown";
    return new Intl.DateTimeFormat('en-US', { 
      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' 
    }).format(new Date(ts));
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2>Call History & Recordings</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Review past interactions and listen to audio recordings.</p>
      </div>

      <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
        <table className="premium-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Caller ID</th>
              <th>Duration</th>
              <th>Routing</th>
              <th>Recording</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '32px' }}>
                  <div className="pulse-dot" style={{ margin: '0 auto' }}></div>
                  <p style={{ color: 'var(--text-secondary)', marginTop: 12 }}>Loading Call History...</p>
                </td>
              </tr>
            ) : calls.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '32px' }}>
                  <p style={{ color: 'var(--text-secondary)' }}>No calls have been recorded yet.</p>
                </td>
              </tr>
            ) : (
              calls.map((call) => (
                <tr key={call.id}>
                  <td>{formatTimestamp(call.timestamp)}</td>
                  <td style={{ fontWeight: 500 }}>{call.caller_id}</td>
                  <td>
                    <Clock size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }}/> 
                    {formatDuration(call.duration)}
                  </td>
                  <td>
                    {call.status.toLowerCase().includes('escalated') ? (
                      <span className="badge low">{call.status}</span>
                    ) : (
                      <span className="badge high">{call.status}</span>
                    )}
                  </td>
                  <td>
                    <button 
                      onClick={() => alert(`In Phase 2, this will play audio from ${call.recording_url || 'S3'}`)}
                      style={{ width: 'auto', padding: '6px 12px', background: 'var(--bg-surface)', display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem' }}
                    >
                      <PlayCircle size={16} /> Play
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
