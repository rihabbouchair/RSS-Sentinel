import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const location = useLocation();
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const initials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : 'U';

  return (
    <div style={{
      background: 'var(--bg-surface)',
      borderBottom: '0.5px solid var(--border)',
      padding: '12px 24px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    }}>
      {/* Page title */}
      <div>
        <div style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
          {location.pathname === '/' ? 'Dashboard' : 'Settings'}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {location.pathname === '/' ? 'Real-time news sentiment analysis' : 'Manage your preferences & feeds'}
        </div>
      </div>

      {/* Right */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Theme switch */}
        <button
          onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          style={{
          width: '32px', height: '32px', borderRadius: '8px',
          background: 'rgba(255,255,255,0.05)', border: '0.5px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', position: 'relative',
        }}
        >
          {theme === 'dark' ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3c0 .28 0 .56.02.84A7 7 0 0 0 21 12.79z" />
            </svg>
          )}
        </button>

        {/* User avatar + logout */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '50%',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '12px', fontWeight: '600', color: 'white',
          }}>
            {initials}
          </div>
          <div>
            <div style={{ fontSize: '12px', fontWeight: '500', color: 'var(--text-primary)' }}>
              {user?.username || 'User'}
            </div>
            <button
              onClick={handleLogout}
              style={{
                background: 'none', border: 'none', padding: 0,
                fontSize: '10px', color: 'var(--text-muted)', cursor: 'pointer',
                transition: 'color 0.15s',
              }}
              onMouseEnter={e => e.target.style.color = '#fb7185'}
              onMouseLeave={e => e.target.style.color = 'var(--text-muted)'}
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
