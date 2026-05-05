import { useMemo, useState } from 'react';
import { createPortal } from 'react-dom';

const sentimentConfig = {
  Positive: { color: 'var(--positive)', bg: 'rgba(0,229,176,0.10)', border: 'rgba(0,229,176,0.25)', bar: 'var(--positive)' },
  Negative: { color: 'var(--negative)', bg: 'rgba(255,85,114,0.10)', border: 'rgba(255,85,114,0.25)', bar: 'var(--negative)' },
  Neutral: { color: 'var(--neutral-color)', bg: 'rgba(122,143,168,0.10)', border: 'rgba(122,143,168,0.25)', bar: 'var(--neutral-color)' },
};

const topicColors = {
  AI: 'var(--accent)',
  Tech: 'var(--positive)',
  Politics: 'var(--negative)',
  Sport: 'var(--positive)',
  Economy: 'var(--accent-light)',
  Science: 'var(--positive)',
};

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
}

const getConfidenceStyles = (score) => {
  if (!score && score !== 0) return { color: '#94a3b8', label: 'Uncertain' };
  if (score >= 0.9) return { color: 'var(--positive)', label: 'High Certainty' };
  if (score >= 0.7) return { color: 'var(--accent)', label: 'Reliable' };
  if (score >= 0.5) return { color: 'var(--accent-light)', label: 'Average' };
  return { color: 'var(--negative)', label: 'Low Certainty' };
};

const stopWords = new Set([
  'the', 'and', 'for', 'with', 'from', 'that', 'this', 'have', 'has', 'was', 'were', 'are', 'will', 'about',
  'into', 'over', 'after', 'before', 'under', 'while', 'where', 'their', 'there', 'them', 'than', 'been',
  'said', 'says', 'amid', 'news', 'article', 'today', 'yesterday', 'dans', 'avec', 'pour', 'contre', 'sur',
  'dans', 'les', 'des', 'une', 'mais', 'dont', 'plus', 'moins', 'tout', 'vous', 'nous', 'ils', 'elles',
  'هذا', 'هذه', 'ذلك', 'تلك', 'على', 'الى', 'إلى', 'من', 'عن', 'في', 'مع', 'كان', 'كانت', 'التي', 'الذي', 'بين',
]);

function parseInferenceLog(rawLog) {
  if (!rawLog) return null;
  if (typeof rawLog === 'object') return rawLog;
  try {
    return JSON.parse(rawLog);
  } catch {
    return null;
  }
}

function extractSignalWords(log, article) {
  if (Array.isArray(log?.evidence_keywords) && log.evidence_keywords.length) {
    return log.evidence_keywords.slice(0, 8);
  }

  const sourceText = [
    log?.title,
    log?.excerpt,
    article?.title,
    article?.summary,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();

  const cleaned = sourceText
    .replace(/https?:\/\/\S+/g, ' ')
    .replace(/[^\p{L}\p{N}\s-]/gu, ' ')
    .split(/\s+/)
    .filter((word) => word.length >= 4 && !stopWords.has(word));

  const frequency = new Map();
  for (const word of cleaned) {
    frequency.set(word, (frequency.get(word) || 0) + 1);
  }

  return [...frequency.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([word]) => word);
}

function normalizeComparableText(text) {
  return (text || '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function getDisplaySummary(article, inference) {
  const title = (article?.title || '').trim();
  const summary = (article?.summary || '').trim();
  const excerpt = (inference?.excerpt || '').trim();

  const normalizedTitle = normalizeComparableText(title);
  const normalizedSummary = normalizeComparableText(summary);
  const normalizedExcerpt = normalizeComparableText(excerpt);

  if (summary && normalizedSummary && normalizedSummary !== normalizedTitle) {
    return summary;
  }

  if (excerpt && normalizedExcerpt && normalizedExcerpt !== normalizedTitle) {
    return excerpt;
  }

  if (inference?.reasoning_summary) {
    return inference.reasoning_summary;
  }

  return 'No short summary was available for this article.';
}

export default function ArticleCard({ article, onMarkRead }) {
  const [showWhy, setShowWhy] = useState(false);
  const sentiment = article.sentiment || 'Neutral';
  const cfg = sentimentConfig[sentiment] || sentimentConfig.Neutral;
  const feedTopicColor = topicColors[article.feed_topic] || 'var(--accent-light)';
  const inference = useMemo(() => parseInferenceLog(article.inference_log), [article.inference_log]);
  const signalWords = useMemo(() => extractSignalWords(inference, article), [inference, article]);
  const displaySummary = useMemo(() => getDisplaySummary(article, inference), [article, inference]);

  const hasConfidence =
    article.confidence_score !== null && article.confidence_score !== undefined;

  const whyModal = showWhy
    ? createPortal(
        <div
          onClick={() => setShowWhy(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(7,17,29,0.46)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            zIndex: 2000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: 'min(920px, 100%)',
              maxHeight: 'min(84vh, 900px)',
              borderRadius: '20px',
              border: '1px solid rgba(167,139,250,0.28)',
              background: 'var(--bg-surface)',
              padding: '24px',
              boxShadow: '0 32px 96px rgba(2,10,24,0.42)',
              overflowY: 'auto',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', marginBottom: '14px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '18px', color: 'var(--text-primary)' }}>Why this classification?</h3>
                <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-muted)' }}>{article.title}</div>
              </div>
              <button
                type="button"
                onClick={() => setShowWhy(false)}
                style={{
                  border: '0.5px solid var(--border)',
                  background: 'transparent',
                  color: 'var(--text-muted)',
                  borderRadius: '8px',
                  fontSize: '12px',
                  padding: '6px 10px',
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
            </div>

            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.6 }}>
              {inference?.reasoning_summary || 'No model reasoning summary was stored for this article.'}
            </div>

            <div style={{ display: 'grid', gap: '10px', marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <span style={{ color: 'var(--text-muted)' }}>Sentiment reason: </span>
                {inference?.sentiment_reason || 'No specific sentiment explanation was stored.'}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <span style={{ color: 'var(--text-muted)' }}>Topic reason: </span>
                {inference?.topic_reason || 'No specific topic explanation was stored.'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
              <span style={{ fontSize: '11px', fontFamily: 'DM Mono, monospace', padding: '4px 10px', borderRadius: '999px', background: cfg.bg, color: cfg.color, border: `0.5px solid ${cfg.border}` }}>
                Sentiment: {article.sentiment || inference?.sentiment || 'Unknown'}
              </span>
              <span style={{ fontSize: '11px', fontFamily: 'DM Mono, monospace', padding: '4px 10px', borderRadius: '999px', background: 'rgba(255,255,255,0.08)', color: 'var(--text-secondary)', border: '0.5px solid var(--border)' }}>
                Topic: {article.feed_topic || 'Unknown'}
              </span>
              <span style={{ fontSize: '11px', fontFamily: 'DM Mono, monospace', padding: '4px 10px', borderRadius: '999px', background: 'rgba(255,255,255,0.08)', color: 'var(--text-secondary)', border: '0.5px solid var(--border)' }}>
                Subtopic: {article.topic || inference?.topic || 'Unknown'}
              </span>
              {hasConfidence && (
                <span style={{ fontSize: '11px', fontFamily: 'DM Mono, monospace', padding: '4px 10px', borderRadius: '999px', background: `${getConfidenceStyles(article.confidence_score).color}12`, color: getConfidenceStyles(article.confidence_score).color, border: `0.5px solid ${getConfidenceStyles(article.confidence_score).color}30` }}>
                  Confidence: {Math.round(article.confidence_score * 100)}%
                </span>
              )}
            </div>

            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Signal words detected in the article text:
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {signalWords.length ? signalWords.map((word) => (
                <span key={word} style={{ fontSize: '11px', fontFamily: 'DM Mono, monospace', padding: '4px 10px', borderRadius: '999px', background: 'rgba(167,139,250,0.14)', color: '#c4b5fd', border: '0.5px solid rgba(167,139,250,0.25)' }}>
                  {word}
                </span>
              )) : (
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Not enough text to extract signal words.</span>
              )}
            </div>
          </div>
        </div>,
        document.body,
      )
    : null;

  const handleMarkRead = async () => {
    if (onMarkRead) {
      await onMarkRead(article.id);
    }
  };

  return (
    <div
      className="animate-fade-in"
      style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid var(--border)',
        borderRadius: '12px',
        padding: '16px',
        position: 'relative',
        overflow: 'hidden',
        transition: 'border-color 0.2s, transform 0.15s',
        cursor: 'default',
        opacity: article.is_read ? 0.62 : 1,
        filter: article.is_read ? 'grayscale(0.2)' : 'none',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
        e.currentTarget.style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: '12px',
          bottom: '12px',
          width: '3px',
          borderRadius: '0 3px 3px 0',
          background: cfg.bar,
        }}
      />

      <div style={{ paddingLeft: '12px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: '12px',
            marginBottom: '8px',
          }}
        >
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '14px',
              fontWeight: '500',
              color: 'var(--text-primary)',
              lineHeight: '1.4',
              transition: 'color 0.15s',
              flex: 1,
              textDecoration: 'none',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--accent-light)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--text-primary)';
            }}
          >
            {article.title}
          </a>

          <span
            style={{
              flexShrink: 0,
              fontSize: '10px',
              fontWeight: '500',
              fontFamily: 'DM Mono, monospace',
              padding: '3px 10px',
              borderRadius: '20px',
              background: cfg.bg,
              color: cfg.color,
              border: `0.5px solid ${cfg.border}`,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: cfg.color }} />
            {sentiment}
          </span>

          {/* confidence score intentionally not shown on card; kept in Why modal */}
        </div>

        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Google News RSS
        </div>

        {displaySummary && (
          <p
            style={{
              fontSize: '12px',
        transition: 'border-color 0.2s, transform 0.15s, opacity 0.2s',
              lineHeight: '1.6',
        opacity: article.is_read ? 0.62 : 1,
        filter: article.is_read ? 'grayscale(0.2)' : 'none',
              marginBottom: '12px',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {displaySummary}
          </p>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {(article.feed_topic || article.topic) && (
            <span
              style={{
                fontSize: '10px',
                fontFamily: 'DM Mono, monospace',
                padding: '2px 8px',
                borderRadius: '4px',
                background: `${feedTopicColor}18`,
                color: feedTopicColor,
              }}
            >
              {article.feed_topic || article.topic}
            </span>
          )}

          <button
            type="button"
            onClick={() => setShowWhy(true)}
            style={{
              fontSize: '10px',
              fontFamily: 'DM Mono, monospace',
              padding: '2px 8px',
              borderRadius: '4px',
              background: 'rgba(255,255,255,0.08)',
              color: 'var(--text-primary)',
              border: '0.5px solid var(--border)',
              cursor: 'pointer',
            }}
          >
            Why?
          </button>

          <button
            type="button"
            onClick={handleMarkRead}
            title={article.is_read ? 'Mark as unread' : 'Mark as read'}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '10px',
              fontFamily: 'DM Mono, monospace',
              padding: '6px 8px',
              borderRadius: '6px',
              background: article.is_read ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.08)',
              color: article.is_read ? 'var(--text-muted)' : 'var(--text-primary)',
              border: `0.5px solid ${article.is_read ? 'rgba(255,255,255,0.04)' : 'var(--border)'}`,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = article.is_read ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.12)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = article.is_read ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.08)';
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ opacity: 0.9 }}>
              <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            {article.is_read ? 'Read' : 'Mark Read'}
          </button>

          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
            {formatDate(article.fetched_at || article.published_at)}
          </span>

          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '11px',
              color: 'var(--accent-light)',
              display: 'flex',
              alignItems: 'center',
              gap: '3px',
              transition: 'opacity 0.15s',
              textDecoration: 'none',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = '0.7';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = '1';
            }}
          >
            Read →
          </a>
        </div>
      </div>

      {whyModal}
    </div>
  );
}
