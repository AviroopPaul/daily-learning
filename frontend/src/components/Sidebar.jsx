import {
  FiServer, FiLayout, FiCpu, FiZap, FiBox, FiGitBranch,
  FiDatabase, FiGlobe, FiLock, FiEye, FiActivity, FiShare2,
  FiInbox, FiCode, FiBookOpen,
} from 'react-icons/fi'

const DOMAIN_ICONS = {
  'Backend': FiServer,
  'Frontend': FiLayout,
  'LLM Training': FiCpu,
  'LLM at Scale': FiZap,
  'Deployment': FiBox,
  'SCM': FiGitBranch,
  'Database': FiDatabase,
  'Networking': FiGlobe,
  'Security': FiLock,
  'Observability': FiEye,
  'Caching': FiActivity,
  'Distributed Systems': FiShare2,
  'Message Queues': FiInbox,
  'API Design': FiCode,
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function Sidebar({ topics, selectedId, onSelect, isOpen, onClose }) {
  return (
    <>
      <div
        className={`sidebar-overlay ${isOpen ? 'open' : ''}`}
        onClick={onClose}
        aria-hidden
      />

      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-title">Topics</div>
          <div className="sidebar-count">
            {topics.length} {topics.length === 1 ? 'entry' : 'entries'}
          </div>
        </div>

        <div className="sidebar-list">
          {topics.length === 0 ? (
            <div className="sidebar-empty">
              No topics yet. First one generates today at 9PM IST.
            </div>
          ) : (
            topics.map((t) => {
              const Icon = DOMAIN_ICONS[t.domain] || FiBookOpen
              return (
                <div
                  key={t.id}
                  className={`sidebar-item ${selectedId === t.id ? 'active' : ''}`}
                  onClick={() => { onSelect(t.id); onClose() }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && onSelect(t.id)}
                >
                  <div className="sidebar-item-date">{formatDate(t.date)}</div>
                  <div className="sidebar-item-title">{t.title}</div>
                  <div className="sidebar-item-domain">
                    <Icon size={11} style={{ flexShrink: 0, marginTop: 1 }} />
                    {t.domain}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </aside>
    </>
  )
}
