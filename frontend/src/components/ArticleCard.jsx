const sentimentConfig = {
  Positive: { color: '#4ade80', bg: 'rgba(74,222,128,0.10)', border: 'rgba(74,222,128,0.25)', bar: '#4ade80' },
  Negative: { color: '#fb7185', bg: 'rgba(251,113,133,0.10)', border: 'rgba(251,113,133,0.25)', bar: '#fb7185' },
  Neutral: { color: '#94a3b8', bg: 'rgba(148,163,184,0.10)', border: 'rgba(148,163,184,0.25)', bar: '#64748b' },
};

const topicColors = {
  AI: '#a78bfa', Tech: '#38bdf8', Politics: '#fb923c',
  Sport: '#fb7185', Economy: '#4ade80', Science: '#34d399',
};

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return dateString; }
}
const getConfidenceStyles = (score) => {
  if (!score) return { color: '#94a3b8', label: 'Uncertain' };
  if (score >= 0.9) return { color: '#22c55e', label: 'High Certainty' };
  if (score >= 0.7) return { color: '#a855f7', label: 'Reliable' };
  if (score >= 0.5) return { color: '#eab308', label: 'Average' };
  return { color: '#ef4444', label: 'Low Certainty' };
};
export default function ArticleCard({ article }) {
  const sentiment = article.sentiment || 'Neutral';
  const cfg = sentimentConfig[sentiment] || sentimentConfig.Neutral;
  const topicColor = topicColors[article.category] || '#a78bfa';

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
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
        e.currentTarget.style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--border)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* Left sentiment bar */}
      <div style={{
        position: 'absolute', left: 0, top: '12px', bottom: '12px',
        width: '3px', borderRadius: '0 3px 3px 0',
        background: cfg.bar,
      }} />

      <div style={{ paddingLeft: '12px' }}>
        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', marginBottom: '8px' }}>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '14px', fontWeight: '500',
              color: 'var(--text-primary)', lineHeight: '1.4',
              transition: 'color 0.15s', flex: 1,
            }}
            onMouseEnter={e => e.target.style.color = 'var(--accent-light)'}
            onMouseLeave={e => e.target.style.color = 'var(--text-primary)'}
          >
            {article.title}
          </a>
          {/* Sentiment badge */}
          <span style={{
            flexShrink: 0,
            fontSize: '10px', fontWeight: '500',
            fontFamily: 'DM Mono, monospace',
            padding: '3px 10px', borderRadius: '20px',
            background: cfg.bg, color: cfg.color,
            border: `0.5px solid ${cfg.border}`,
            display: 'flex', alignItems: 'center', gap: '4px',
          }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: cfg.color }}></span>
            {sentiment}
          </span>
          {/* confidence score */}
          {article.confidence_score && (
            <div style={{
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
              lineHeight: '1.2'
            }}>

              <span style={{ fontSize: '11px', verticalAlign: 'middle' }}>🛡️</span>

              <span style={{ fontWeight: '500' }}>
                {Math.round(article.confidence_score * 100)}%
              </span>

              <span style={{ opacity: 0.8, fontSize: '8px', marginLeft: '2px' }}>
                ({getConfidenceStyles(article.confidence_score).label})
              </span>
            </div>
          )}
        </div>

        {/* Source */}
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Google News RSS
        </div>

        {/* Summary */}
        {article.summary && (
          <p style={{
            fontSize: '12px', color: 'var(--text-secondary)',
            lineHeight: '1.6', marginBottom: '12px',
            display: '-webkit-box', WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical', overflow: 'hidden',
          }}>
            {article.summary}
          </p>
        )}

        {/* Footer */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {article.category && (
            <span style={{
              fontSize: '10px', fontFamily: 'DM Mono, monospace',
              padding: '2px 8px', borderRadius: '4px',
              background: `${topicColor}18`, color: topicColor,
            }}>
              {article.category}
            </span>
          )}
          {article.topic && article.topic !== article.category && (
            <span style={{
              fontSize: '10px', fontFamily: 'DM Mono, monospace',
              padding: '2px 8px', borderRadius: '4px',
              background: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)',
            }}>
              {article.topic}
            </span>
          )}
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
            {formatDate(article.published_at || article.fetched_at)}
          </span>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '11px', color: 'var(--accent-light)',
              display: 'flex', alignItems: 'center', gap: '3px',
              transition: 'opacity 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.opacity = '0.7'}
            onMouseLeave={e => e.currentTarget.style.opacity = '1'}
          >
            Read →
          </a>
        </div>
      </div>
    </div>
  );
}
