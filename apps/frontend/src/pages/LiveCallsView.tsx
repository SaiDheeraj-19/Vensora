import React, { useEffect, useState, useRef } from 'react';
import { PhoneCall, ShieldAlert, MessageSquare } from 'lucide-react';

interface CallEvent {
  call_id: string;
  state: string;
  caller_id: string;
  timestamp: string;
}

interface TranscriptEvent {
  speaker: string;
  text: string;
  timestamp: string;
}

export default function LiveCallsView() {
  const [activeCalls, setActiveCalls] = useState<Record<string, CallEvent>>({});
  const [transcripts, setTranscripts] = useState<Record<string, TranscriptEvent[]>>({});
  const [selectedCall, setSelectedCall] = useState<string | null>(null);
  const [bargeMessage, setBargeMessage] = useState("");
  
  const ws = useRef<WebSocket | null>(null);
  const transcriptContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/api/v1/telephony/ws/live-calls');

    ws.current.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "transcript" || payload.event === "barge_in") {
          // Both transcript and barge_in share the same format essentially for the UI (barge_in is added as transcript by backend)
          if (payload.event === "transcript") {
              setTranscripts(prev => ({
                ...prev,
                [payload.call_id]: [...(prev[payload.call_id] || []), payload]
              }));
          }
        } else if (payload.state) {
          setActiveCalls(prev => {
             const newCalls = { ...prev, [payload.call_id]: payload };
             if (payload.state === "COMPLETED") {
                 delete newCalls[payload.call_id];
             }
             return newCalls;
          });
        }
      } catch (e) {
        console.error("Failed to parse websocket message", e);
      }
    };

    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);
  
  useEffect(() => {
      if (transcriptContainerRef.current) {
          transcriptContainerRef.current.scrollTop = transcriptContainerRef.current.scrollHeight;
      }
  }, [transcripts, selectedCall]);

  const sendBargeIn = () => {
      if (!bargeMessage.trim() || !selectedCall || !ws.current) return;
      ws.current.send(JSON.stringify({
          action: "barge_in",
          call_id: selectedCall,
          message: bargeMessage
      }));
      setBargeMessage("");
  };

  const calls = Object.values(activeCalls);
  const selectedTranscripts = selectedCall ? transcripts[selectedCall] || [] : [];

  return (
    <div style={{ display: 'flex', gap: '24px', height: 'calc(100vh - 120px)' }}>
      <div style={{ flex: '1', overflowY: 'auto', paddingRight: '12px' }}>
        <div style={{ marginBottom: 32 }}>
          <h2>Live Network Traffic</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Monitoring active Asterisk SIP channels in real-time.</p>
        </div>

        <div className="grid grid-cols-1" style={{ gap: '16px' }}>
          {calls.length === 0 ? (
            <div className="glass-panel" style={{ textAlign: 'center', padding: '48px 0' }}>
              <PhoneCall size={48} color="var(--border-color)" style={{ margin: '0 auto 16px' }} />
              <h3 style={{ color: 'var(--text-secondary)' }}>No active calls</h3>
            </div>
          ) : (
            calls.map((call) => (
              <div 
                key={call.call_id} 
                className="glass-panel" 
                style={{ 
                    cursor: 'pointer', 
                    border: selectedCall === call.call_id ? '2px solid rgba(255,255,255,0.5)' : '1px solid var(--border-color)'
                }}
                onClick={() => setSelectedCall(call.call_id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                  <div>
                    <h4 style={{ margin: 0 }}>{call.caller_id}</h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>ID: {call.call_id.substring(0, 8)}</p>
                  </div>
                  {call.state === 'ESCALATING' ? (
                    <span className="badge low"><ShieldAlert size={14} /> Escalating</span>
                  ) : (
                    <span className="badge ringing"><div className="pulse-dot"></div> {call.state}</span>
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
      
      {selectedCall && (
        <div className="glass-panel" style={{ flex: '1.5', display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0 }}>Call Details: {selectedCall}</h3>
              <button onClick={() => setSelectedCall(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>Close</button>
          </div>
          
          <div ref={transcriptContainerRef} style={{ flex: 1, overflowY: 'auto', marginBottom: '16px', padding: '16px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
            {selectedTranscripts.length === 0 && (
                <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '20px' }}>
                    <MessageSquare style={{ margin: '0 auto 10px', opacity: 0.5 }} />
                    No transcripts yet.
                </div>
            )}
            {selectedTranscripts.map((t, idx) => (
              <div key={idx} style={{ marginBottom: 12, textAlign: t.speaker === 'customer' ? 'left' : 'right' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: 4 }}>{t.speaker.toUpperCase()}</div>
                <div style={{ 
                  display: 'inline-block', 
                  padding: '10px 14px', 
                  borderRadius: '12px',
                  background: t.speaker === 'customer' ? 'rgba(255,255,255,0.1)' : t.speaker === 'admin' ? 'rgba(255,50,50,0.3)' : 'rgba(0,180,255,0.2)',
                  color: 'white',
                  maxWidth: '80%',
                  textAlign: 'left'
                }}>
                  {t.text}
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <input 
              type="text" 
              placeholder="Type a message to inject into the live call..." 
              value={bargeMessage}
              onChange={e => setBargeMessage(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendBargeIn()}
              style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'transparent', color: 'white' }}
            />
            <button onClick={sendBargeIn} style={{ padding: '12px 24px', borderRadius: '8px', background: 'var(--primary-color)', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}>
              Barge In
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
