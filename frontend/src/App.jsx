import { useState } from 'react'
import Nav from './components/Nav'
import Hero from './components/Hero'
import Sidebar from './components/Sidebar'
import AISummary from './components/AISummary'
import TenderCard from './components/TenderCard'

const DEFAULT_FILTERS = { source: 'all', closing_days: null, regions: [] }

export default function App() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [results, setResults] = useState(null)   // { summary, tenders }
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSearch() {
    const q = query.trim()
    if (!q) return

    setLoading(true)
    setError(null)

    try {
      const res = await fetch('/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          source: filters.source,
          closing_days: filters.closing_days,
          regions: filters.regions.length > 0 ? filters.regions : null,
        }),
      })

      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const tenders = results?.tenders ?? []
  const hasResults = tenders.length > 0

  return (
    <>
      <Nav />
      <Hero
        query={query}
        onChange={setQuery}
        onSearch={handleSearch}
        loading={loading}
      />

      {/* Stats bar */}
      <div className="stats-bar">
        <div className="stat">
          <span className="stat-num">
            {results ? tenders.length : '—'}
          </span>
          <span className="stat-label">
            {results ? 'results found' : 'results'}
          </span>
        </div>
        <div className="stat-divider" />
        <div className="stat">
          <span className="stat-num">2</span>
          <span className="stat-label">sources indexed</span>
        </div>
        <div className="stat-divider" />
        <div className="stat">
          <span className="stat-num">Updated daily</span>
        </div>
      </div>

      <div className="body">
        <Sidebar filters={filters} onChange={setFilters} />

        <section>
          {!results && !loading && (
            <div className="empty-state">
              Enter a search query above to find relevant tenders.
            </div>
          )}

          {loading && (
            <div className="loading-spinner">
              <div className="spinner" />
              Searching and summarizing tenders…
            </div>
          )}

          {error && (
            <div className="empty-state" style={{ color: 'var(--red)' }}>
              {error}
            </div>
          )}

          {results && !loading && (
            <>
              <div className="results-bar">
                <p>
                  <strong>{tenders.length} result{tenders.length !== 1 ? 's' : ''}</strong>
                  {' '}for "{query}"
                </p>
              </div>

              <AISummary summary={results.summary} />

              {hasResults ? (
                tenders.map((tender, i) => (
                  <TenderCard key={`${tender.title}-${i}`} tender={tender} />
                ))
              ) : (
                <div className="empty-state">No tenders matched your query.</div>
              )}
            </>
          )}
        </section>
      </div>
    </>
  )
}
