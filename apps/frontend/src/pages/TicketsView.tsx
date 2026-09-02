import React, { useEffect, useState } from 'react';
import { Activity, CheckCircle, AlertCircle, Clock } from 'lucide-react';

interface Ticket {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  customer_id: string;
  customer_phone: string;
}

export default function TicketsView() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/crm/tickets')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setTickets(data);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <span className="badge ringing"><AlertCircle size={14} /> Open</span>;
      case 'IN_PROGRESS':
        return <span className="badge"><Clock size={14} /> In Progress</span>;
      case 'RESOLVED':
      case 'CLOSED':
        return <span className="badge" style={{ background: 'rgba(0, 255, 100, 0.1)', color: '#4ade80' }}><CheckCircle size={14} /> {status}</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'HIGH':
      case 'URGENT':
        return '#ef4444';
      case 'MEDIUM':
        return '#f59e0b';
      default:
        return 'var(--text-secondary)';
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2>Support Tickets</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Manage and track customer support issues raised by the AI or agents.</p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 48 }}>Loading tickets...</div>
      ) : tickets.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '48px 0' }}>
          <Activity size={48} color="var(--border-color)" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ color: 'var(--text-secondary)' }}>No tickets found</h3>
        </div>
      ) : (
        <div className="grid grid-cols-1" style={{ gap: 16 }}>
          {tickets.map(ticket => (
            <div key={ticket.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{ticket.title}</h3>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                    Customer Phone: <strong style={{ color: 'white' }}>{ticket.customer_phone}</strong> | Priority: <strong style={{ color: getPriorityColor(ticket.priority) }}>{ticket.priority}</strong>
                  </div>
                </div>
                <div>
                  {getStatusBadge(ticket.status)}
                </div>
              </div>
              
              <div style={{ background: 'rgba(0,0,0,0.2)', padding: 12, borderRadius: 8, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                {ticket.description || "No description provided."}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
