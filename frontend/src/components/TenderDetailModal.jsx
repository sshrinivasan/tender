import { useEffect, useState } from 'react'

export default function TenderDetailModal({ tender, onClose }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const params = new URLSearchParams({
      url: tender.url,
      source: tender.source,
      title: tender.title,
    })
    fetch(`/tender-detail?${params}`)
      .then(r => {
        if (!r.ok) return r.json().then(e => Promise.reject(e.detail || 'Server error'))
        return r.json()
      })
      .then(data => setDetail(data.detail))
      .catch(err => setError(String(err)))
      .finally(() => setLoading(false))
  }, [tender.url])

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className={`source-pill ${tender.source}`}>
              {{ canadabuys: 'CanadaBuys', merx: 'MERX', procuredata: 'ProcureData', bidsandtenders: 'Bids & Tenders' }[tender.source] ?? tender.source}
            </span>
            <h2>{tender.title}</h2>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="modal-loading">
              <div className="spinner" />
              Fetching and summarizing tender page…
            </div>
          )}
          {error && (
            <p className="modal-error">{error}</p>
          )}
          {detail && (
            <div className="modal-detail">
              <div className="ai-dot" style={{ marginBottom: 12 }}>✦</div>
              <p>{detail}</p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {tender.url && (
            <a className="btn-view" href={tender.url} target="_blank" rel="noreferrer">
              Open original page ↗
            </a>
          )}
          <button className="btn-close-modal" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
