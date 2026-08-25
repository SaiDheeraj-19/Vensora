import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';

export default function ChangePasswordView() {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  
  // The temp token passed from the login failure
  const tempToken = location.state?.tempToken;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tempToken) {
      setError("Session expired. Please log in again.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/change-password', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tempToken}`
        },
        body: JSON.stringify({ new_password: newPassword })
      });
      
      if (!res.ok) throw new Error('Password change failed');
      
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      navigate('/');
    } catch (err) {
      setError('Failed to securely change password.');
    }
  };

  return (
    <div className="dashboard-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div className="glass-panel animate-fade-in" style={{ width: 400, textAlign: 'center' }}>
        <div style={{ marginBottom: 24 }}>
          <ShieldAlert size={48} color="var(--danger)" style={{ margin: '0 auto' }} />
          <h2 style={{ marginTop: 16 }}>Security Enforced</h2>
          <p style={{ color: 'var(--text-secondary)' }}>You must change your initial password before accessing Vensora.</p>
        </div>
        
        {error && <div style={{ color: 'var(--danger)', marginBottom: 16, fontSize: '0.9rem' }}>{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <input 
            type="password" 
            placeholder="New Secure Password" 
            value={newPassword} 
            onChange={(e) => setNewPassword(e.target.value)} 
            required 
            minLength={12}
          />
          <input 
            type="password" 
            placeholder="Confirm Password" 
            value={confirmPassword} 
            onChange={(e) => setConfirmPassword(e.target.value)} 
            required 
          />
          <button type="submit">Secure & Continue</button>
        </form>
      </div>
    </div>
  );
}
