import { useState, useEffect } from 'react'
import { FiX, FiCheck, FiXCircle, FiZap, FiArrowRight } from 'react-icons/fi'
import { getDeviceId } from '../utils/deviceId.js'

function ScoreBadge({ score, total }) {
  const pct = score / total
  const cls = pct >= 0.8 ? 'score-badge--great' : pct >= 0.6 ? 'score-badge--ok' : 'score-badge--low'
  return (
    <div className={`score-badge ${cls}`}>
      {score} / {total}
    </div>
  )
}

const optionLabels = { a: 'A', b: 'B', c: 'C', d: 'D' }
const optionKeys = ['a', 'b', 'c', 'd']

export default function QuizPanel({ topicId, topicDate, onClose }) {
  const [phase, setPhase] = useState('loading') // loading | questions | submitted | error | no-quiz | generating
  const [questions, setQuestions] = useState([])
  const [quizId, setQuizId] = useState(null)
  const [current, setCurrent] = useState(0)      // index of visible question
  const [answers, setAnswers] = useState({})      // { "1": "a", ... }
  const [results, setResults] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const deviceId = getDeviceId()
  const storageKey = `quiz_result_${topicDate}`

  useEffect(() => {
    const cached = sessionStorage.getItem(storageKey)
    if (cached) {
      try {
        setResults(JSON.parse(cached))
        setPhase('submitted')
        return
      } catch { /* fall through */ }
    }

    fetch(`/api/quiz/${topicId}`)
      .then(r => {
        if (r.status === 404) { setPhase('no-quiz'); return null }
        if (!r.ok) throw new Error('Failed to load quiz')
        return r.json()
      })
      .then(data => {
        if (!data) return
        setQuizId(data.quiz_id)
        setQuestions(data.questions)
        setCurrent(0)
        setPhase('questions')
      })
      .catch(() => setPhase('error'))
  }, [topicId])

  const handleGenerate = async () => {
    setPhase('generating')
    try {
      const r = await fetch(`/api/quiz/${topicId}/generate`, { method: 'POST' })
      if (!r.ok) throw new Error('Generation failed')
      const data = await r.json()
      setQuizId(data.quiz_id)
      setQuestions(data.questions)
      setCurrent(0)
      setPhase('questions')
    } catch {
      setPhase('error')
    }
  }

  const handleSubmit = async () => {
    if (submitting) return
    setSubmitting(true)
    try {
      const r = await fetch(`/api/quiz/${quizId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_id: deviceId, answers }),
      })
      if (r.status === 409) { setPhase('error'); return }
      if (!r.ok) throw new Error('Submit failed')
      const data = await r.json()
      sessionStorage.setItem(storageKey, JSON.stringify(data))
      localStorage.setItem(`${topicDate}_quiz_done`, '1')
      window.postMessage({ type: 'QUIZ_COMPLETED', date: topicDate }, '*')
      setResults(data)
      setPhase('submitted')
    } catch {
      setPhase('error')
    } finally {
      setSubmitting(false)
    }
  }

  const q = questions[current]
  const isLast = current === questions.length - 1
  const currentAnswered = q ? !!answers[String(q.order)] : false

  return (
    <div className="quiz-panel">
      <div className="quiz-panel-header">
        <div className="quiz-panel-header-left">
          <span className="quiz-panel-title">Quiz</span>
          {phase === 'questions' && (
            <span className="quiz-panel-progress">{current + 1} / {questions.length}</span>
          )}
        </div>
        <button className="icon-btn" onClick={onClose} aria-label="Close quiz">
          <FiX size={16} />
        </button>
      </div>

      <div className="quiz-panel-body">

        {phase === 'loading' && (
          <div className="quiz-loading">
            {[1, 2, 3].map(i => (
              <div key={i} className="skeleton" style={{ height: 60, marginBottom: 12, borderRadius: 8 }} />
            ))}
          </div>
        )}

        {phase === 'no-quiz' && (
          <div className="quiz-empty">
            <div className="quiz-no-quiz-icon"><FiZap size={28} /></div>
            <p className="quiz-empty-title">No quiz yet for this topic</p>
            <p className="quiz-empty-sub">
              Quizzes are generated automatically for new topics. For older topics you can generate one on demand — it takes about 10 seconds.
            </p>
            <button className="btn btn-primary quiz-generate-btn" onClick={handleGenerate}>
              Generate Quiz
            </button>
          </div>
        )}

        {phase === 'generating' && (
          <div className="quiz-generating">
            <div className="quiz-generating-spinner" />
            <p className="quiz-generating-text">Generating your quiz…</p>
            <p className="quiz-empty-sub">This takes about 10 seconds.</p>
          </div>
        )}

        {phase === 'error' && (
          <div className="quiz-empty">
            <p>Failed to load quiz. Please try again.</p>
          </div>
        )}

        {phase === 'questions' && q && (
          <div className="quiz-step">
            {/* Progress bar */}
            <div className="quiz-progress-bar">
              <div
                className="quiz-progress-fill"
                style={{ width: `${((current + 1) / questions.length) * 100}%` }}
              />
            </div>

            <div className="quiz-question">
              <div className="quiz-question-text">{q.question}</div>
              <div className="quiz-options">
                {optionKeys.map(opt => {
                  const text = q[`option_${opt}`]
                  const selected = answers[String(q.order)] === opt
                  return (
                    <label key={opt} className={`quiz-option ${selected ? 'quiz-option--selected' : ''}`}>
                      <input
                        type="radio"
                        name={`q_${q.order}`}
                        value={opt}
                        checked={selected}
                        onChange={() => setAnswers(prev => ({ ...prev, [String(q.order)]: opt }))}
                      />
                      <span className="quiz-option-label">{optionLabels[opt]}</span>
                      <span className="quiz-option-text">{text}</span>
                    </label>
                  )
                })}
              </div>
            </div>

            <div className="quiz-nav">
              {current > 0 && (
                <button
                  className="btn btn-ghost quiz-nav-btn"
                  onClick={() => setCurrent(c => c - 1)}
                >
                  Back
                </button>
              )}
              <div style={{ flex: 1 }} />
              {!isLast ? (
                <button
                  className="btn btn-primary quiz-nav-btn"
                  onClick={() => setCurrent(c => c + 1)}
                  disabled={!currentAnswered}
                >
                  Next <FiArrowRight size={13} />
                </button>
              ) : (
                <button
                  className="btn btn-primary quiz-nav-btn"
                  onClick={handleSubmit}
                  disabled={!currentAnswered || submitting}
                >
                  {submitting ? 'Submitting…' : 'Submit'}
                </button>
              )}
            </div>
          </div>
        )}

        {phase === 'submitted' && results && (
          <>
            <div className="quiz-score-row">
              <ScoreBadge score={results.score} total={results.total} />
              <span className="quiz-score-label">
                {results.score === results.total ? 'Perfect score!' :
                 results.score >= results.total * 0.8 ? 'Great job!' :
                 results.score >= results.total * 0.6 ? 'Good effort!' : 'Keep learning!'}
              </span>
            </div>
            {results.results.map((r, idx) => (
              <div key={idx} className={`quiz-result-item ${r.is_correct ? 'quiz-result--correct' : 'quiz-result--wrong'}`}>
                <div className="quiz-result-header">
                  <span className="quiz-result-icon">
                    {r.is_correct ? <FiCheck size={14} /> : <FiXCircle size={14} />}
                  </span>
                  <span className="quiz-question-num">{r.order}.</span>
                  <span className="quiz-result-q">{r.question}</span>
                </div>
                {!r.is_correct && (
                  <div className="quiz-result-your">
                    Your answer: <strong>{r.your_answer.toUpperCase()}</strong>
                  </div>
                )}
                <div className="quiz-result-correct">
                  Correct: <strong>{r.correct.toUpperCase()}</strong> — {r.correct_text}
                </div>
                <div className="quiz-result-explanation">{r.explanation}</div>
              </div>
            ))}
          </>
        )}

      </div>
    </div>
  )
}
