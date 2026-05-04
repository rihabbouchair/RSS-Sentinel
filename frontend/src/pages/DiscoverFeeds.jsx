import { useState, useEffect } from 'react';
import { discoverFeeds, discoverFeedTopics, subscribeToFeed } from '../api';

function extractFeedName(url) {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.replace('www.', '');
    // Capitalize first letter of domain name
    return hostname.charAt(0).toUpperCase() + hostname.slice(1);
  } catch {
    return url;
  }
}

export default function DiscoverFeeds() {
  const [feeds, setFeeds] = useState([]);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(new Set());
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadTopics();
  }, []);

  useEffect(() => {
    loadFeeds();
  }, [selectedTopic]);

  async function loadTopics() {
    try {
      const data = await discoverFeedTopics();
      setTopics(data.topics || []);
    } catch (error) {
      console.error('Failed to load topics:', error);
    }
  }

  async function loadFeeds() {
    setLoading(true);
    try {
      const data = await discoverFeeds(selectedTopic, 50);
      setFeeds(data.feeds || []);
    } catch (error) {
      console.error('Failed to load feeds:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubscribe(feedId) {
    setSubscribing(new Set([...subscribing, feedId]));
    try {
      await subscribeToFeed(feedId);
      setMessage('✓ Successfully subscribed!');
      setTimeout(() => setMessage(''), 3000);
      // Remove from list
      setFeeds(feeds.filter(f => f.id !== feedId));
    } catch (error) {
      console.error('Failed to subscribe:', error);
      setMessage('✗ Failed to subscribe');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setSubscribing(new Set([...subscribing].filter(id => id !== feedId)));
    }
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: 'var(--bg-base)', padding: '24px' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '20px', fontWeight: '600', color: 'var(--text-primary)', margin: '0 0 8px 0' }}>
          Discover Feeds
        </h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', marginBottom: '24px' }}>
          Browse popular and recommended feeds to expand your news sources
        </p>

        {message && (
          <div
            style={{
              padding: '10px 14px',
              background: message.startsWith('✓') ? 'rgba(74,222,128,0.15)' : 'rgba(251,113,133,0.15)',
              border: `0.5px solid ${message.startsWith('✓') ? 'rgba(74,222,128,0.3)' : 'rgba(251,113,133,0.3)'}`,
              borderRadius: '8px',
              color: message.startsWith('✓') ? '#4ade80' : '#fb7185',
              fontSize: '12px',
              marginBottom: '16px',
            }}
          >
            {message}
          </div>
        )}

        {/* Topic Filter */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Filter by Topic
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setSelectedTopic(null)}
              style={{
                padding: '6px 12px',
                background: selectedTopic === null ? 'rgba(124,58,237,0.2)' : 'rgba(255,255,255,0.08)',
                border: `0.5px solid ${selectedTopic === null ? 'rgba(124,58,237,0.4)' : 'var(--border)'}`,
                borderRadius: '6px',
                color: selectedTopic === null ? '#a78bfa' : 'var(--text-primary)',
                fontSize: '11px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.target.style.background = selectedTopic === null ? 'rgba(124,58,237,0.25)' : 'rgba(255,255,255,0.12)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = selectedTopic === null ? 'rgba(124,58,237,0.2)' : 'rgba(255,255,255,0.08)';
              }}
            >
              All Topics
            </button>
            {topics.map(topic => (
              <button
                key={topic}
                onClick={() => setSelectedTopic(topic)}
                style={{
                  padding: '6px 12px',
                  background: selectedTopic === topic ? 'rgba(124,58,237,0.2)' : 'rgba(255,255,255,0.08)',
                  border: `0.5px solid ${selectedTopic === topic ? 'rgba(124,58,237,0.4)' : 'var(--border)'}`,
                  borderRadius: '6px',
                  color: selectedTopic === topic ? '#a78bfa' : 'var(--text-primary)',
                  fontSize: '11px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = selectedTopic === topic ? 'rgba(124,58,237,0.25)' : 'rgba(255,255,255,0.12)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = selectedTopic === topic ? 'rgba(124,58,237,0.2)' : 'rgba(255,255,255,0.08)';
                }}
              >
                {topic}
              </button>
            ))}
          </div>
        </div>

        {/* Feeds Grid */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '13px' }}>Loading feeds...</div>
          </div>
        ) : feeds.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>No feeds found.</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>Try selecting a different topic</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '14px' }}>
            {feeds.map(feed => (
              <div
                key={feed.id}
                style={{
                  background: 'var(--bg-surface)',
                  border: '0.5px solid var(--border)',
                  borderRadius: '12px',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  transition: 'border-color 0.2s, transform 0.15s',
                  cursor: 'default',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                {/* Header: Feed name and badges */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '3px' }}>
                      {extractFeedName(feed.url)}
                    </div>
                    <a
                      href={feed.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={feed.url}
                      style={{
                        fontSize: '9px',
                        color: 'var(--accent-light)',
                        textDecoration: 'none',
                        opacity: 0.8,
                        transition: 'opacity 0.15s',
                        display: 'inline-block',
                        wordBreak: 'break-word',
                      }}
                      onMouseEnter={(e) => (e.target.style.opacity = '1')}
                      onMouseLeave={(e) => (e.target.style.opacity = '0.8')}
                    >
                      {feed.url.replace(/^https?:\/\/(www\.)?/, '').substring(0, 45)}
                      {feed.url.length > 45 ? '...' : ''}
                    </a>
                  </div>
                  <div style={{ display: 'flex', gap: '6px', flexShrink: 0, flexDirection: 'column', alignItems: 'flex-end' }}>
                    {Boolean(feed.is_recommended) && (
                      <span
                        style={{
                          fontSize: '8px',
                          fontWeight: '600',
                          padding: '2px 6px',
                          background: 'rgba(251,113,133,0.15)',
                          border: '0.5px solid rgba(251,113,133,0.3)',
                          borderRadius: '3px',
                          color: '#fb7185',
                          flexShrink: 0,
                        }}
                      >
                        Recommended
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Topic and Language */}
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <span
                    style={{
                      fontSize: '9px',
                      fontFamily: 'DM Mono, monospace',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      background: 'rgba(167,139,250,0.1)',
                      color: '#c4b5fd',
                    }}
                  >
                    {feed.topic}
                  </span>
                  <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace' }}>
                    {feed.language}
                  </span>
                </div>

                <button
                  onClick={() => handleSubscribe(feed.id)}
                  disabled={subscribing.has(feed.id)}
                  style={{
                    padding: '8px 12px',
                    background: subscribing.has(feed.id) ? '#6b7280' : '#8b5cf6',
                    border: 'none',
                    borderRadius: '6px',
                    color: 'white',
                    fontSize: '11px',
                    fontWeight: '500',
                    cursor: subscribing.has(feed.id) ? 'not-allowed' : 'pointer',
                    opacity: subscribing.has(feed.id) ? 0.6 : 1,
                    transition: 'all 0.2s',
                    width: '100%',
                  }}
                  onMouseEnter={(e) => !subscribing.has(feed.id) && (e.target.style.background = '#7c3aed')}
                  onMouseLeave={(e) => !subscribing.has(feed.id) && (e.target.style.background = '#8b5cf6')}
                >
                  {subscribing.has(feed.id) ? 'Subscribing...' : '+ Subscribe'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
