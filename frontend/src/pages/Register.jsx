import { useState } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { register as apiRegister } from '../api';

const TOPICS = ['AI', 'Tech', 'Politics', 'Sport', 'Economy', 'Science'];

const topicColors = {
  AI: '#a78bfa', Tech: '#38bdf8', Politics: '#fb923c',
  Sport: '#fb7185', Economy: '#4ade80', Science: '#34d399',
};

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [wantsDigest, setWantsDigest] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login, token } = useAuth();
  const navigate = useNavigate();

  if (token) return <Navigate to="/" replace />;

  function toggleTopic(topic) {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (selectedTopics.length === 0) { setError('Please select at least one topic'); return; }
    setLoading(true); setError(null);
    try {
      const result = await apiRegister({ username, password, email: email || null, topics: selectedTopics, wants_email_digest: wantsDigest });
      login(result.token, result.user);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = {
    width: '100%', padding: '10px 14px',
    background: 'rgba(255,255,255,0.05)', border: '0.5px solid var(--border)',
    borderRadius: '8px', color: 'var(--text-primary)', fontSize: '13px',
    outline: 'none', transition: 'border-color 0.15s', fontFamily: 'inherit',
  };

  const canSubmit = !loading && username && password && selectedTopics.length > 0;

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-base)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
      <div style={{ position: 'fixed', top: '30%', left: '50%', transform: 'translate(-50%,-50%)', width: '400px', height: '400px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)', pointerEvents: 'none' }} />

      <div style={{ width: '100%', maxWidth: '420px', background: 'var(--bg-surface)', border: '0.5px solid var(--border)', borderRadius: '16px', padding: '32px' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 10px' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1" fill="white" stroke="none"/></svg>
          </div>
          <h1 style={{ fontSize: '18px', fontWeight: '600', color: 'var(--text-primary)', margin: '0 0 4px' }}>Create Account</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>Set up your RSS Sentinel feed</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Username */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Username <span style={{ color: '#fb7185' }}>*</span>
            </label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} required placeholder="Choose a username" style={inputStyle} onFocus={e => e.target.style.borderColor='#7c3aed'} onBlur={e => e.target.style.borderColor='var(--border)'} />
          </div>
          {/* Password */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Password <span style={{ color: '#fb7185' }}>*</span>
            </label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="Choose a password" style={inputStyle} onFocus={e => e.target.style.borderColor='#7c3aed'} onBlur={e => e.target.style.borderColor='var(--border)'} />
          </div>
          {/* Email */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Email <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>(optional — for daily digest)</span>
            </label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="your@email.com" style={inputStyle} onFocus={e => e.target.style.borderColor='#7c3aed'} onBlur={e => e.target.style.borderColor='var(--border)'} />
          </div>

          {/* Topics */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
              Topics <span style={{ color: '#fb7185' }}>*</span>
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              {TOPICS.map((topic) => {
                const selected = selectedTopics.includes(topic);
                const color = topicColors[topic] || '#a78bfa';
                return (
                  <label key={topic} style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px 12px', borderRadius: '8px', cursor: 'pointer',
                    background: selected ? `${color}12` : 'rgba(255,255,255,0.03)',
                    border: selected ? `0.5px solid ${color}40` : '0.5px solid var(--border)',
                    transition: 'all 0.15s',
                  }}>
                    <div style={{
                      width: '16px', height: '16px', borderRadius: '4px', flexShrink: 0,
                      background: selected ? color : 'transparent',
                      border: selected ? `1.5px solid ${color}` : '1.5px solid var(--border)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s',
                    }}>
                      {selected && <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>}
                    </div>
                    <input type="checkbox" checked={selected} onChange={() => toggleTopic(topic)} style={{ display: 'none' }} />
                    <span style={{ fontSize: '12px', color: selected ? color : 'var(--text-secondary)', fontWeight: selected ? '500' : '400' }}>{topic}</span>
                    <span style={{ marginLeft: 'auto', width: '7px', height: '7px', borderRadius: '50%', background: color, opacity: selected ? 1 : 0.3 }}></span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Digest toggle */}
          {email && (
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '8px', cursor: 'pointer', background: 'rgba(255,255,255,0.03)', border: '0.5px solid var(--border)' }}>
              <div style={{ width: '16px', height: '16px', borderRadius: '4px', flexShrink: 0, background: wantsDigest ? '#7c3aed' : 'transparent', border: wantsDigest ? '1.5px solid #7c3aed' : '1.5px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {wantsDigest && <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>}
              </div>
              <input type="checkbox" checked={wantsDigest} onChange={e => setWantsDigest(e.target.checked)} style={{ display: 'none' }} />
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Receive daily email digest</span>
            </label>
          )}

          {error && (
            <div style={{ padding: '10px 12px', borderRadius: '8px', fontSize: '12px', background: 'rgba(251,113,133,0.1)', color: '#fb7185', border: '0.5px solid rgba(251,113,133,0.25)' }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={!canSubmit} style={{
            width: '100%', padding: '11px', background: canSubmit ? 'linear-gradient(135deg,#6366f1,#8b5cf6)' : 'rgba(255,255,255,0.05)',
            border: 'none', borderRadius: '8px', color: canSubmit ? 'white' : 'var(--text-muted)',
            fontSize: '13px', fontWeight: '500', cursor: canSubmit ? 'pointer' : 'not-allowed', fontFamily: 'inherit',
          }}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: '#a78bfa', textDecoration: 'none' }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
