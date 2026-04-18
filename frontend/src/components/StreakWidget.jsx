import { useState, useEffect, useRef } from 'react'
import { FiZap } from 'react-icons/fi'
import { getDeviceId } from '../utils/deviceId.js'

function ContributionGraph({ activity }) {
  // Build a 52-week × 7-day grid ending today
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  // Find the Sunday on or before 52 weeks ago
  const startDate = new Date(today)
  startDate.setDate(startDate.getDate() - 364) // 52 weeks back
  // Align to Sunday
  startDate.setDate(startDate.getDate() - startDate.getDay())

  const activitySet = new Set(activity)

  // Build columns (each column = one week, Sun-Sat)
  const columns = []
  const cursor = new Date(startDate)
  while (cursor <= today) {
    const week = []
    for (let d = 0; d < 7; d++) {
      const dateStr = cursor.toISOString().slice(0, 10)
      const isFuture = cursor > today
      week.push({ dateStr, done: activitySet.has(dateStr), isFuture })
      cursor.setDate(cursor.getDate() + 1)
    }
    columns.push(week)
  }

  return (
    <div className="contribution-graph">
      {columns.map((week, wi) => (
        <div key={wi} className="contribution-col">
          {week.map((day, di) => (
            <div
              key={di}
              className={`contribution-cell ${day.done ? 'contribution-cell--done' : ''} ${day.isFuture ? 'contribution-cell--future' : ''}`}
              title={day.isFuture ? '' : `${day.dateStr}${day.done ? ' ✓' : ''}`}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

export default function StreakWidget() {
  const [open, setOpen] = useState(false)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const ref = useRef(null)

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const handleOpen = () => {
    setOpen(prev => !prev)
    if (!data && !loading) {
      setLoading(true)
      const deviceId = getDeviceId()
      fetch(`/api/quiz/streak?device_id=${encodeURIComponent(deviceId)}`)
        .then(r => r.json())
        .then(d => { setData(d); setLoading(false) })
        .catch(() => setLoading(false))
    }
  }

  const streak = data?.current_streak ?? 0

  return (
    <div className="streak-widget" ref={ref}>
      <button
        className={`icon-btn streak-btn ${streak > 0 ? 'streak-btn--active' : ''}`}
        onClick={handleOpen}
        title="Quiz streak"
        aria-label="Quiz streak"
      >
        <FiZap size={15} />
        {streak > 0 && <span className="streak-count">{streak}</span>}
      </button>

      {open && (
        <div className="streak-dropdown">
          <div className="streak-dropdown-header">
            <span className="streak-dropdown-title">Quiz Streak</span>
          </div>

          {loading && (
            <div className="streak-loading">
              <div className="skeleton" style={{ height: 14, width: '60%', marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 80, width: '100%' }} />
            </div>
          )}

          {data && (
            <>
              <div className="streak-stats">
                <div className="streak-stat">
                  <span className="streak-stat-value">{data.current_streak}</span>
                  <span className="streak-stat-label">Current streak</span>
                </div>
                <div className="streak-stat">
                  <span className="streak-stat-value">{data.longest_streak}</span>
                  <span className="streak-stat-label">Longest streak</span>
                </div>
                <div className="streak-stat">
                  <span className="streak-stat-value">{data.total_completed}</span>
                  <span className="streak-stat-label">Total quizzes</span>
                </div>
              </div>

              <div className="streak-graph-label">Last 52 weeks</div>
              <ContributionGraph activity={data.activity} />
            </>
          )}

          {!loading && !data && (
            <p className="streak-empty">Complete quizzes to build your streak.</p>
          )}
        </div>
      )}
    </div>
  )
}
