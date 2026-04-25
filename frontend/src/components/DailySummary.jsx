import { useMemo, useState } from 'react';

function SparkleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
    </svg>
  );
}

function getOverallLabel(pos, neg, neu) {
  if (pos > neg && pos >= neu) return 'Mostly Positive';
  if (neg > pos && neg >= neu) return 'Mostly Negative';
  return 'Mostly Neutral';
}

export default function DailySummary({ articles }) {
  const [expanded, setExpanded] = useState(false);
  
  const data = useMemo(() => {
    const todayArticles = (articles || []).slice(0, 100);
    const positive = todayArticles.filter((a) => a.sentiment === 'Positive').length;
    const negative = todayArticles.filter((a) => a.sentiment === 'Negative').length;
    const neutral = todayArticles.filter((a) => a.sentiment === 'Neutral').length;
    const total = todayArticles.length;
    const overall = getOverallLabel(positive, negative, neutral);
    const topFiveArticles = todayArticles.slice(0, 5);

    return { total, positive, negative, neutral, overall, topFiveArticles };
  }, [articles]);

  if (!data.total) {
    return (
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '0.5px solid rgba(167,139,250,0.2)',
          borderRadius: '12px',
          padding: '16px 18px',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a78bfa' }}>
          <SparkleIcon />
          <span style={{ fontSize: '13px', fontWeight: '500' }}>Resume IA du jour</span>
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
          No recent articles yet. Summary will appear automatically.
        </div>
      </div>
    );
  }

  // Collapsed view - only show first article
  if (!expanded) {
    const firstArticle = data.topFiveArticles[0];
    const sentimentColor = firstArticle.sentiment === 'Positive' ? '#4ade80' : firstArticle.sentiment === 'Negative' ? '#fb7185' : '#94a3b8';
    
    return (
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '0.5px solid rgba(167,139,250,0.25)',
          borderRadius: '12px',
          padding: '16px 18px',
          marginBottom: '20px',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
        onClick={() => setExpanded(true)}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a78bfa' }}>
            <SparkleIcon />
            <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>Resume IA du jour</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace' }}>
            {data.overall}
          </div>
        </div>

        <div
          style={{
            padding: '10px 12px',
            borderLeft: `3px solid ${sentimentColor}`,
            background: 'rgba(255,255,255,0.02)',
            borderRadius: '6px',
            fontSize: '11px',
            color: 'var(--text-secondary)',
            lineHeight: 1.45,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
            <span style={{ color: sentimentColor, fontWeight: '600', flexShrink: 0 }}>
              [{firstArticle.sentiment}]
            </span>
            <div>
              <div style={{ color: 'var(--text-primary)', fontWeight: '500', marginBottom: '3px' }}>
                {firstArticle.title}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                {firstArticle.feed_topic || 'Unknown'}
              </div>
            </div>
          </div>
        </div>

        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '10px', textAlign: 'center' }}>
          Click to expand ({data.topFiveArticles.length} articles available)
        </div>
      </div>
    );
  }

  // Expanded view - show all articles
  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid rgba(167,139,250,0.25)',
        borderRadius: '12px',
        padding: '16px 18px',
        marginBottom: '20px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a78bfa' }}>
          <SparkleIcon />
          <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>Resume IA du jour</span>
        </div>
        <button
          onClick={() => setExpanded(false)}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            fontSize: '12px',
            padding: 0,
          }}
        >
          Collapse ×
        </button>
      </div>

      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '12px', fontFamily: 'DM Mono, monospace' }}>
        Overall: {data.overall}
      </div>

      <div style={{ display: 'grid', gap: '8px' }}>
        {data.topFiveArticles.map((article, index) => {
          const sentimentColor = article.sentiment === 'Positive' ? '#4ade80' : article.sentiment === 'Negative' ? '#fb7185' : '#94a3b8';
          return (
            <div
              key={article.id || index}
              style={{
                padding: '10px 12px',
                borderLeft: `3px solid ${sentimentColor}`,
                background: 'rgba(255,255,255,0.02)',
                borderRadius: '6px',
                fontSize: '11px',
                color: 'var(--text-secondary)',
                lineHeight: 1.45,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                <span style={{ color: sentimentColor, fontWeight: '600', flexShrink: 0 }}>
                  [{article.sentiment}]
                </span>
                <div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: '500', marginBottom: '3px' }}>
                    {article.title}
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                    {article.feed_topic || 'Unknown'}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
