const SEVEN_DAYS = 7 * 24 * 60 * 60

export default function TenderCard({ tender }) {
  const nowTs = Math.floor(Date.now() / 1000)
  const isClosingSoon =
    tender.closing_date_ts > 0 &&
    tender.closing_date_ts - nowTs <= SEVEN_DAYS &&
    tender.closing_date_ts >= nowTs

  const daysUntil = tender.closing_date_ts > 0
    ? Math.ceil((tender.closing_date_ts - nowTs) / 86400)
    : null

  return (
    <div className="tender-card">
      <div className="card-header">
        <h2>{tender.title || 'Untitled Tender'}</h2>
        <span className={`source-pill ${tender.source}`}>
          {{ canadabuys: 'CanadaBuys', merx: 'MERX', procuredata: 'ProcureData' }[tender.source] ?? tender.source}
        </span>
      </div>

      <div className="card-meta">
        {tender.organization && (
          <span className="meta">Org: <strong>{tender.organization}</strong></span>
        )}
        {tender.closing_date && (
          <span className="meta">Closes: <strong>{tender.closing_date}</strong></span>
        )}
        {tender.region && (
          <span className="meta">Region: <strong>{tender.region}</strong></span>
        )}
      </div>

      <div className="card-footer">
        {isClosingSoon && daysUntil !== null ? (
          <span className="closing-soon">
            Closing in {daysUntil} day{daysUntil !== 1 ? 's' : ''}
          </span>
        ) : (
          <div />
        )}
        {tender.url ? (
          <a className="btn-view" href={tender.url} target="_blank" rel="noreferrer">
            View tender
          </a>
        ) : (
          <span className="btn-view disabled">View tender</span>
        )}
      </div>
    </div>
  )
}
