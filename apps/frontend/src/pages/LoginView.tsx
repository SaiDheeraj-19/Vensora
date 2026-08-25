import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';

export default function LoginView() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        if (data.detail === "MUST_CHANGE_PASSWORD") {
          // Pass the temporary token to the next view
          navigate('/change-password', { state: { tempToken: data.token } });
        } else {
          setError(data.detail || 'Login failed');
        }
        return;
      }

      localStorage.setItem('token', data.access_token);
      navigate('/');
    } catch (err) {
      setError('Network error');
    }
  };

  return (
    <>
      <div className="mesh-bg">
        <div className="mesh-orb orb-1"></div>
        <div className="mesh-orb orb-2"></div>
      </div>
      <div className="dashboard-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="glass-panel animate-fade-in" style={{ width: 400, textAlign: 'center' }}>
        <div style={{ marginBottom: 24 }}>
          <img src="/logo.png" alt="Vensora AI Logo" style={{ height: 64, objectFit: 'contain', margin: '0 auto' }} />
          <p style={{ color: 'var(--text-secondary)', marginTop: 16 }}>Sign in to manage operations</p>
        </div>
        
        {error && <div style={{ color: 'var(--danger)', marginBottom: 16, fontSize: '0.9rem' }}>{error}</div>}
        
        <form onSubmit={handleLogin}>
          <input 
            type="email" 
            placeholder="Email Address" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            required 
          />
          <input 
            type="password" 
            placeholder="Password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            required 
          />
          <button type="submit">Authenticate</button>
        </form>
      </div>
    </div>
    </>
  );
}
