import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header.jsx'
import Sidebar from './components/Sidebar.jsx'
import TopicDetail from './components/TopicDetail.jsx'
import AdminPanel from './components/AdminPanel.jsx'

const FONT_SIZES = ['sm', 'md', 'lg', 'xl']

function useFontSize() {
  const [fontSize, setFontSize] = useState(() => {
    return localStorage.getItem('fontSize') || 'md'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-font-size', fontSize)
    localStorage.setItem('fontSize', fontSize)
  }, [fontSize])

  const increase = () => setFontSize((f) => {
    const i = FONT_SIZES.indexOf(f)
    return FONT_SIZES[Math.min(i + 1, FONT_SIZES.length - 1)]
  })
  const decrease = () => setFontSize((f) => {
    const i = FONT_SIZES.indexOf(f)
    return FONT_SIZES[Math.max(i - 1, 0)]
  })
  return { fontSize, increase, decrease }
}

function useTheme() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
    // Update meta theme-color
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) meta.content = theme === 'dark' ? '#0f0f0f' : '#fafaf8'
  }, [theme])

  const toggle = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))
  return { theme, toggle }
}

function MainApp() {
  const { theme, toggle: toggleTheme } = useTheme()
  const { fontSize, increase: increaseFontSize, decrease: decreaseFontSize } = useFontSize()
  const [topics, setTopics] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [loadingTopics, setLoadingTopics] = useState(true)

  const loadTopics = useCallback(async () => {
    try {
      const res = await fetch('/api/topics')
      if (!res.ok) throw new Error('Failed to load topics')
      const data = await res.json()
      setTopics(data)

      // Auto-select today's topic, or most recent
      if (data.length > 0 && !selectedId) {
        const today = new Date().toISOString().split('T')[0]
        const todayTopic = data.find((t) => t.date === today)
        setSelectedId(todayTopic ? todayTopic.id : data[0].id)
      }
    } catch (err) {
      console.error('Failed to load topics:', err)
    } finally {
      setLoadingTopics(false)
    }
  }, [selectedId])

  useEffect(() => {
    loadTopics()

    // Check URL param for deep link
    const params = new URLSearchParams(window.location.search)
    const topicParam = params.get('topic')
    if (topicParam) setSelectedId(parseInt(topicParam, 10))
  }, [])

  // Poll for new topics every 5 minutes
  useEffect(() => {
    const interval = setInterval(loadTopics, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [loadTopics])

  const handleSelect = (id) => {
    setSelectedId(id)
    // Update URL for shareable links
    const url = new URL(window.location)
    url.searchParams.set('topic', id)
    window.history.pushState({}, '', url)
  }

  return (
    <div className="app-layout">
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        sidebarOpen={sidebarOpen}
        fontSize={fontSize}
        onIncreaseFontSize={increaseFontSize}
        onDecreaseFontSize={decreaseFontSize}
      />

      <div className="app-body">
        <Sidebar
          topics={topics}
          selectedId={selectedId}
          onSelect={handleSelect}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        <main className="main-content">
          {loadingTopics ? (
            <div className="empty-state">
              <div className="loading-spinner" />
            </div>
          ) : (
            <TopicDetail topicId={selectedId} />
          )}
        </main>
      </div>
    </div>
  )
}

export default function App() {
  if (window.location.pathname === '/admin') return <AdminPanel />
  return <MainApp />
}
