import { useState, useEffect } from 'react'
import { FiSun, FiMoon, FiBell, FiBellOff, FiSidebar } from 'react-icons/fi'
import { usePush } from '../hooks/usePush.js'
import StreakWidget from './StreakWidget.jsx'

const LOGO_TEXT = 'daily_learning'

function TypewriterLogo() {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    let i = 0
    const tick = setInterval(() => {
      i++
      setDisplayed(LOGO_TEXT.slice(0, i))
      if (i >= LOGO_TEXT.length) {
        clearInterval(tick)
        setDone(true)
      }
    }, 65)
    return () => clearInterval(tick)
  }, [])

  return (
    <div className="header-logo">
      {displayed}
      <span className={`logo-cursor ${done ? 'logo-cursor--blink' : ''}`}>▊</span>
    </div>
  )
}

export default function Header({ theme, onToggleTheme, onToggleSidebar, sidebarOpen, fontSize, onIncreaseFontSize, onDecreaseFontSize }) {
  const { status, loading, subscribe, unsubscribe } = usePush()

  const handleBell = () => {
    if (status === 'subscribed') unsubscribe()
    else if (status !== 'unsupported' && status !== 'denied') subscribe()
  }

  return (
    <header className="app-header">
      <button
        className="icon-btn sidebar-toggle"
        onClick={onToggleSidebar}
        aria-label="Toggle sidebar"
        title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        <FiSidebar size={16} />
      </button>

      <TypewriterLogo />

      <div className="header-spacer" />

      <div className="header-actions">
        <StreakWidget />

        <div className="font-size-controls">
          <button
            className="icon-btn font-size-btn"
            onClick={onDecreaseFontSize}
            disabled={fontSize === 'sm'}
            title="Decrease font size"
            aria-label="Decrease font size"
          >
            <span className="font-size-a font-size-a--sm">A</span>
          </button>
          <button
            className="icon-btn font-size-btn"
            onClick={onIncreaseFontSize}
            disabled={fontSize === 'xl'}
            title="Increase font size"
            aria-label="Increase font size"
          >
            <span className="font-size-a font-size-a--lg">A</span>
          </button>
        </div>

        {status !== 'unsupported' && (
          <button
            className={`icon-btn ${status === 'subscribed' ? 'active' : ''}`}
            onClick={handleBell}
            disabled={loading}
            title={
              status === 'subscribed' ? 'Disable notifications'
              : status === 'denied' ? 'Notifications blocked'
              : 'Enable notifications'
            }
          >
            {status === 'subscribed' ? <FiBell size={15} /> : <FiBellOff size={15} />}
          </button>
        )}

        <button
          className="icon-btn"
          onClick={onToggleTheme}
          title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
        >
          {theme === 'dark' ? <FiSun size={15} /> : <FiMoon size={15} />}
        </button>
      </div>
    </header>
  )
}
