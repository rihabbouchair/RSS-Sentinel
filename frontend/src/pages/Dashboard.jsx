import { useState, useEffect } from 'react';
import { getArticles, refreshArticles, refreshTopic } from '../api';
import ArticleCard from '../components/ArticleCard';
import FilterBar from '../components/FilterBar';
import DailySummary from '../components/DailySummary';

export default function Dashboard({ selectedTopic }) {
  const [articles, setArticles] = useState([]);
  const [allArticles, setAllArticles] = useState([]);
  const [selectedSentiment, setSelectedSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const articlesPerPage = 20;

  useEffect(() => { loadArticles(); }, [selectedTopic, selectedSentiment]);

  useEffect(() => {
    // Load all articles (no filter) for the summary
    loadAllArticles();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => loadArticles(true), 10000);
    return () => clearInterval(interval);
  }, [selectedTopic, selectedSentiment]);

  async function loadAllArticles() {
    try {
      const data = await getArticles({ limit: 100 });
      setAllArticles(data);
    } catch (error) {
      console.error('Failed to load all articles:', error);
    }
  }

  async function loadArticles(isAutoRefresh = false) {
    if (!isAutoRefresh) setLoading(true);
    else setFetching(true);
    try {
      const data = await getArticles({ feedTopic: selectedTopic, sentiment: selectedSentiment, limit: 100 });
      setArticles(data);

      // If backend returned fallback articles (marked with is_fallback), trigger a topic refresh
      // and poll until real topic-specific articles are available.
      if (selectedTopic && data && data.length > 0 && data.some(a => a.is_fallback)) {
        triggerTopicPrewarm(selectedTopic);
      }

      // Keep summary source fresh even while filters are active.
      const summaryData = await getArticles({ limit: 100 });
      setAllArticles(summaryData);

      if (!isAutoRefresh) setCurrentPage(1);
    } catch (error) {
      console.error('Failed to load articles:', error);
    } finally {
      setLoading(false);
      setFetching(false);
    }
  }

  async function triggerTopicPrewarm(topic) {
    try {
      await refreshTopic(topic);
    } catch (err) {
      console.error('Failed to request topic refresh:', err);
    }

    // Poll every 2s up to 20s for new non-fallback articles
    const start = Date.now();
    const interval = setInterval(async () => {
      try {
        const latest = await getArticles({ feedTopic: topic, limit: 20 });
        const nonFallback = latest.filter(a => !a.is_fallback);
        if (nonFallback.length > 0 || Date.now() - start > 20000) {
          // update list with whichever we have (prefer non-fallback)
          setArticles(nonFallback.length > 0 ? latest : latest);
          setFetching(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Polling for topic articles failed:', err);
      }
    }, 2000);
  }

  async function handleRefreshPipeline() {
    setRefreshing(true);
    try {
      await refreshArticles();
      // Wait 2 seconds then reload articles
      setTimeout(() => {
        loadArticles();
        loadAllArticles();
        setRefreshing(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to refresh pipeline:', error);
      setRefreshing(false);
    }
  }

  const totalPages = Math.ceil(articles.length / articlesPerPage);
  const startIndex = (currentPage - 1) * articlesPerPage;
  const currentArticles = articles.slice(startIndex, startIndex + articlesPerPage);
  const uniqueSources = new Set(articles.map(a => a.feed_id)).size;

  // Stats
  const pos = articles.filter(a => a.sentiment === 'Positive').length;
  const neg = articles.filter(a => a.sentiment === 'Negative').length;
  const neu = articles.filter(a => a.sentiment === 'Neutral').length;
  const total = articles.length;
  const pct = (n) => total > 0 ? Math.round((n / total) * 100) : 0;

  const kpis = [
    {
      label: 'Total Articles', value: total, color: '#a78bfa',
      icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>,
    },
    {
      label: 'Positive', value: `${pct(pos)}%`, sub: `${pos} articles`, color: '#4ade80',
      icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>,
    },
    {
      label: 'Negative', value: `${pct(neg)}%`, sub: `${neg} articles`, color: '#fb7185',
      icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
    },
    {
      label: 'Neutral', value: `${pct(neu)}%`, sub: `${neu} articles`, color: '#94a3b8',
      icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/></svg>,
    },
  ];

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: 'var(--bg-base)', padding: '24px' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>

        {/* Daily AI Summary — always visible at top */}
        <DailySummary articles={allArticles.length > 0 ? allArticles : articles} />

        {/* KPI cards */}
        {!loading && articles.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
            {kpis.map(({ label, value, sub, color, icon }) => (
              <div key={label} style={{
                background: 'var(--bg-surface)',
                border: '0.5px solid var(--border)',
                borderRadius: '12px',
                padding: '14px 16px',
                borderTop: `2px solid ${color}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px', color, fontSize: '11px' }}>
                  {icon} {label}
                </div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: 'var(--text-primary)', lineHeight: 1 }}>{value}</div>
                {sub && <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>{sub}</div>}
              </div>
            ))}
          </div>
        )}

        {/* Header */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div>
              <h1 style={{ fontSize: '17px', fontWeight: '600', color: 'var(--text-primary)', margin: 0 }}>
                {selectedTopic ? `${selectedTopic} Articles` : 'All Articles'}
              </h1>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', marginTop: '3px' }}>
                {articles.length} articles · {uniqueSources} sources
                {(fetching || refreshing) && <span style={{ color: '#a78bfa', marginLeft: '8px' }}>· refreshing...</span>}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {totalPages > 1 && (
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace' }}>
                  Page {currentPage} / {totalPages}
                </div>
              )}
              <button
                onClick={handleRefreshPipeline}
                disabled={refreshing}
                style={{
                  padding: '6px 12px',
                  background: refreshing ? '#6b7280' : '#8b5cf6',
                  border: 'none',
                  borderRadius: '6px',
                  color: 'white',
                  fontSize: '11px',
                  fontWeight: '500',
                  cursor: refreshing ? 'not-allowed' : 'pointer',
                  opacity: refreshing ? 0.6 : 1,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => !refreshing && (e.target.style.background = '#7c3aed')}
                onMouseLeave={(e) => !refreshing && (e.target.style.background = '#8b5cf6')}
              >
                {refreshing ? 'Refreshing...' : '↻ Refresh Now'}
              </button>
            </div>
          </div>
          <FilterBar selectedSentiment={selectedSentiment} onSentimentChange={setSelectedSentiment} />
        </div>

        {/* Articles */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '13px' }}>Loading articles...</div>
          </div>
        ) : articles.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>No articles found.</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>Pipeline is fetching articles, check back soon...</div>
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {currentArticles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>

            {totalPages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '24px' }}>
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  style={{
                    padding: '7px 18px', borderRadius: '8px', fontSize: '12px',
                    fontFamily: 'DM Mono, monospace', cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                    background: 'var(--bg-surface)', border: '0.5px solid var(--border)',
                    color: currentPage === 1 ? 'var(--text-muted)' : 'var(--text-primary)',
                    opacity: currentPage === 1 ? 0.5 : 1,
                  }}
                >
                  Previous
                </button>
                <div style={{
                  padding: '7px 18px', borderRadius: '8px', fontSize: '12px',
                  fontFamily: 'DM Mono, monospace',
                  background: 'rgba(124,58,237,0.15)',
                  border: '0.5px solid rgba(124,58,237,0.3)', color: '#a78bfa',
                }}>
                  {currentPage} / {totalPages}
                </div>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  style={{
                    padding: '7px 18px', borderRadius: '8px', fontSize: '12px',
                    fontFamily: 'DM Mono, monospace', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                    background: 'var(--bg-surface)', border: '0.5px solid var(--border)',
                    color: currentPage === totalPages ? 'var(--text-muted)' : 'var(--text-primary)',
                    opacity: currentPage === totalPages ? 0.5 : 1,
                  }}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
