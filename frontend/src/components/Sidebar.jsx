export const REGIONS = [
  'National',
  'NCR',
  'Ontario',
  'Quebec',
  'British Columbia',
  'Alberta',
  'Saskatchewan',
  'Manitoba',
  'New Brunswick',
  'Nova Scotia',
  'Prince Edward Island',
  'Newfoundland',
  'Northwest Territories',
  'Nunavut',
  'Yukon',
  'International',
]

export default function Sidebar({ filters, onChange }) {
  function setSource(source) {
    onChange({ ...filters, source })
  }

  function setClosingDays(closing_days) {
    onChange({ ...filters, closing_days })
  }

  function toggleRegion(region) {
    const current = filters.regions
    const updated = current.includes(region)
      ? current.filter(r => r !== region)
      : [...current, region]
    onChange({ ...filters, regions: updated })
  }

  return (
    <aside>
      <div className="filter-group">
        <h4>Source</h4>
        {[['all', 'All'], ['merx', 'MERX'], ['canadabuys', 'CanadaBuys'], ['procuredata', 'ProcureData']].map(([val, label]) => (
          <div className="filter-option" key={val}>
            <label>
              <input
                type="radio"
                name="source"
                checked={filters.source === val}
                onChange={() => setSource(val)}
              />
              {label}
            </label>
          </div>
        ))}
      </div>

      <div className="filter-group">
        <h4>Closing Date</h4>
        {[[null, 'Any'], [7, 'Next 7 days'], [30, 'Next 30 days']].map(([val, label]) => (
          <div className="filter-option" key={label}>
            <label>
              <input
                type="radio"
                name="closing"
                checked={filters.closing_days === val}
                onChange={() => setClosingDays(val)}
              />
              {label}
            </label>
          </div>
        ))}
      </div>

      <div className="filter-group">
        <h4>Region</h4>
        {REGIONS.map(r => (
          <div className="filter-option" key={r}>
            <label>
              <input
                type="checkbox"
                checked={filters.regions.includes(r)}
                onChange={() => toggleRegion(r)}
              />
              {r}
            </label>
          </div>
        ))}
      </div>
    </aside>
  )
}
