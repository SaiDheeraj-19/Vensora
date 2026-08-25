import React from 'react';
import { Contact, Search, Star } from 'lucide-react';

export default function ContactsView() {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h2>CRM & Contacts</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Synced Customer Profiles and AI-extracted Long Term Facts.</p>
        </div>
        <div style={{ position: 'relative', width: 250 }}>
          <Search size={16} color="var(--text-secondary)" style={{ position: 'absolute', top: 14, left: 12 }} />
          <input 
            type="text" 
            placeholder="Search phone number..." 
            style={{ paddingLeft: 36, marginBottom: 0 }}
          />
        </div>
      </div>

      <div className="glass-panel">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Customer Name</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Phone Number</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>AI Facts (Memory)</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 500 }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {/* Mock Data for Phase 1 UI */}
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '16px', fontWeight: 500 }}>Jane Doe</td>
              <td style={{ padding: '16px' }}>+1 (555) 019-2834</td>
              <td style={{ padding: '16px' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  - Prefers morning calls<br/>
                  - Needs accessibility support
                </div>
              </td>
              <td style={{ padding: '16px' }}><span className="badge high" style={{ display: 'flex', alignItems: 'center', gap: 4, width: 'fit-content' }}><Star size={14}/> VIP</span></td>
            </tr>
            <tr>
              <td style={{ padding: '16px', fontWeight: 500 }}>Michael Smith</td>
              <td style={{ padding: '16px' }}>+1 (555) 888-1122</td>
              <td style={{ padding: '16px' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  - No active shipments
                </div>
              </td>
              <td style={{ padding: '16px' }}><span className="badge ringing">Standard</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
