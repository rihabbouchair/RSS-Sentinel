import { useMemo, useState } from 'react';

const sentimentConfig = {
  Positive: { color: '#4ade80', bg: 'rgba(74,222,128,0.10)', border: 'rgba(74,222,128,0.25)', bar: '#4ade80' },
  Negative: { color: '#fb7185', bg: 'rgba(251,113,133,0.10)', border: 'rgba(251,113,133,0.25)', bar: '#fb7185' },
  Neutral: { color: '#94a3b8', bg: 'rgba(148,163,184,0.10)', border: 'rgba(148,163,184,0.25)', bar: '#64748b' },
};

const topicColors = {
  AI: '#a78bfa',
  Tech: '#38bdf8',
  Politics: '#fb923c',
  Sport: '#fb7185',
  Economy: '#4ade80',
  Science: '#34d399',
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
  if (score >= 0.9) return { color: '#22c55e', label: 'High Certainty' };
  if (score >= 0.7) return { color: '#a855f7', label: 'Reliable' };
  if (score >= 0.5) return { color: '#eab308', label: 'Average' };
  return { color: '#ef4444', label: 'Low Certainty' };
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

export default function ArticleCard({ article }) {
  const [showWhy, setShowWhy] = useState(false);
  const sentiment = article.sentiment || 'Neutral';
  const cfg = sentimentConfig[sentiment] || sentimentConfig.Neutral;
  const feedTopicColor = topicColors[article.feed_topic] || '#a78bfa';
  const inference = useMemo(() => parseInferenceLog(article.inference_log), [article.inference_log]);
  const signalWords = useMemo(() => extractSignalWords(inference, article), [inference, article]);
  const displaySummary = useMemo(() => getDisplaySummary(article, inference), [article, inference]);

  const hasConfidence =
    article.confidence_score !== null && article.confidence_score !== undefined;

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

          {hasConfidence && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '9px',
                fontFamily: 'DM Mono, monospace',
                color: getConfidenceStyles(article.confidence_score).color,
                background: `${getConfidenceStyles(article.confidence_score).color}10`,
                padding: '2px 8px',
                borderRadius: '4px',
                border: `0.5px solid ${getConfidenceStyles(article.confidence_score).color}30`,
                lineHeight: '1.2',
              }}
            >
              <span style={{ fontWeight: '500' }}>
                {Math.round(article.confidence_score * 100)}%
              </span>
              <span style={{ opacity: 0.8, fontSize: '8px', marginLeft: '2px' }}>
                ({getConfidenceStyles(article.confidence_score).label})
              </span>
            </div>
          )}
        </div>

        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Google News RSS
        </div>

        {displaySummary && (
          <p
            style={{
              fontSize: '12px',
              color: 'var(--text-secondary)',
              lineHeight: '1.6',
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

      {showWhy && (
        <div
          onClick={() => setShowWhy(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(2,6,23,0.55)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
            padding: '24px 16px',
            overflowY: 'auto',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '760px',
              maxHeight: 'calc(100vh - 48px)',
              borderRadius: '16px',
              border: '1px solid rgba(167,139,250,0.25)',
              background: 'var(--bg-surface)',
              padding: '20px',
              boxShadow: '0 40px 100px rgba(0,0,0,0.5)',
              overflowY: 'auto',
              margin: '8px 0',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <h3 style={{ margin: 0, fontSize: '14px', color: 'var(--text-primary)' }}>Why this classification?</h3>
              <button
                type="button"
                onClick={() => setShowWhy(false)}
                style={{
                  border: '0.5px solid var(--border)',
                  background: 'transparent',
                  color: 'var(--text-muted)',
                  borderRadius: '6px',
                  fontSize: '11px',
                  padding: '3px 8px',
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
            </div>

            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '10px', lineHeight: 1.5 }}>
              {inference?.reasoning_summary || 'No model reasoning summary was stored for this article.'}
            </div>

            <div style={{ display: 'grid', gap: '8px', marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                <span style={{ color: 'var(--text-muted)' }}>Sentiment reason: </span>
                {inference?.sentiment_reason || 'No specific sentiment explanation was stored.'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                <span style={{ color: 'var(--text-muted)' }}>Topic reason: </span>
                {inference?.topic_reason || 'No specific topic explanation was stored.'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
              <span
                style={{
                  fontSize: '10px',
                  fontFamily: 'DM Mono, monospace',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  background: cfg.bg,
                  color: cfg.color,
                  border: `0.5px solid ${cfg.border}`,
                }}
              >
                Sentiment: {article.sentiment || inference?.sentiment || 'Unknown'}
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontFamily: 'DM Mono, monospace',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  background: 'rgba(255,255,255,0.08)',
                  color: 'var(--text-secondary)',
                  border: '0.5px solid var(--border)',
                }}
              >
                Topic: {article.feed_topic || 'Unknown'}
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontFamily: 'DM Mono, monospace',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  background: 'rgba(255,255,255,0.08)',
                  color: 'var(--text-secondary)',
                  border: '0.5px solid var(--border)',
                }}
              >
                Subtopic: {article.topic || inference?.topic || 'Unknown'}
              </span>
              {hasConfidence && (
                <span
                  style={{
                    fontSize: '10px',
                    fontFamily: 'DM Mono, monospace',
                    padding: '3px 8px',
                    borderRadius: '6px',
                    background: `${getConfidenceStyles(article.confidence_score).color}12`,
                    color: getConfidenceStyles(article.confidence_score).color,
                    border: `0.5px solid ${getConfidenceStyles(article.confidence_score).color}30`,
                  }}
                >
                  Confidence: {Math.round(article.confidence_score * 100)}%
                </span>
              )}
            </div>

            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>
              Signal words detected in the article text:
            </div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {signalWords.length ? (
                signalWords.map((word) => (
                  <span
                    key={word}
                    style={{
                      fontSize: '10px',
                      fontFamily: 'DM Mono, monospace',
                      padding: '3px 8px',
                      borderRadius: '999px',
                      background: 'rgba(167,139,250,0.14)',
                      color: '#c4b5fd',
                      border: '0.5px solid rgba(167,139,250,0.25)',
                    }}
                  >
                    {word}
                  </span>
                ))
              ) : (
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Not enough text to extract signal words.
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
