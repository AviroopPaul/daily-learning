import { useState, useEffect, useCallback } from 'react'
import {
  FiRefreshCw, FiTrash2, FiZap, FiUsers, FiBook,
  FiSettings, FiLock, FiUnlock, FiBell, FiKey,
  FiCheckCircle, FiAlertCircle, FiCpu,
} from 'react-icons/fi'

const TABS = ['overview', 'topics', 'subjects', 'prompt', 'push']

export default function AdminPanel() {
  // Apply saved theme (MainApp's useTheme doesn't run on /admin)
  useEffect(() => {
    const theme = localStorage.getItem('theme') || 'dark'
    document.documentElement.setAttribute('data-theme', theme)
  }, [])

  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem('adminKey') || '')
  const [authenticated, setAuthenticated] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authLoading, setAuthLoading] = useState(false)

  const [stats, setStats] = useState(null)
  const [topics, setTopics] = useState([])
  const [config, setConfig] = useState({ model: '', system_prompt: '', topic_prompt_template: '' })
  const [models, setModels] = useState([])

  const [subjectAreas, setSubjectAreas] = useState([])
  const [newSubject, setNewSubject] = useState('')
  const [addingSubject, setAddingSubject] = useState(false)
  const [subjectMsg, setSubjectMsg] = useState(null)

  const [selectedModel, setSelectedModel] = useState('')
  const [generating, setGenerating] = useState(false)
  const [genResult, setGenResult] = useState(null)

  const [savingConfig, setSavingConfig] = useState(false)
  const [configMsg, setConfigMsg] = useState(null)

  const [activeTab, setActiveTab] = useState('overview')
  const [pushMsg, setPushMsg] = useState(null)
  const [vapidKeys, setVapidKeys] = useState(null)

  const headers = useCallback(
    () => ({ 'X-Admin-Key': adminKey, 'Content-Type': 'application/json' }),
    [adminKey]
  )

  // ── Auth ────────────────────────────────────────────────────────────────

  const login = async () => {
    setAuthError('')
    setAuthLoading(true)
    try {
      const res = await fetch('/api/admin/stats', { headers: { 'X-Admin-Key': adminKey } })
      if (res.status === 401) { setAuthError('Invalid admin key'); return }
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      sessionStorage.setItem('adminKey', adminKey)
      setAuthenticated(true)
    } catch (e) {
      setAuthError(e.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const logout = () => {
    sessionStorage.removeItem('adminKey')
    setAuthenticated(false)
    setAdminKey('')
  }

  // ── Data loaders ─────────────────────────────────────────────────────────

  const loadStats = useCallback(async () => {
    const res = await fetch('/api/admin/stats', { headers: headers() })
    if (res.ok) setStats(await res.json())
  }, [headers])

  const loadTopics = useCallback(async () => {
    const res = await fetch('/api/admin/topics', { headers: headers() })
    if (res.ok) setTopics(await res.json())
  }, [headers])

  const loadConfig = useCallback(async () => {
    const res = await fetch('/api/admin/config', { headers: headers() })
    if (res.ok) {
      const data = await res.json()
      setConfig(data)
      setSelectedModel(data.model)
    }
  }, [headers])

  const loadModels = useCallback(async () => {
    const res = await fetch('/api/admin/models', { headers: headers() })
    if (res.ok) {
      const data = await res.json()
      setModels(data.models || [])
    }
  }, [headers])

  const loadSubjectAreas = useCallback(async () => {
    const res = await fetch('/api/admin/subject-areas', { headers: headers() })
    if (res.ok) setSubjectAreas(await res.json())
  }, [headers])

  useEffect(() => {
    if (authenticated) {
      loadStats()
      loadTopics()
      loadConfig()
      loadModels()
      loadSubjectAreas()
    }
  }, [authenticated])

  // ── Actions ───────────────────────────────────────────────────────────────

  const handleGenerate = async (force = false) => {
    setGenerating(true)
    setGenResult(null)
    const endpoint = force ? '/api/admin/trigger-force' : '/api/admin/trigger'
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ model: selectedModel || null }),
      })
      const data = await res.json()
      setGenResult({ ok: res.ok, ...data })
    } catch (e) {
      setGenResult({ ok: false, message: e.message })
    } finally {
      setGenerating(false)
      loadStats()
      loadTopics()
    }
  }

  const handleDelete = async (id, title) => {
    if (!confirm(`Delete "${title}"?`)) return
    await fetch(`/api/admin/topics/${id}`, { method: 'DELETE', headers: headers() })
    loadTopics()
    loadStats()
  }

  const handleSaveConfig = async () => {
    setSavingConfig(true)
    setConfigMsg(null)
    try {
      const res = await fetch('/api/admin/config', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify(config),
      })
      if (res.ok) {
        const updated = await res.json()
        setConfig(updated)
        setConfigMsg({ ok: true, text: 'Config saved' })
      } else {
        setConfigMsg({ ok: false, text: 'Save failed' })
      }
    } catch (e) {
      setConfigMsg({ ok: false, text: e.message })
    } finally {
      setSavingConfig(false)
      setTimeout(() => setConfigMsg(null), 3000)
    }
  }

  const handleTestPush = async () => {
    setPushMsg(null)
    const res = await fetch('/api/admin/push/test', { method: 'POST', headers: headers() })
    const data = await res.json()
    setPushMsg({ ok: res.ok, text: data.message })
  }

  const handleAddSubject = async () => {
    const name = newSubject.trim()
    if (!name) return
    setAddingSubject(true)
    setSubjectMsg(null)
    const res = await fetch('/api/admin/subject-areas', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ name }),
    })
    if (res.ok) {
      setNewSubject('')
      loadSubjectAreas()
    } else {
      const data = await res.json()
      setSubjectMsg({ ok: false, text: data.detail || 'Error adding subject' })
      setTimeout(() => setSubjectMsg(null), 3000)
    }
    setAddingSubject(false)
  }

  const handleDeleteSubject = async (id) => {
    await fetch(`/api/admin/subject-areas/${id}`, { method: 'DELETE', headers: headers() })
    loadSubjectAreas()
  }

  const handleCleanup = async () => {
    setPushMsg(null)
    const res = await fetch('/api/admin/push/cleanup', { method: 'POST', headers: headers() })
    const data = await res.json()
    setPushMsg({ ok: res.ok, text: `Removed ${data.removed} stale subscription(s). ${data.remaining} remaining.` })
    loadStats()
  }

  const handleGenerateVapid = async () => {
    if (!confirm('Generate new VAPID keys? Only do this once — existing subscribers will break.')) return
    const res = await fetch('/api/admin/generate-vapid', { headers: headers() })
    const data = await res.json()
    setVapidKeys(data)
  }

  // ── Auth gate ─────────────────────────────────────────────────────────────

  if (!authenticated) {
    return (
      <div className="admin-auth-wrap">
        <div className="admin-auth-card">
          <div className="admin-auth-icon"><FiLock size={24} /></div>
          <h2 className="admin-auth-title">Admin Access</h2>
          <p className="admin-auth-sub">Enter your admin key to continue</p>
          <input
            type="password"
            className="admin-input"
            placeholder="Admin key"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && login()}
            autoFocus
          />
          {authError && (
            <div className="admin-msg admin-msg--error">
              <FiAlertCircle size={13} /> {authError}
            </div>
          )}
          <button className="btn btn-primary" onClick={login} disabled={authLoading || !adminKey}>
            {authLoading ? <div className="loading-spinner loading-spinner--sm" /> : 'Unlock'}
          </button>
        </div>
      </div>
    )
  }

  // ── Main panel ────────────────────────────────────────────────────────────

  return (
    <div className="admin-panel">
      {/* Header */}
      <div className="admin-header">
        <span className="admin-title">admin panel</span>
        <nav className="admin-tabs">
          {TABS.map((tab) => (
            <button
              key={tab}
              className={`admin-tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </nav>
        <button className="icon-btn" onClick={logout} title="Log out">
          <FiUnlock size={15} />
        </button>
      </div>

      {/* Body */}
      <div className="admin-body">

        {/* ── Overview ── */}
        {activeTab === 'overview' && (
          <div className="admin-section">
            {stats && (
              <div className="admin-stats">
                <div className="stat-card">
                  <div className="stat-value"><FiBook size={18} /></div>
                  <div className="stat-number">{stats.topic_count}</div>
                  <div className="stat-label">Topics</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value"><FiUsers size={18} /></div>
                  <div className="stat-number">{stats.subscriber_count}</div>
                  <div className="stat-label">Push Subscribers</div>
                </div>
                <div className="stat-card">
                  <div className={`stat-value ${stats.today_exists ? 'stat-green' : 'stat-amber'}`}>
                    {stats.today_exists ? <FiCheckCircle size={18} /> : <FiAlertCircle size={18} />}
                  </div>
                  <div className="stat-number">{stats.today_exists ? 'Done' : 'Pending'}</div>
                  <div className="stat-label">Today's Topic</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value"><FiCpu size={18} /></div>
                  <div className="stat-number stat-number--sm">{stats.current_model}</div>
                  <div className="stat-label">Active Model</div>
                </div>
              </div>
            )}

            {stats?.today_exists && stats?.today_title && (
              <div className="admin-today">
                <span className="admin-today-label">Today</span>
                <span className="admin-today-title">{stats.today_title}</span>
              </div>
            )}

            <div className="admin-card">
              <div className="admin-card-title">Generate Topic</div>
              <div className="admin-field">
                <label className="admin-label">Model</label>
                <select
                  className="admin-select"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  {models.length === 0 && (
                    <option value="">(loading models…)</option>
                  )}
                  {models.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div className="admin-actions">
                <button
                  className="btn btn-ghost"
                  onClick={() => handleGenerate(false)}
                  disabled={generating}
                >
                  {generating
                    ? <div className="loading-spinner loading-spinner--sm" />
                    : <FiRefreshCw size={13} />}
                  Generate (skip if today exists)
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => handleGenerate(true)}
                  disabled={generating}
                >
                  <FiZap size={13} />
                  Force Regenerate
                </button>
              </div>
              {genResult && (
                <div className={`admin-msg ${genResult.ok ? 'admin-msg--success' : 'admin-msg--error'}`}>
                  {genResult.ok ? <FiCheckCircle size={13} /> : <FiAlertCircle size={13} />}
                  {genResult.message}
                  {genResult.topic && <> — <em>{genResult.topic.title}</em></>}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Topics ── */}
        {activeTab === 'topics' && (
          <div className="admin-section">
            <div className="admin-card">
              <div className="admin-card-title">All Topics <span className="admin-count">{topics.length}</span></div>
              <div className="admin-topic-list">
                {topics.length === 0 && (
                  <div className="admin-empty">No topics yet.</div>
                )}
                {topics.map((t) => (
                  <div key={t.id} className="admin-topic-row">
                    <span className="admin-topic-date">{t.date}</span>
                    <span className="admin-topic-title">{t.title}</span>
                    <span className="admin-topic-domain">{t.domain}</span>
                    <span className={`badge badge-${t.difficulty.toLowerCase()}`}>{t.difficulty}</span>
                    <button
                      className="icon-btn icon-btn--danger"
                      onClick={() => handleDelete(t.id, t.title)}
                      title="Delete topic"
                    >
                      <FiTrash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Subjects ── */}
        {activeTab === 'subjects' && (
          <div className="admin-section">
            <div className="admin-card">
              <div className="admin-card-title">
                Prompt Subject Areas
                <span className="admin-count">{subjectAreas.length}</span>
              </div>
              <p className="admin-hint">
                These are injected into the generation prompt. The LLM picks one that hasn't been covered recently.
              </p>

              {/* Add new */}
              <div className="admin-subject-add">
                <input
                  className="admin-input"
                  placeholder="Add a subject area…"
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddSubject()}
                />
                <button
                  className="btn btn-primary"
                  onClick={handleAddSubject}
                  disabled={addingSubject || !newSubject.trim()}
                >
                  Add
                </button>
              </div>
              {subjectMsg && (
                <div className={`admin-msg ${subjectMsg.ok ? 'admin-msg--success' : 'admin-msg--error'}`}>
                  <FiAlertCircle size={13} /> {subjectMsg.text}
                </div>
              )}

              {/* List */}
              <div className="admin-subject-list">
                {subjectAreas.map((s) => (
                  <div key={s.id} className="admin-subject-row">
                    <span className="admin-subject-name">{s.name}</span>
                    <button
                      className="icon-btn icon-btn--danger"
                      onClick={() => handleDeleteSubject(s.id)}
                      title="Remove"
                    >
                      <FiTrash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Prompt ── */}
        {activeTab === 'prompt' && (
          <div className="admin-section">
            <div className="admin-card">
              <div className="admin-card-title">LLM Configuration</div>
              <div className="admin-field">
                <label className="admin-label">Active Model</label>
                <select
                  className="admin-select"
                  value={config.model}
                  onChange={(e) => setConfig((c) => ({ ...c, model: e.target.value }))}
                >
                  {models.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                <div className="admin-hint">Persists for the lifetime of the process. Override per-generation in Overview.</div>
              </div>
              <div className="admin-field">
                <label className="admin-label">System Prompt</label>
                <textarea
                  className="admin-textarea"
                  value={config.system_prompt}
                  onChange={(e) => setConfig((c) => ({ ...c, system_prompt: e.target.value }))}
                  rows={6}
                  spellCheck={false}
                />
              </div>
              <div className="admin-field">
                <label className="admin-label">Topic Prompt Template</label>
                <textarea
                  className="admin-textarea"
                  value={config.topic_prompt_template}
                  onChange={(e) => setConfig((c) => ({ ...c, topic_prompt_template: e.target.value }))}
                  rows={9}
                  spellCheck={false}
                />
                <div className="admin-hint">Available variables: <code>&#123;date&#125;</code>, <code>&#123;previous_topics&#125;</code></div>
              </div>
              <div className="admin-actions">
                <button className="btn btn-primary" onClick={handleSaveConfig} disabled={savingConfig}>
                  {savingConfig ? 'Saving…' : 'Save Config'}
                </button>
                <button
                  className="btn btn-ghost"
                  onClick={loadConfig}
                >
                  Reset
                </button>
                {configMsg && (
                  <span className={`admin-msg ${configMsg.ok ? 'admin-msg--success' : 'admin-msg--error'}`}>
                    {configMsg.ok ? <FiCheckCircle size={13} /> : <FiAlertCircle size={13} />}
                    {configMsg.text}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Push ── */}
        {activeTab === 'push' && (
          <div className="admin-section">
            <div className="admin-card">
              <div className="admin-card-title">Push Notifications</div>
              {stats && (
                <div className="admin-push-stat">
                  <FiUsers size={14} />
                  {stats.subscriber_count} active subscriber{stats.subscriber_count !== 1 ? 's' : ''}
                </div>
              )}
              <div className="admin-actions">
                <button className="btn btn-ghost" onClick={handleTestPush}>
                  <FiBell size={13} /> Send Test Push
                </button>
                <button className="btn btn-ghost" onClick={handleCleanup}>
                  <FiRefreshCw size={13} /> Clean Stale Subscriptions
                </button>
              </div>
              {pushMsg && (
                <div className={`admin-msg ${pushMsg.ok ? 'admin-msg--success' : 'admin-msg--error'}`}>
                  {pushMsg.ok ? <FiCheckCircle size={13} /> : <FiAlertCircle size={13} />}
                  {pushMsg.text}
                </div>
              )}
            </div>

            <div className="admin-card">
              <div className="admin-card-title">VAPID Keys</div>
              <p className="admin-hint" style={{ marginBottom: 12 }}>
                Only generate once. Regenerating breaks all existing subscriptions.
              </p>
              <button className="btn btn-ghost" onClick={handleGenerateVapid}>
                <FiKey size={13} /> Generate New VAPID Keys
              </button>
              {vapidKeys && (
                <div className="admin-vapid">
                  <div className="admin-vapid-row">
                    <span className="admin-vapid-label">VAPID_PRIVATE_KEY</span>
                    <code className="admin-vapid-value">{vapidKeys.VAPID_PRIVATE_KEY}</code>
                  </div>
                  <div className="admin-vapid-row">
                    <span className="admin-vapid-label">VAPID_PUBLIC_KEY</span>
                    <code className="admin-vapid-value">{vapidKeys.VAPID_PUBLIC_KEY}</code>
                  </div>
                  <div className="admin-hint">{vapidKeys.note}</div>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
