import { useState, useEffect, useRef } from 'react'
import { FiCalendar, FiAward, FiPlay, FiPause, FiSquare, FiVolume2, FiLoader } from 'react-icons/fi'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { usePush } from '../hooks/usePush.js'
import QuizPanel from './QuizPanel.jsx'

function Markdown({ children, className }) {
  if (!children) return null
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node, ...props }) => <a target="_blank" rel="noopener noreferrer" {...props} />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}

const MODEL_NAME = 'gpt-oss-120b'

function formatDateLong(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

function DifficultyBadge({ difficulty }) {
  const cls = {
    Beginner: 'badge-beginner',
    Intermediate: 'badge-intermediate',
    Advanced: 'badge-advanced',
  }[difficulty] || 'badge-intermediate'
  return <span className={`badge ${cls}`}>{difficulty}</span>
}

function Section({ label, children }) {
  return (
    <div className="section">
      <div className="section-label">{label}</div>
      {children}
    </div>
  )
}

function SkeletonDetail() {
  return (
    <div className="topic-detail">
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <div className="skeleton" style={{ width: 80, height: 22, borderRadius: 20 }} />
        <div className="skeleton" style={{ width: 70, height: 22, borderRadius: 20 }} />
        <div className="skeleton" style={{ width: 120, height: 22, borderRadius: 4 }} />
      </div>
      <div className="skeleton" style={{ height: 36, width: '80%', marginBottom: 8 }} />
      <div className="skeleton" style={{ height: 36, width: '60%', marginBottom: 28 }} />
      {[100, 90, 80, 95, 70].map((w, i) => (
        <div key={i} className="skeleton" style={{ height: 16, width: `${w}%`, marginBottom: 10, maxWidth: `${w}%` }} />
      ))}
    </div>
  )
}

function NotifyBanner() {
  const { status, loading, subscribe } = usePush()
  const [dismissed, setDismissed] = useState(() => localStorage.getItem('notifyDismissed') === '1')

  if (dismissed || status === 'subscribed' || status === 'unsupported' || status === 'denied') return null

  return (
    <div className="notify-banner">
      <div className="notify-banner-text">
        <strong>Get notified at 9PM IST</strong> when a new topic drops.
      </div>
      <button className="btn btn-primary" onClick={subscribe} disabled={loading}>
        {loading ? 'Enabling…' : 'Enable'}
      </button>
      <button
        className="btn btn-ghost"
        onClick={() => { localStorage.setItem('notifyDismissed', '1'); setDismissed(true) }}
      >
        Later
      </button>
    </div>
  )
}

function buildTopicText(topic) {
  if (topic.tldr) return topic.tldr
  // Fallback if no TLDR: read full content
  const parts = [
    topic.title,
    topic.problem_statement && `The Problem: ${topic.problem_statement}`,
    topic.context_text && `Context: ${topic.context_text}`,
    topic.deep_dive && `Deep Dive: ${topic.deep_dive}`,
    topic.real_world_examples && `Real-World Examples: ${topic.real_world_examples}`,
    topic.solution_approaches && `Solution Approaches: ${topic.solution_approaches}`,
    topic.key_takeaways?.length && `Key Takeaways: ${topic.key_takeaways.join('. ')}`,
  ]
  return parts.filter(Boolean).join('\n\n')
}

function formatTime(s) {
  if (!s || isNaN(s) || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

function AudioPlayer({ topic }) {
  const [state, setState] = useState('idle') // idle | loading | playing | paused
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const audioRef = useRef(null)
  const blobUrlRef = useRef(null)

  useEffect(() => {
    return () => stopAudio()
  }, [topic?.id])

  function stopAudio() {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current = null
    }
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current)
      blobUrlRef.current = null
    }
    setState('idle')
    setCurrentTime(0)
    setDuration(0)
  }

  async function play() {
    if (state === 'paused' && audioRef.current) {
      audioRef.current.play()
      setState('playing')
      return
    }

    setState('loading')
    try {
      const resp = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: buildTopicText(topic) }),
      })
      if (!resp.ok) throw new Error('TTS request failed')

      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      blobUrlRef.current = url

      const audio = new Audio(url)
      audioRef.current = audio
      audio.onloadedmetadata = () => setDuration(audio.duration)
      audio.ontimeupdate = () => setCurrentTime(audio.currentTime)
      audio.onended = () => { setState('idle'); setCurrentTime(0) }
      audio.onerror = () => setState('idle')
      audio.play()
      setState('playing')
    } catch (err) {
      console.error('TTS error:', err)
      setState('idle')
    }
  }

  function pause() {
    if (audioRef.current) {
      audioRef.current.pause()
      setState('paused')
    }
  }

  function seek(e) {
    const time = parseFloat(e.target.value)
    setCurrentTime(time)
    if (audioRef.current) audioRef.current.currentTime = time
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  if (state === 'idle') {
    return (
      <div className="audio-player">
        <button className="audio-btn-listen" onClick={play}>
          <FiVolume2 size={13} /> Listen
        </button>
      </div>
    )
  }

  return (
    <div className="audio-player audio-player--active">
      <button
        className="audio-ctrl-btn"
        onClick={state === 'playing' ? pause : play}
        disabled={state === 'loading'}
        title={state === 'playing' ? 'Pause' : 'Play'}
      >
        {state === 'loading'
          ? <FiLoader size={14} className="audio-spin" />
          : state === 'playing'
          ? <FiPause size={14} />
          : <FiPlay size={14} />}
      </button>

      <div className="audio-seek-wrap">
        <input
          type="range"
          className="audio-seek"
          min={0}
          max={duration || 100}
          step={0.1}
          value={currentTime}
          onChange={seek}
          disabled={state === 'loading'}
          style={{ '--progress': `${progress}%` }}
        />
      </div>

      <span className="audio-time">
        {formatTime(currentTime)}<span className="audio-time-sep">/</span>{formatTime(duration)}
      </span>

      <button className="audio-ctrl-btn audio-stop-btn" onClick={stopAudio} title="Stop">
        <FiSquare size={11} />
      </button>
    </div>
  )
}

export default function TopicDetail({ topicId }) {
  const [topic, setTopic] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showQuiz, setShowQuiz] = useState(false)

  useEffect(() => {
    if (!topicId) { setTopic(null); return }
    setLoading(true)
    setError(null)
    fetch(`/api/topics/${topicId}`)
      .then((r) => { if (!r.ok) throw new Error('Topic not found'); return r.json() })
      .then(setTopic)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [topicId])

  if (!topicId) {
    return (
      <div className="empty-state">
        <h2>Daily Learning</h2>
        <p>Select a topic from the sidebar, or wait for today's topic at 9PM IST.</p>
      </div>
    )
  }

  if (loading) return <SkeletonDetail />

  if (error) {
    return (
      <div className="empty-state">
        <h2>Couldn't load topic</h2>
        <p>{error}</p>
      </div>
    )
  }

  if (!topic) return null

  const quizDone = localStorage.getItem(`${topic.date}_quiz_done`) === '1'

  return (
    <div className="topic-detail-wrapper">
      <div className="topic-detail">
        <NotifyBanner />

      <div className="topic-meta">
        <span className="topic-date">
          <FiCalendar size={13} />
          {formatDateLong(topic.date)}
        </span>
        <span className="badge badge-domain">{topic.domain}</span>
        <DifficultyBadge difficulty={topic.difficulty} />
        <button
          className={`btn btn-quiz ${quizDone ? 'btn-quiz--done' : ''}`}
          onClick={() => setShowQuiz(prev => !prev)}
        >
          <FiAward size={13} />
          {quizDone ? 'Quiz Done' : 'Quiz'}
        </button>
      </div>

      <h1 className="topic-title">{topic.title}</h1>

      <AudioPlayer topic={topic} />

      {topic.tldr && (
        <div className="tldr-box">
          <div className="tldr-label">TL;DR</div>
          <Markdown className="tldr-text markdown">{topic.tldr}</Markdown>
        </div>
      )}

      <Section label="The Problem">
        <div className="problem-box">
          <Markdown className="markdown">{topic.problem_statement}</Markdown>
        </div>
      </Section>

      <Section label="Context">
        <Markdown className="prose markdown">{topic.context_text}</Markdown>
      </Section>

      <Section label="Deep Dive">
        <Markdown className="prose markdown">{topic.deep_dive}</Markdown>
      </Section>

      <Section label="Real-World Examples">
        <Markdown className="prose markdown">{topic.real_world_examples}</Markdown>
      </Section>

      <Section label="Solution Approaches">
        <Markdown className="prose markdown">{topic.solution_approaches}</Markdown>
      </Section>

      <Section label="Key Takeaways">
        <ul className="takeaways-list">
          {(topic.key_takeaways || []).map((t, i) => (
            <li key={i}><Markdown className="markdown markdown--inline">{t}</Markdown></li>
          ))}
        </ul>
      </Section>

      {topic.further_reading?.length > 0 && (
        <Section label="Further Reading">
          <ul className="reading-list">
            {topic.further_reading.map((t, i) => (
              <li key={i}><Markdown className="markdown markdown--inline">{t}</Markdown></li>
            ))}
          </ul>
        </Section>
      )}

      <div className="content-footer">
        Generated by {MODEL_NAME}
      </div>
    </div>

      {showQuiz && (
        <QuizPanel
          topicId={topic.id}
          topicDate={topic.date}
          onClose={() => setShowQuiz(false)}
        />
      )}
    </div>
  )
}
