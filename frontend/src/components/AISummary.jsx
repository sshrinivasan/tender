export default function AISummary({ summary }) {
  if (!summary) return null
  return (
    <div className="ai-card">
      <div className="ai-dot">✦</div>
      <p>{summary}</p>
    </div>
  )
}
