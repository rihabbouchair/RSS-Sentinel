import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getTopics, getArticles } from '../api';

const topicColors = {
  AI: '#a78bfa',
  Tech: '#38bdf8',
  Politics: '#fb923c',
  Sport: '#fb7185',
  Economy: '#4ade80',
  Science: '#34d399',
};

const NavIcon = ({ path, active }) => {
  const icons = {
    '/': (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
    '/settings': (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
      </svg>
    ),
  };
  return icons[path] || null;
};

export default function Sidebar({ selectedTopic, onTopicSelect }) {
  const [topics, setTopics] = useState([]);
  const [topicCounts, setTopicCounts] = useState({});
  const location = useLocation();

  useEffect(() => {
    loadTopics();
    const interval = setInterval(loadTopics, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadTopics() {
    try {
      const data = await getTopics();
      setTopics(data.topics);
      const counts = {};
      await Promise.all(data.topics.map(async (topic) => {
        try {
          const articles = await getArticles({ category: topic, limit: 100 });
          counts[topic] = articles.length;
        } catch { counts[topic] = 0; }
      }));
      setTopicCounts(counts);
    } catch (error) {
      console.error('Failed to load topics:', error);
    }
  }

  return (
    <div style={{
      width: '220px', minWidth: '220px',
      background: 'var(--bg-surface)',
      borderRight: '0.5px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      height: '100vh',
    }}>
      {/* Logo */}
      <div style={{ padding: '20px 18px 18px', borderBottom: '0.5px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '8px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1" fill="white" stroke="none"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', lineHeight: 1.2 }}>RSS Sentinel</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>AI News Analyzer</div>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav style={{ padding: '14px 0' }}>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', padding: '0 18px 8px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Navigation
        </div>
        {[
          { path: '/', label: 'Dashboard' },
          { path: '/settings', label: 'Settings' },
        ].map(({ path, label }) => {
          const active = location.pathname === path;
          return (
            <Link key={path} to={path} style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '9px 18px',
              color: active ? 'var(--accent-light)' : 'var(--text-secondary)',
              background: active ? 'rgba(139,92,246,0.1)' : 'transparent',
              borderLeft: active ? '2px solid #7c3aed' : '2px solid transparent',
              fontSize: '13px', fontWeight: active ? '500' : '400',
              transition: 'all 0.15s',
              textDecoration: 'none',
            }}
            onMouseEnter={e => { if (!active) { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.background = 'var(--bg-hover)'; } }}
            onMouseLeave={e => { if (!active) { e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.background = 'transparent'; } }}
            >
              <NavIcon path={path} active={active} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Topics */}
      {topics.length > 0 && (
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 0 16px' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', padding: '8px 18px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Topics
          </div>

          <button
            onClick={() => onTopicSelect(null)}
            style={{
              width: '100%', textAlign: 'left', padding: '8px 18px',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: selectedTopic === null ? 'rgba(139,92,246,0.1)' : 'transparent',
              borderLeft: selectedTopic === null ? '2px solid #7c3aed' : '2px solid transparent',
              color: selectedTopic === null ? 'var(--accent-light)' : 'var(--text-secondary)',
              fontSize: '13px', fontWeight: selectedTopic === null ? '500' : '400',
              cursor: 'pointer', border: 'none', transition: 'all 0.15s',
            }}
          >
            <span>All Articles</span>
            <span style={{
              fontSize: '10px', padding: '2px 7px', borderRadius: '20px',
              background: 'rgba(139,92,246,0.15)', color: 'var(--accent-light)', fontFamily: 'DM Mono, monospace',
            }}>
              {Object.values(topicCounts).reduce((a, b) => a + b, 0)}
            </span>
          </button>

          {topics.map((topic) => {
            const active = selectedTopic === topic;
            const color = topicColors[topic] || 'var(--accent-light)';
            return (
              <button
                key={topic}
                onClick={() => onTopicSelect(topic)}
                style={{
                  width: '100%', textAlign: 'left', padding: '8px 18px',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: active ? `${color}15` : 'transparent',
                  borderLeft: active ? `2px solid ${color}` : '2px solid transparent',
                  color: active ? color : 'var(--text-secondary)',
                  fontSize: '13px', fontWeight: active ? '500' : '400',
                  cursor: 'pointer', border: 'none', transition: 'all 0.15s',
                }}
                onMouseEnter={e => { if (!active) { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; } }}
                onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; } }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: color, flexShrink: 0 }}></span>
                  <span className="truncate">{topic}</span>
                </div>
                <span style={{
                  fontSize: '10px', padding: '2px 7px', borderRadius: '20px',
                  background: `${color}20`, color, fontFamily: 'DM Mono, monospace',
                }}>
                  {topicCounts[topic] || 0}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Live indicator */}
      <div style={{ padding: '14px 18px', borderTop: '0.5px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', fontSize: '11px', color: '#22c55e' }}>
          <span className="pulse-dot" style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}></span>
          Live · Auto-refresh 10s
        </div>
      </div>
    </div>
  );
}
