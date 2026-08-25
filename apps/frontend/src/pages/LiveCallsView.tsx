import React, { useEffect, useState, useRef } from 'react';
import { PhoneCall, ShieldAlert, CheckCircle } from 'lucide-react';

interface CallEvent {
  call_id: string;
  state: string;
  caller_id: string;
  timestamp: string;
}

export default function LiveCallsView() {
  const [activeCalls, setActiveCalls] = useState<Record<string, CallEvent>>({});
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to the backend WebSocket
    ws.current = new WebSocket('ws://localhost:8000/api/v1/telephony/ws/live-calls');

    ws.current.onmessage = (event) => {
      try {
        const payload: CallEvent = JSON.parse(event.data);
        setActiveCalls(prev => ({
          ...prev,
          [payload.call_id]: payload
        }));
      } catch (e) {
        console.error("Failed to parse websocket message", e);
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const calls = Object.values(activeCalls);

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2>Live Network Traffic</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Monitoring active Asterisk SIP channels in real-time.</p>
      </div>

      <div className="grid grid-cols-3">
        {calls.length === 0 ? (
          <div className="glass-panel" style={{ gridColumn: 'span 3', textAlign: 'center', padding: '48px 0' }}>
            <PhoneCall size={48} color="var(--border-color)" style={{ margin: '0 auto 16px' }} />
            <h3 style={{ color: 'var(--text-secondary)' }}>No active calls</h3>
          </div>
        ) : (
          calls.map((call) => (
            <div key={call.call_id} className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div>
                  <h4 style={{ margin: 0 }}>{call.caller_id}</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>ID: {call.call_id.substring(0, 8)}</p>
                </div>
                {call.state === 'ESCALATING' ? (
                  <span className="badge low">
                    <ShieldAlert size={14} /> Escalating
                  </span>
                ) : (
                  <span className="badge ringing">
                    <div className="pulse-dot"></div> {call.state}
                  </span>
                )}
              </div>
              
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Last Update: {new Date(call.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
