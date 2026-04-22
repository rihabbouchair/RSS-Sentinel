export default function FilterBar({ selectedSentiment, onSentimentChange }) {
  const filters = [
    { label: 'All', value: null, color: '#a78bfa', bg: 'rgba(167,139,250,0.12)' },
    { label: 'Positive', value: 'Positive', color: '#4ade80', bg: 'rgba(74,222,128,0.12)' },
    { label: 'Negative', value: 'Negative', color: '#fb7185', bg: 'rgba(251,113,133,0.12)' },
    { label: 'Neutral', value: 'Neutral', color: '#94a3b8', bg: 'rgba(148,163,184,0.12)' },
  ];

  return (
    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
      {filters.map(({ label, value, color, bg }) => {
        const active = selectedSentiment === value;
        return (
          <button
            key={label}
            onClick={() => onSentimentChange(value)}
            style={{
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: active ? '500' : '400',
              fontFamily: 'DM Mono, monospace',
              cursor: 'pointer',
              transition: 'all 0.15s',
              background: active ? bg : 'rgba(255,255,255,0.04)',
              color: active ? color : 'var(--text-secondary)',
              border: active ? `0.5px solid ${color}40` : '0.5px solid var(--border)',
            }}
            onMouseEnter={e => { if (!active) { e.currentTarget.style.background = bg; e.currentTarget.style.color = color; } }}
            onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.color = 'var(--text-secondary)'; } }}
          >
            {label !== 'All' && (
              <span style={{ display: 'inline-block', width: '5px', height: '5px', borderRadius: '50%', background: color, marginRight: '6px', verticalAlign: 'middle' }}></span>
            )}
            {label}
          </button>
        );
      })}
    </div>
  );
}
