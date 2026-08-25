import React, { useEffect, useState } from 'react';
import { Contact, Search, Star, UserPlus } from 'lucide-react';

interface Customer {
  id: string;
  phone_number: string;
  name: string;
  metadata_tags: {
    vip?: boolean;
    facts?: string[];
  };
}

export default function ContactsView() {
  const [contacts, setContacts] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/crm/contacts', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    .then(res => res.json())
    .then(data => {
      setContacts(data);
      setLoading(false);
    })
    .catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h2>CRM & Contacts</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Synced Customer Profiles and AI-extracted Long Term Facts.</p>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <div style={{ position: 'relative', width: 250 }}>
            <Search size={16} color="var(--text-secondary)" style={{ position: 'absolute', top: 14, left: 12 }} />
            <input 
              type="text" 
              placeholder="Search phone number..." 
              style={{ paddingLeft: 36, marginBottom: 0 }}
            />
          </div>
          <button style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            <UserPlus size={16} /> New Contact
          </button>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
        <table className="premium-table">
          <thead>
            <tr>
              <th>Customer Name</th>
              <th>Phone Number</th>
              <th>AI Facts (Memory)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '32px' }}>
                  <div className="pulse-dot" style={{ margin: '0 auto' }}></div>
                  <p style={{ color: 'var(--text-secondary)', marginTop: 12 }}>Loading Contacts...</p>
                </td>
              </tr>
            ) : contacts.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '32px' }}>
                  <p style={{ color: 'var(--text-secondary)' }}>No contacts found.</p>
                </td>
              </tr>
            ) : (
              contacts.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 500 }}>{c.name}</td>
                  <td>{c.phone_number}</td>
                  <td>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {(c.metadata_tags?.facts || []).map((fact, idx) => (
                        <div key={idx}>- {fact}</div>
                      ))}
                      {(!c.metadata_tags?.facts || c.metadata_tags.facts.length === 0) && (
                        <span>No facts extracted yet</span>
                      )}
                    </div>
                  </td>
                  <td>
                    {c.metadata_tags?.vip ? (
                      <span className="badge high"><Star size={14}/> VIP</span>
                    ) : (
                      <span className="badge ringing">Standard</span>
                    )}
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
