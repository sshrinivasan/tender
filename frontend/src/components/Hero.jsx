const HINTS = [
  'IT consulting',
  'Construction Ontario',
  'Cybersecurity federal',
  'Translation services',
  'Cloud infrastructure',
]

export default function Hero({ query, onChange, onSearch, loading }) {
  function handleKey(e) {
    if (e.key === 'Enter') onSearch()
  }

  return (
    <div className="hero">
      <div className="hero-eyebrow">✦ AI-powered tender discovery</div>
      <h1>
        Find Canadian government<br />
        <span>tenders that match</span> your work
      </h1>
      <p>
        Search across MERX, CanadaBuys, and more — summarized by AI so you can act fast.
      </p>

      <div className="search-wrap">
        <div className="search-bar">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Describe the kind of work you're looking for…"
            value={query}
            onChange={e => onChange(e.target.value)}
            onKeyDown={handleKey}
          />
          <button onClick={onSearch} disabled={loading || !query.trim()}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        <div className="search-hints">
          {HINTS.map(h => (
            <button key={h} className="hint-chip" onClick={() => onChange(h)}>
              {h}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
