import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const location = useLocation();
  const { logout, user } = useAuth();
  const navigate = useNavigate();

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
        {/* Bell icon */}
        <button style={{
          width: '32px', height: '32px', borderRadius: '8px',
          background: 'rgba(255,255,255,0.05)', border: '0.5px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', position: 'relative',
        }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
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
