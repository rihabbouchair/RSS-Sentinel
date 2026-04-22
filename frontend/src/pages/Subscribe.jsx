import { useState, useEffect } from 'react';
import { getCurrentUser, updatePreferences, getFeeds } from '../api';

const TOPICS = ['AI', 'Tech', 'Politics', 'Sport', 'Economy', 'Science'];

const topicColors = {
  AI: '#a78bfa', Tech: '#38bdf8', Politics: '#fb923c',
  Sport: '#fb7185', Economy: '#4ade80', Science: '#34d399',
};

function formatDate(dateString) {
  if (!dateString) return 'Never';
  try { return new Date(dateString).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
  catch { return dateString; }
}

export default function Subscribe() {
  const [email, setEmail] = useState('');
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [wantsDigest, setWantsDigest] = useState(false);
  const [feeds, setFeeds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => { loadUserData(); loadFeeds(); }, []);

  async function loadUserData() {
    try {
      const user = await getCurrentUser();
      setEmail(user.email || ''); setSelectedTopics(user.topics || []); setWantsDigest(user.wants_email_digest || false);
    } catch (error) { console.error('Failed to load user data:', error); }
  }

  async function loadFeeds() {
    try { const data = await getFeeds(); setFeeds(data); }
    catch (error) { console.error('Failed to load feeds:', error); }
  }

  function toggleTopic(topic) {
    setSelectedTopics((prev) => prev.includes(topic) ? prev.filter(t => t !== topic) : [...prev, topic]);
  }

  async function handleSave(e) {
    e.preventDefault(); setLoading(true); setMessage(null);
    try {
      const result = await updatePreferences({ topics: selectedTopics, email: email || null, wants_email_digest: wantsDigest });
      setMessage({ type: 'success', text: `Preferences saved! ${result.feeds_created} feeds created.` });
      loadFeeds();
    } catch (error) {
      setMessage({ type: 'error', text: `Failed: ${error.message}` });
    } finally { setLoading(false); }
  }

  const inputStyle = {
    width: '100%', padding: '10px 14px',
    background: 'rgba(255,255,255,0.05)', border: '0.5px solid var(--border)',
    borderRadius: '8px', color: 'var(--text-primary)', fontSize: '13px',
    outline: 'none', transition: 'border-color 0.15s', fontFamily: 'inherit',
  };

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: 'var(--bg-base)', padding: '24px' }}>
      <div style={{ maxWidth: '640px', margin: '0 auto' }}>

        {/* Preferences card */}
        <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border)', borderRadius: '12px', padding: '24px', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', margin: '0 0 20px' }}>Preferences</h2>

          <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {/* Email */}
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Email Address <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>(optional)</span>
              </label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="your@email.com" style={inputStyle} onFocus={e => e.target.style.borderColor='#7c3aed'} onBlur={e => e.target.style.borderColor='var(--border)'} />
            </div>

            {/* Topics */}
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>Topics</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                {TOPICS.map((topic) => {
                  const selected = selectedTopics.includes(topic);
                  const color = topicColors[topic] || '#a78bfa';
                  return (
                    <label key={topic} style={{
                      display: 'flex', alignItems: 'center', gap: '8px',
                      padding: '9px 12px', borderRadius: '8px', cursor: 'pointer',
                      background: selected ? `${color}12` : 'rgba(255,255,255,0.03)',
                      border: selected ? `0.5px solid ${color}40` : '0.5px solid var(--border)',
                      transition: 'all 0.15s',
                    }}>
                      <div style={{ width: '14px', height: '14px', borderRadius: '3px', flexShrink: 0, background: selected ? color : 'transparent', border: selected ? `1.5px solid ${color}` : '1.5px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {selected && <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>}
                      </div>
                      <input type="checkbox" checked={selected} onChange={() => toggleTopic(topic)} style={{ display: 'none' }} />
                      <span style={{ fontSize: '12px', color: selected ? color : 'var(--text-secondary)', fontWeight: selected ? '500' : '400' }}>{topic}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Digest */}
            {email && (
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '8px', cursor: 'pointer', background: 'rgba(255,255,255,0.03)', border: '0.5px solid var(--border)' }}>
                <div style={{ width: '16px', height: '16px', borderRadius: '4px', flexShrink: 0, background: wantsDigest ? '#7c3aed' : 'transparent', border: wantsDigest ? '1.5px solid #7c3aed' : '1.5px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {wantsDigest && <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>}
                </div>
                <input type="checkbox" checked={wantsDigest} onChange={e => setWantsDigest(e.target.checked)} style={{ display: 'none' }} />
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Receive daily email digest</span>
              </label>
            )}

            {message && (
              <div style={{
                padding: '10px 12px', borderRadius: '8px', fontSize: '12px',
                background: message.type === 'success' ? 'rgba(74,222,128,0.1)' : 'rgba(251,113,133,0.1)',
                color: message.type === 'success' ? '#4ade80' : '#fb7185',
                border: `0.5px solid ${message.type === 'success' ? 'rgba(74,222,128,0.25)' : 'rgba(251,113,133,0.25)'}`,
              }}>
                {message.text}
              </div>
            )}

            <button type="submit" disabled={loading || selectedTopics.length === 0} style={{
              padding: '11px', background: loading || selectedTopics.length === 0 ? 'rgba(255,255,255,0.05)' : 'linear-gradient(135deg,#6366f1,#8b5cf6)',
              border: 'none', borderRadius: '8px',
              color: loading || selectedTopics.length === 0 ? 'var(--text-muted)' : 'white',
              fontSize: '13px', fontWeight: '500',
              cursor: loading || selectedTopics.length === 0 ? 'not-allowed' : 'pointer',
              fontFamily: 'inherit', transition: 'opacity 0.15s',
            }}>
              {loading ? 'Saving...' : 'Save Preferences'}
            </button>
          </form>
        </div>

        {/* Feeds list */}
        <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border)', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', margin: '0 0 16px' }}>
            Active Feeds
            <span style={{ marginLeft: '8px', fontSize: '11px', color: 'var(--text-muted)', fontWeight: '400', fontFamily: 'DM Mono, monospace' }}>
              {feeds.length} total
            </span>
          </h2>

          {feeds.length === 0 ? (
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No feeds registered yet. Save preferences above to create feeds.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {feeds.map((feed) => {
                const color = topicColors[feed.topic] || '#a78bfa';
                return (
                  <div key={feed.id} style={{
                    padding: '12px 14px', borderRadius: '8px',
                    background: 'rgba(255,255,255,0.03)', border: '0.5px solid var(--border)',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{
                        fontSize: '11px', fontFamily: 'DM Mono, monospace',
                        padding: '2px 8px', borderRadius: '4px',
                        background: `${color}18`, color,
                      }}>
                        {feed.topic}
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', color: '#22c55e' }}>
                        <span className="pulse-dot" style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}></span>
                        Live
                      </div>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', wordBreak: 'break-all', marginBottom: '4px' }}>{feed.url}</div>
                    {feed.last_fetched_at && (
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                        Last synced: {formatDate(feed.last_fetched_at)}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
