import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'

let mermaidInitialized = false

function getTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'default' : 'dark'
}

function initMermaid() {
  if (mermaidInitialized) return
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: getTheme(),
    fontFamily: 'inherit',
    flowchart: { htmlLabels: true, curve: 'basis' },
  })
  mermaidInitialized = true
}

let renderCounter = 0

export default function MermaidDiagram({ code }) {
  const ref = useRef(null)
  const [error, setError] = useState(null)
  const [svg, setSvg] = useState('')

  useEffect(() => {
    if (!code) return
    let cancelled = false
    initMermaid()

    const id = `mermaid-${Date.now()}-${++renderCounter}`
    mermaid
      .render(id, code.trim())
      .then(({ svg }) => {
        if (!cancelled) {
          setSvg(svg)
          setError(null)
        }
      })
      .catch((e) => {
        if (!cancelled) {
          console.error('Mermaid render error:', e)
          setError(e?.message || String(e))
          setSvg('')
        }
      })

    return () => { cancelled = true }
  }, [code])

  // Re-render when theme changes
  useEffect(() => {
    const observer = new MutationObserver(() => {
      mermaidInitialized = false
      initMermaid()
      // Force re-render by toggling state
      setSvg((prev) => prev)
      if (code) {
        const id = `mermaid-theme-${Date.now()}-${++renderCounter}`
        mermaid.render(id, code.trim())
          .then(({ svg }) => setSvg(svg))
          .catch((e) => setError(e?.message || String(e)))
      }
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => observer.disconnect()
  }, [code])

  if (!code) return null

  if (error) {
    return (
      <div className="mermaid-error">
        <div className="mermaid-error-label">Diagram failed to render</div>
        <pre className="mermaid-source">{code}</pre>
      </div>
    )
  }

  return (
    <div className="mermaid-wrap" ref={ref} dangerouslySetInnerHTML={{ __html: svg }} />
  )
}
