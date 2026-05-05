import { useState } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login as apiLogin } from '../api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login, token } = useAuth();
  const navigate = useNavigate();

  if (token) return <Navigate to="/" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await apiLogin(username, password);
      login(result.token, result.user);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = {
    width: '100%', padding: '10px 14px',
    background: 'rgba(255,255,255,0.06)',
    border: '0.5px solid var(--border)',
    borderRadius: '8px', color: 'var(--text-primary)',
    fontSize: '13px', outline: 'none',
    transition: 'border-color 0.15s',
    fontFamily: 'Plus Jakarta Sans, system-ui, sans-serif',
    backdropFilter: 'var(--blur)',
    WebkitBackdropFilter: 'var(--blur)',
  };

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-base)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      {/* Background glow */}
      <div style={{
        position: 'fixed', top: '30%', left: '50%', transform: 'translate(-50%, -50%)',
        width: '400px', height: '400px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(124,111,255,0.12) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <div className="gc" style={{
        width: '100%', maxWidth: '380px',
        padding: '36px 32px',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '44px', height: '44px', borderRadius: '10px',
            background: 'rgba(124,111,255,0.18)',
            border: '0.5px solid rgba(124,111,255,0.35)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 12px',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-light)" strokeWidth="2.5">
              <path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1" fill="var(--accent-light)" stroke="none"/>
            </svg>
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: '600', color: 'var(--text-primary)', margin: '0 0 4px' }}>
            RSS Sentinel
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Username
            </label>
            <input
              type="text" value={username}
              onChange={(e) => setUsername(e.target.value)}
              required placeholder="Enter username"
              style={inputStyle}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              required placeholder="Enter password"
              style={inputStyle}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>

          {error && (
            <div style={{
              padding: '10px 12px', borderRadius: '8px', fontSize: '12px',
              background: 'rgba(255,85,114,0.1)', color: 'var(--negative)',
              border: '0.5px solid rgba(255,85,114,0.25)',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !username || !password}
            style={{
              width: '100%', padding: '11px',
              background: loading || !username || !password ? 'rgba(255,255,255,0.05)' : 'var(--accent)',
              border: '0.5px solid rgba(124,111,255,0.35)', borderRadius: '8px',
              color: loading || !username || !password ? 'var(--text-muted)' : 'white',
              fontSize: '13px', fontWeight: '500',
              cursor: loading || !username || !password ? 'not-allowed' : 'pointer',
              transition: 'background 0.15s, opacity 0.15s',
              fontFamily: 'JetBrains Mono, monospace',
            }}
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '12px', color: 'var(--text-muted)' }}>
          No account?{' '}
          <Link to="/register" style={{ color: 'var(--accent-light)', textDecoration: 'none' }}>
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}
