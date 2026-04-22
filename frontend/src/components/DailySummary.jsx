import { useState, useEffect, useRef } from 'react';
import { getArticles, getTopics } from '../api';

const ANTHROPIC_KEY_STORAGE = 'rss_anthropic_key';

function SparkleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
    </svg>
  );
}

function TrendIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
      <polyline points="17 6 23 6 23 12"/>
    </svg>
  );
}

function TopicIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4"/>
    </svg>
  );
}

const topicColors = {
  AI: '#a78bfa', Tech: '#38bdf8', Politics: '#fb923c',
  Sport: '#fb7185', Economy: '#4ade80', Science: '#34d399',
};

function parseSummaryResponse(text) {
  // Extract trending topics section
  const trendsMatch = text.match(/##?\s*Tendances|##?\s*Trending|##?\s*🔥/i);
  const topicsMatch = text.match(/##?\s*Topics|##?\s*Analyse|##?\s*📊/i);

  // Try to parse structured JSON if model returned it
  try {
    const jsonMatch = text.match(/```json\s*([\s\S]*?)```/);
    if (jsonMatch) return JSON.parse(jsonMatch[1]);
  } catch {}

  // Fallback: return raw text split by sections
  return { raw: text };
}

export default function DailySummary({ articles }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem(ANTHROPIC_KEY_STORAGE) || '');
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [lastGenerated, setLastGenerated] = useState(null);
  const [streaming, setStreaming] = useState('');
  const generatedTodayRef = useRef(false);

  const today = new Date().toDateString();

  useEffect(() => {
    // Auto-generate if we have key and articles and haven't generated today
    const cachedDate = sessionStorage.getItem('summary_date');
    const cachedSummary = sessionStorage.getItem('summary_data');
    if (cachedDate === today && cachedSummary) {
      setSummary(JSON.parse(cachedSummary));
      setLastGenerated(cachedDate);
      return;
    }
    if (apiKey && articles.length > 0 && !generatedTodayRef.current) {
      generatedTodayRef.current = true;
      generateSummary();
    }
  }, [articles, apiKey]);

  async function generateSummary() {
    if (!apiKey) { setShowKeyInput(true); return; }
    if (articles.length === 0) return;

    setLoading(true);
    setError(null);
    setStreaming('');

    // Prepare article data for Claude
    const topicGroups = {};
    articles.forEach(a => {
      const cat = a.category || 'Other';
      if (!topicGroups[cat]) topicGroups[cat] = { positive: 0, negative: 0, neutral: 0, titles: [] };
      const s = (a.sentiment || 'Neutral').toLowerCase();
      topicGroups[cat][s] = (topicGroups[cat][s] || 0) + 1;
      if (topicGroups[cat].titles.length < 3) topicGroups[cat].titles.push(a.title);
    });

    const topTitles = articles
      .sort((a, b) => (a.sentiment === 'Positive' ? -1 : 1))
      .slice(0, 12)
      .map(a => `[${a.sentiment}] [${a.category}] ${a.title}`)
      .join('\n');

    const prompt = `Tu es un analyste de presse AI. Voici les actualités du ${new Date().toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })} collectées depuis des flux RSS.

DONNÉES PAR TOPIC:
${Object.entries(topicGroups).map(([topic, data]) => 
  `${topic}: ${data.positive} positifs, ${data.negative} négatifs, ${data.neutral} neutres\nExemples: ${data.titles.join(' | ')}`
).join('\n\n')}

TOP TITRES:
${topTitles}

Génère une analyse quotidienne JSON avec cette structure EXACTE (réponds UNIQUEMENT avec le JSON, sans markdown):
{
  "headline": "Phrase d'accroche percutante résumant la journée en max 12 mots",
  "overview": "2-3 phrases de résumé de l'ambiance générale de l'actualité du jour",
  "trending": [
    {"topic": "nom du sujet chaud", "reason": "pourquoi c'est trending en 8 mots max", "sentiment": "positive|negative|neutral"},
    {"topic": "...", "reason": "...", "sentiment": "..."},
    {"topic": "...", "reason": "...", "sentiment": "..."}
  ],
  "topicAnalysis": [
    {"name": "AI", "mood": "optimiste|tendu|stable|mitigé", "insight": "observation clé en 10 mots max", "dominant": "Positive|Negative|Neutral"},
    {"name": "Tech", "mood": "...", "insight": "...", "dominant": "..."},
    {"name": "Politics", "mood": "...", "insight": "...", "dominant": "..."}
  ],
  "watchout": "1 signal faible ou risque à surveiller aujourd'hui, max 15 mots"
}`;

    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          stream: true,
          messages: [{ role: 'user', content: prompt }],
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error?.message || `API Error ${response.status}`);
      }

      // Stream the response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '));
        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'content_block_delta' && data.delta?.text) {
              fullText += data.delta.text;
              setStreaming(fullText);
            }
          } catch {}
        }
      }

      // Parse the final JSON
      const cleaned = fullText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      const parsed = JSON.parse(cleaned);
      setSummary(parsed);
      setLastGenerated(today);
      sessionStorage.setItem('summary_date', today);
      sessionStorage.setItem('summary_data', JSON.stringify(parsed));

    } catch (err) {
      if (err.message.includes('401') || err.message.includes('invalid')) {
        setError('Clé API invalide. Vérifiez votre clé Anthropic.');
        setShowKeyInput(true);
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
      setStreaming('');
    }
  }

  function saveApiKey(key) {
    localStorage.setItem(ANTHROPIC_KEY_STORAGE, key);
    setApiKey(key);
    setShowKeyInput(false);
    generatedTodayRef.current = false;
    generateSummary();
  }

  const sentimentColor = (s) => {
    if (!s) return '#94a3b8';
    const sl = s.toLowerCase();
    if (sl === 'positive') return '#4ade80';
    if (sl === 'negative') return '#fb7185';
    return '#94a3b8';
  };

  const moodColor = (mood) => {
    if (!mood) return '#94a3b8';
    const m = mood.toLowerCase();
    if (m.includes('optim') || m.includes('posit')) return '#4ade80';
    if (m.includes('tend') || m.includes('négatif') || m.includes('criti')) return '#fb7185';
    if (m.includes('mitig') || m.includes('neutr')) return '#94a3b8';
    return '#a78bfa';
  };

  // API Key setup screen
  if (showKeyInput) {
    return (
      <div style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid rgba(167,139,250,0.3)',
        borderRadius: '12px',
        padding: '20px 24px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a78bfa' }}>
          <SparkleIcon />
          <span style={{ fontSize: '13px', fontWeight: '500' }}>Résumé IA quotidien</span>
        </div>
        <div style={{ flex: 1, display: 'flex', gap: '8px', minWidth: '280px' }}>
          <input
            type="password"
            placeholder="sk-ant-api... (clé Anthropic)"
            defaultValue={apiKey}
            id="api-key-input"
            style={{
              flex: 1, padding: '8px 12px',
              background: 'rgba(255,255,255,0.05)',
              border: '0.5px solid var(--border)',
              borderRadius: '8px',
              color: 'var(--text-primary)', fontSize: '12px',
              fontFamily: 'DM Mono, monospace', outline: 'none',
            }}
          />
          <button
            onClick={() => saveApiKey(document.getElementById('api-key-input').value.trim())}
            style={{
              padding: '8px 16px', borderRadius: '8px',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              border: 'none', color: 'white', fontSize: '12px',
              fontWeight: '500', cursor: 'pointer', whiteSpace: 'nowrap',
            }}
          >
            Activer
          </button>
          <button
            onClick={() => setShowKeyInput(false)}
            style={{
              padding: '8px 12px', borderRadius: '8px',
              background: 'transparent', border: '0.5px solid var(--border)',
              color: 'var(--text-muted)', fontSize: '12px', cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>
        <div style={{ width: '100%', fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace' }}>
          Votre clé est stockée localement dans le navigateur · <a href="https://console.anthropic.com" target="_blank" style={{ color: '#a78bfa' }}>Obtenir une clé →</a>
        </div>
      </div>
    );
  }

  // Loading / streaming state
  if (loading) {
    return (
      <div style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid rgba(167,139,250,0.2)',
        borderRadius: '12px',
        padding: '20px 24px',
        marginBottom: '20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <div style={{ color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="pulse-dot" style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#a78bfa', display: 'inline-block' }}></span>
            <SparkleIcon />
            <span style={{ fontSize: '12px', fontWeight: '500' }}>Claude analyse vos actualités...</span>
          </div>
        </div>
        {streaming && (
          <div style={{
            fontSize: '11px', color: 'var(--text-muted)',
            fontFamily: 'DM Mono, monospace',
            maxHeight: '60px', overflow: 'hidden',
            opacity: 0.6, lineHeight: 1.5,
          }}>
            {streaming.slice(-200)}
            <span className="pulse-dot" style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#a78bfa', marginLeft: '4px', verticalAlign: 'middle' }}></span>
          </div>
        )}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{
        background: 'rgba(251,113,133,0.06)',
        border: '0.5px solid rgba(251,113,133,0.2)',
        borderRadius: '12px', padding: '14px 18px',
        marginBottom: '20px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px',
      }}>
        <span style={{ fontSize: '12px', color: '#fb7185' }}>⚠ {error}</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => { setError(null); setShowKeyInput(true); }} style={{ fontSize: '11px', color: '#a78bfa', background: 'none', border: 'none', cursor: 'pointer' }}>Changer la clé</button>
          <button onClick={() => { setError(null); generatedTodayRef.current = false; generateSummary(); }} style={{ fontSize: '11px', color: '#a78bfa', background: 'none', border: 'none', cursor: 'pointer' }}>Réessayer</button>
        </div>
      </div>
    );
  }

  // No key yet
  if (!apiKey && !summary) {
    return (
      <div style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid rgba(167,139,250,0.15)',
        borderRadius: '12px', padding: '16px 20px',
        marginBottom: '20px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#a78bfa' }}><SparkleIcon /></span>
          <div>
            <span style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text-primary)' }}>Résumé IA du jour</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '8px' }}>Activez Claude pour analyser vos actualités</span>
          </div>
        </div>
        <button
          onClick={() => setShowKeyInput(true)}
          style={{
            padding: '7px 16px', borderRadius: '8px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            border: 'none', color: 'white', fontSize: '12px',
            fontWeight: '500', cursor: 'pointer',
          }}
        >
          Configurer →
        </button>
      </div>
    );
  }

  // Summary display
  if (!summary) return null;

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '0.5px solid rgba(167,139,250,0.25)',
      borderRadius: '14px',
      marginBottom: '20px',
      overflow: 'hidden',
    }}
    className="animate-fade-in"
    >
      {/* Header bar */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08))',
        borderBottom: '0.5px solid rgba(167,139,250,0.15)',
        padding: '14px 20px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#a78bfa' }}><SparkleIcon /></span>
          <span style={{ fontSize: '12px', fontWeight: '500', color: '#a78bfa' }}>Briefing IA du jour</span>
          <span style={{
            fontSize: '10px', padding: '1px 7px', borderRadius: '20px',
            background: 'rgba(167,139,250,0.15)', color: '#a78bfa',
            fontFamily: 'DM Mono, monospace',
          }}>
            {new Date().toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace' }}>
            {articles.length} articles analysés
          </span>
          <button
            onClick={() => { sessionStorage.clear(); setSummary(null); generatedTodayRef.current = false; generateSummary(); }}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '11px', padding: '2px 6px',
              borderRadius: '4px', transition: 'color 0.15s',
            }}
            title="Régénérer"
            onMouseEnter={e => e.target.style.color = '#a78bfa'}
            onMouseLeave={e => e.target.style.color = 'var(--text-muted)'}
          >
            ↻
          </button>
          <button
            onClick={() => setShowKeyInput(true)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '10px', padding: '2px 6px',
            }}
            title="Changer la clé API"
          >
            ⚙
          </button>
        </div>
      </div>

      <div style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Headline + overview */}
        <div>
          {summary.headline && (
            <h2 style={{
              fontSize: '16px', fontWeight: '600',
              color: 'var(--text-primary)', margin: '0 0 8px',
              lineHeight: 1.35,
            }}>
              {summary.headline}
            </h2>
          )}
          {summary.overview && (
            <p style={{
              fontSize: '13px', color: 'var(--text-secondary)',
              lineHeight: '1.65', margin: 0,
            }}>
              {summary.overview}
            </p>
          )}
        </div>

        {/* Two columns: trending + topic analysis */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>

          {/* Trending topics */}
          {summary.trending?.length > 0 && (
            <div style={{
              background: 'rgba(255,255,255,0.03)',
              border: '0.5px solid var(--border)',
              borderRadius: '10px', padding: '14px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                <span style={{ color: '#fb923c' }}><TrendIcon /></span>
                <span style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Tendances du jour
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '9px' }}>
                {summary.trending.map((t, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    <span style={{
                      fontSize: '10px', fontFamily: 'DM Mono, monospace',
                      color: 'var(--text-muted)', minWidth: '14px', paddingTop: '1px',
                    }}>
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                        <span style={{ fontSize: '12px', fontWeight: '500', color: 'var(--text-primary)' }}>
                          {t.topic}
                        </span>
                        <span style={{
                          width: '5px', height: '5px', borderRadius: '50%',
                          background: sentimentColor(t.sentiment), flexShrink: 0,
                        }} />
                      </div>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                        {t.reason}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Topic analysis */}
          {summary.topicAnalysis?.length > 0 && (
            <div style={{
              background: 'rgba(255,255,255,0.03)',
              border: '0.5px solid var(--border)',
              borderRadius: '10px', padding: '14px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                <span style={{ color: '#38bdf8' }}><TopicIcon /></span>
                <span style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Analyse par topic
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '9px' }}>
                {summary.topicAnalysis.map((t, i) => {
                  const tc = topicColors[t.name] || '#a78bfa';
                  const mc = moodColor(t.mood);
                  return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        fontSize: '10px', fontFamily: 'DM Mono, monospace',
                        padding: '2px 7px', borderRadius: '4px',
                        background: `${tc}18`, color: tc,
                        minWidth: '52px', textAlign: 'center', flexShrink: 0,
                      }}>
                        {t.name}
                      </span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                          <span style={{
                            fontSize: '10px', fontFamily: 'DM Mono, monospace',
                            color: mc, fontWeight: '500',
                          }}>
                            {t.mood}
                          </span>
                        </div>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                          {t.insight}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Watchout banner */}
        {summary.watchout && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '10px',
            padding: '10px 14px', borderRadius: '8px',
            background: 'rgba(251,146,60,0.08)',
            border: '0.5px solid rgba(251,146,60,0.2)',
          }}>
            <span style={{ fontSize: '13px' }}>⚠️</span>
            <div>
              <span style={{ fontSize: '10px', fontWeight: '500', color: '#fb923c', marginRight: '8px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                À surveiller
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {summary.watchout}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
