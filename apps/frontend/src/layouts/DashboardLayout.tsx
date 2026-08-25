import React, { useEffect, useState } from 'react';
import { Outlet, Navigate, NavLink, useNavigate } from 'react-router-dom';
import { Activity, Book, Users, LogOut, Shield } from 'lucide-react';

export default function DashboardLayout() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const [role, setRole] = useState<string>('');

  useEffect(() => {
    if (!token) return;
    
    // Very basic JWT decode for Phase 1 to get the role (without bringing in extra dependencies)
    try {
      const payloadBase64 = token.split('.')[1];
      const decodedJson = JSON.parse(atob(payloadBase64));
      setRole(decodedJson.role || '');
    } catch (e) {
      console.error("Failed to decode token");
    }
  }, [token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="dashboard-container animate-fade-in">
      <nav className="sidebar">
        <div style={{ marginBottom: 32, padding: '0 16px' }}>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '1.25rem' }}>
            <div style={{ background: 'var(--accent-primary)', padding: 6, borderRadius: 8 }}>
              <Shield size={20} color="white" />
            </div>
            Vensora
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 4, textTransform: 'uppercase' }}>
            {role.replace('_', ' ')}
          </p>
        </div>

        <NavLink to="/live-calls" className={({ isActive }) => isActive ? 'active' : ''}>
          <Activity size={18} /> Live Calls
        </NavLink>
        
        <NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>
          <Book size={18} /> Call History
        </NavLink>
        
        <NavLink to="/contacts" className={({ isActive }) => isActive ? 'active' : ''}>
          <Users size={18} /> CRM & Contacts
        </NavLink>
        
        {/* Permission-aware routing: Only SUPER_ADMIN sees Knowledge Base & Users */}
        {role === 'SUPER_ADMIN' && (
          <>
            <NavLink to="/knowledge-base" className={({ isActive }) => isActive ? 'active' : ''}>
              <Book size={18} /> Knowledge Base
            </NavLink>
            <NavLink to="/users" className={({ isActive }) => isActive ? 'active' : ''}>
              <Users size={18} /> User Management
            </NavLink>
          </>
        )}

        <div style={{ marginTop: 'auto' }}>
          <button 
            onClick={handleLogout} 
            style={{ 
              background: 'transparent', 
              color: 'var(--text-secondary)', 
              textAlign: 'left', 
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 12
            }}
          >
            <LogOut size={18} /> Sign Out
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
