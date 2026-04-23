import { useState, useEffect, useMemo } from 'react';
import {
  getCurrentUser,
  updatePreferences,
  getFeeds,
  requestEmailVerification,
  verifyEmailCode,
} from '../api';

const POPULAR_TOPICS = [
  'AI', 'Tech', 'Politics', 'Sport', 'Economy', 'Science',
  'Health', 'Business', 'Entertainment', 'World', 'Climate',
  'Crypto', 'Education', 'Travel', 'Gaming',
];

const topicColors = {
  AI: '#a78bfa',
  Tech: '#38bdf8',
  Politics: '#fb923c',
  Sport: '#fb7185',
  Economy: '#4ade80',
  Science: '#34d399',
  Health: '#2dd4bf',
  Business: '#60a5fa',
  Entertainment: '#f472b6',
  World: '#f59e0b',
  Climate: '#22c55e',
  Crypto: '#fbbf24',
  Education: '#818cf8',
  Travel: '#06b6d4',
  Gaming: '#a3e635',
};

function normalizeTopicLabel(topic) {
  const raw = (topic || '')
    .trim()
    .replace(/\s+/g, ' ');

  if (!raw) return '';

  const canonical = POPULAR_TOPICS.find((item) => item.toLowerCase() === raw.toLowerCase());
  if (canonical) return canonical;

  return raw
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

function formatDate(dateString) {
  if (!dateString) return 'Never';
  try {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

export default function Subscribe() {
  const [email, setEmail] = useState('');
  const [verifiedEmail, setVerifiedEmail] = useState('');
  const [pendingEmail, setPendingEmail] = useState('');
  const [emailVerified, setEmailVerified] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [languagePreferences, setLanguagePreferences] = useState(['English']);
  const [wantsDigest, setWantsDigest] = useState(false);
  const [feeds, setFeeds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [message, setMessage] = useState(null);
  const [topicToAdd, setTopicToAdd] = useState('');
  const [customTopic, setCustomTopic] = useState('');

  useEffect(() => {
    loadUserData();
    loadFeeds();
  }, []);

  async function loadUserData() {
    try {
      const user = await getCurrentUser();
      setVerifiedEmail(user.email || '');
      setPendingEmail(user.pending_email || '');
      setEmail(user.pending_email || user.email || '');
      setEmailVerified(Boolean(user.email_verified));
      setSelectedTopics(user.topics || []);
      setLanguagePreferences(user.language_preferences || ['English']);
      setWantsDigest(Boolean(user.wants_email_digest));
    } catch (error) {
      console.error('Failed to load user data:', error);
    }
  }

  async function loadFeeds() {
    try {
      const data = await getFeeds();
      setFeeds(data);
    } catch (error) {
      console.error('Failed to load feeds:', error);
    }
  }

  function toggleTopic(topic) {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  }

  function addTopic(topic) {
    const normalized = normalizeTopicLabel(topic);
    if (!normalized) return;
    setSelectedTopics((prev) => (prev.includes(normalized) ? prev : [...prev, normalized]));
  }

  const availableTopics = useMemo(
    () => POPULAR_TOPICS.filter((topic) => !selectedTopics.includes(topic)),
    [selectedTopics]
  );

  async function handleSave(e) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const result = await updatePreferences({
        topics: selectedTopics,
        email: email || null,
        wants_email_digest: wantsDigest,
        language_preferences: languagePreferences,
      });

      await loadUserData();
      await loadFeeds();

      if (result.email_verification_sent) {
        setMessage({
          type: 'success',
          text: `Preferences saved. ${result.feeds_created} feeds created. A verification code was sent to your email.`,
        });
      } else {
        setMessage({
          type: 'success',
          text: `Preferences saved. ${result.feeds_created} feeds created.`,
        });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Failed: ${error.message}` });
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyCode() {
    if (!verificationCode.trim()) return;

    setVerifying(true);
    setMessage(null);

    try {
      await verifyEmailCode(verificationCode.trim());
      setVerificationCode('');
      await loadUserData();
      setMessage({
        type: 'success',
        text: 'Email verified successfully. Daily digest can now be delivered.',
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.message || 'Verification failed',
      });
    } finally {
      setVerifying(false);
    }
  }

  async function handleResendCode() {
    setResending(true);
    setMessage(null);

    try {
      const result = await requestEmailVerification();
      setMessage({
        type: result.email_verification_sent ? 'success' : 'error',
        text: result.message,
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.message || 'Failed to resend verification code',
      });
    } finally {
      setResending(false);
    }
  }

  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    background: 'rgba(255,255,255,0.05)',
    border: '0.5px solid var(--border)',
    borderRadius: '8px',
    color: 'var(--text-primary)',
    fontSize: '13px',
    outline: 'none',
    transition: 'border-color 0.15s',
    fontFamily: 'inherit',
  };

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: 'var(--bg-base)', padding: '24px' }}>
      <div style={{ maxWidth: '640px', margin: '0 auto' }}>
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '0.5px solid var(--border)',
            borderRadius: '12px',
            padding: '24px',
            marginBottom: '16px',
          }}
        >
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', margin: '0 0 20px' }}>
            Preferences
          </h2>

          <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Email Address <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>(optional)</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                style={inputStyle}
              />

              {verifiedEmail && emailVerified && (
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#4ade80' }}>
                  Verified email: {verifiedEmail}
                </div>
              )}

              {pendingEmail && !emailVerified && (
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#f59e0b' }}>
                  Pending verification: {pendingEmail}
                </div>
              )}
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Article Languages
              </label>

              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                {['English', 'French', 'Arabic'].map((lang) => (
                  <label
                    key={lang}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      background: languagePreferences.includes(lang)
                        ? 'rgba(96, 165, 250, 0.2)'
                        : 'rgba(255,255,255,0.03)',
                      border: languagePreferences.includes(lang)
                        ? '0.5px solid rgba(96, 165, 250, 0.4)'
                        : '0.5px solid var(--border)',
                      transition: 'all 0.15s',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={languagePreferences.includes(lang)}
                      onChange={() => {
                        setLanguagePreferences((prev) =>
                          prev.includes(lang)
                            ? prev.filter((l) => l !== lang)
                            : [...prev, lang]
                        );
                      }}
                      style={{ cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '12px', color: 'var(--text-primary)' }}>
                      {lang}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Topics
              </label>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                {selectedTopics.map((topic) => {
                  const selected = selectedTopics.includes(topic);
                  const color = topicColors[topic] || '#a78bfa';

                  return (
                    <label
                      key={topic}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '9px 12px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        background: selected ? `${color}12` : 'rgba(255,255,255,0.03)',
                        border: selected ? `0.5px solid ${color}40` : '0.5px solid var(--border)',
                        transition: 'all 0.15s',
                      }}
                    >
                      <div
                        style={{
                          width: '14px',
                          height: '14px',
                          borderRadius: '3px',
                          flexShrink: 0,
                          background: selected ? color : 'transparent',
                          border: selected ? `1.5px solid ${color}` : '1.5px solid var(--border)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {selected && (
                          <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        )}
                      </div>
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={() => toggleTopic(topic)}
                        style={{ display: 'none' }}
                      />
                      <span
                        style={{
                          fontSize: '12px',
                          color: selected ? color : 'var(--text-secondary)',
                          fontWeight: selected ? '500' : '400',
                        }}
                      >
                        {topic}
                      </span>
                    </label>
                  );
                })}
              </div>

              {availableTopics.length > 0 && (
                <div style={{ marginTop: '16px', marginBottom: '12px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Popular Topics
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                    {availableTopics.map((topic) => {
                      const color = topicColors[topic] || '#a78bfa';
                      return (
                        <label
                          key={topic}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '9px 12px',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            background: 'rgba(255,255,255,0.03)',
                            border: '0.5px solid var(--border)',
                            transition: 'all 0.15s',
                          }}
                        >
                          <div
                            style={{
                              width: '14px',
                              height: '14px',
                              borderRadius: '3px',
                              flexShrink: 0,
                              background: 'transparent',
                              border: `1.5px solid ${color}40`,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          />
                          <input
                            type="checkbox"
                            checked={false}
                            onChange={() => addTopic(topic)}
                            style={{ display: 'none' }}
                          />
                          <span
                            style={{
                              fontSize: '12px',
                              color: 'var(--text-secondary)',
                              fontWeight: '400',
                            }}
                          >
                            + {topic}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Add Custom Topic
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    value={customTopic}
                    onChange={(e) => setCustomTopic(e.target.value)}
                    placeholder="e.g. Automotive, Cybersecurity"
                    style={{ ...inputStyle, flex: 1 }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      addTopic(customTopic);
                      setCustomTopic('');
                    }}
                    disabled={!customTopic.trim()}
                    style={{
                      padding: '10px 14px',
                      borderRadius: '8px',
                      border: '0.5px solid var(--border)',
                      background: customTopic.trim() ? 'rgba(34,197,94,0.18)' : 'rgba(255,255,255,0.04)',
                      color: customTopic.trim() ? '#86efac' : 'var(--text-muted)',
                      cursor: customTopic.trim() ? 'pointer' : 'not-allowed',
                      fontSize: '12px',
                      fontWeight: '500',
                    }}
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            {email && (
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  background: 'rgba(255,255,255,0.03)',
                  border: '0.5px solid var(--border)',
                }}
              >
                <div
                  style={{
                    width: '16px',
                    height: '16px',
                    borderRadius: '4px',
                    flexShrink: 0,
                    background: wantsDigest ? '#7c3aed' : 'transparent',
                    border: wantsDigest ? '1.5px solid #7c3aed' : '1.5px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {wantsDigest && (
                    <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </div>
                <input
                  type="checkbox"
                  checked={wantsDigest}
                  onChange={(e) => setWantsDigest(e.target.checked)}
                  style={{ display: 'none' }}
                />
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Receive daily email digest {emailVerified ? '(active)' : '(starts after verification)'}
                </span>
              </label>
            )}

            {pendingEmail && !emailVerified && (
              <div
                style={{
                  padding: '14px',
                  borderRadius: '10px',
                  background: 'rgba(245,158,11,0.08)',
                  border: '0.5px solid rgba(245,158,11,0.25)',
                }}
              >
                <div style={{ fontSize: '12px', color: '#fbbf24', marginBottom: '10px', fontWeight: '600' }}>
                  Verify your email
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                  Enter the 6-digit code sent to {pendingEmail}.
                </div>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <input
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    placeholder="123456"
                    maxLength={6}
                    style={{ ...inputStyle, flex: '1 1 180px' }}
                  />
                  <button
                    type="button"
                    onClick={handleVerifyCode}
                    disabled={verifying || !verificationCode.trim()}
                    style={{
                      padding: '10px 14px',
                      borderRadius: '8px',
                      border: 'none',
                      background: '#f59e0b',
                      color: 'white',
                      cursor: verifying ? 'not-allowed' : 'pointer',
                      opacity: verifying ? 0.7 : 1,
                    }}
                  >
                    {verifying ? 'Verifying...' : 'Verify'}
                  </button>
                  <button
                    type="button"
                    onClick={handleResendCode}
                    disabled={resending}
                    style={{
                      padding: '10px 14px',
                      borderRadius: '8px',
                      border: '0.5px solid var(--border)',
                      background: 'rgba(255,255,255,0.04)',
                      color: 'var(--text-primary)',
                      cursor: resending ? 'not-allowed' : 'pointer',
                      opacity: resending ? 0.7 : 1,
                    }}
                  >
                    {resending ? 'Sending...' : 'Resend Code'}
                  </button>
                </div>
              </div>
            )}

            {message && (
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  background: message.type === 'success' ? 'rgba(74,222,128,0.1)' : 'rgba(251,113,133,0.1)',
                  color: message.type === 'success' ? '#4ade80' : '#fb7185',
                  border: `0.5px solid ${
                    message.type === 'success'
                      ? 'rgba(74,222,128,0.25)'
                      : 'rgba(251,113,133,0.25)'
                  }`,
                }}
              >
                {message.text}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || selectedTopics.length === 0}
              style={{
                padding: '11px',
                background:
                  loading || selectedTopics.length === 0
                    ? 'rgba(255,255,255,0.05)'
                    : 'linear-gradient(135deg,#6366f1,#8b5cf6)',
                border: 'none',
                borderRadius: '8px',
                color: loading || selectedTopics.length === 0 ? 'var(--text-muted)' : 'white',
                fontSize: '13px',
                fontWeight: '500',
                cursor: loading || selectedTopics.length === 0 ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
                transition: 'opacity 0.15s',
              }}
            >
              {loading ? 'Saving...' : 'Save Preferences'}
            </button>
          </form>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '0.5px solid var(--border)',
            borderRadius: '12px',
            padding: '24px',
          }}
        >
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', margin: '0 0 16px' }}>
            Active Feeds
            <span
              style={{
                marginLeft: '8px',
                fontSize: '11px',
                color: 'var(--text-muted)',
                fontWeight: '400',
                fontFamily: 'DM Mono, monospace',
              }}
            >
              {feeds.length} total
            </span>
          </h2>

          {feeds.length === 0 ? (
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              No feeds registered yet. Save preferences above to create feeds.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {feeds.map((feed) => {
                const color = topicColors[feed.topic] || '#a78bfa';

                return (
                  <div
                    key={feed.id}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.03)',
                      border: '0.5px solid var(--border)',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '6px',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '11px',
                          fontFamily: 'DM Mono, monospace',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: `${color}18`,
                          color,
                        }}
                      >
                        {feed.topic}
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', color: '#22c55e' }}>
                        <span
                          className="pulse-dot"
                          style={{
                            width: '5px',
                            height: '5px',
                            borderRadius: '50%',
                            background: '#22c55e',
                            display: 'inline-block',
                          }}
                        />
                        Live
                      </div>
                    </div>

                    <div
                      style={{
                        fontSize: '11px',
                        color: 'var(--text-muted)',
                        fontFamily: 'DM Mono, monospace',
                        wordBreak: 'break-all',
                        marginBottom: '4px',
                      }}
                    >
                      {feed.url}
                    </div>

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
