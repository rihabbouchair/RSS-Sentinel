export default function FilterBar({ selectedSentiment, onSentimentChange }) {
  const filters = [
    { label: 'All', value: null, color: 'var(--accent-light)', bg: 'rgba(124,111,255,0.12)' },
    { label: 'Positive', value: 'Positive', color: 'var(--positive)', bg: 'rgba(0,229,176,0.12)' },
    { label: 'Negative', value: 'Negative', color: 'var(--negative)', bg: 'rgba(255,85,114,0.12)' },
    { label: 'Neutral', value: 'Neutral', color: 'var(--neutral-color)', bg: 'rgba(122,143,168,0.12)' },
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
              fontFamily: 'JetBrains Mono, monospace',
              cursor: 'pointer',
              transition: 'all 0.15s',
              background: active ? bg : 'rgba(255,255,255,0.05)',
              color: active ? color : 'var(--text-secondary)',
              border: active ? `0.5px solid ${color}40` : '0.5px solid var(--border)',
            }}
            onMouseEnter={e => { if (!active) { e.currentTarget.style.background = bg; e.currentTarget.style.color = color; } }}
            onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.color = 'var(--text-secondary)'; } }}
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
