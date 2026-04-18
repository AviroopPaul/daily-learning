// Runs at document_start on youtube.com — blocks page if quiz not done today

const APP_URL = 'https://daily-learning-taxnvq53va-uc.a.run.app'
const TODAY = new Date().toISOString().slice(0, 10)
const STORAGE_KEY = TODAY + '_quiz_done'

// Inline styles — no external CSS dependency
const OVERLAY_STYLES = `
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 2147483647;
  background: #0f0f0f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
`

const CARD_STYLES = `
  background: #1a1a1a;
  border: 1px solid #2e2e2e;
  border-radius: 12px;
  padding: 40px 48px;
  max-width: 440px;
  text-align: center;
`

const TITLE_STYLES = `
  font-size: 20px;
  font-weight: 700;
  color: #e8e8e8;
  margin-bottom: 12px;
  line-height: 1.3;
`

const DESC_STYLES = `
  font-size: 14px;
  color: #888;
  margin-bottom: 28px;
  line-height: 1.6;
`

const BTN_STYLES = `
  display: inline-block;
  padding: 10px 24px;
  background: #4a90d9;
  color: #fff;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s;
`

const LOGO_STYLES = `
  font-size: 11px;
  color: #555;
  margin-top: 20px;
  font-family: monospace;
`

function injectOverlay() {
  const overlay = document.createElement('div')
  overlay.id = 'dlq-overlay'
  overlay.setAttribute('style', OVERLAY_STYLES)

  overlay.innerHTML = `
    <div style="${CARD_STYLES}">
      <div style="font-size: 36px; margin-bottom: 16px;">📚</div>
      <div style="${TITLE_STYLES}">Complete Today's Quiz First</div>
      <div style="${DESC_STYLES}">
        You've blocked YouTube until you learn something new.<br>
        Take the daily system design quiz to unlock it.
      </div>
      <a href="${APP_URL}" style="${BTN_STYLES}" id="dlq-go-btn">Take the Quiz →</a>
      <div style="${LOGO_STYLES}">daily_learning</div>
    </div>
  `

  // Block underlying page
  const blockBody = () => {
    if (document.body) {
      document.body.style.cssText = 'display:none!important'
    }
  }

  document.documentElement.appendChild(overlay)
  blockBody()
  document.addEventListener('DOMContentLoaded', blockBody)
}

function removeOverlay() {
  const overlay = document.getElementById('dlq-overlay')
  if (overlay) overlay.remove()
  if (document.body) document.body.style.cssText = ''
}

// Check storage and block/unblock
chrome.storage.local.get(STORAGE_KEY, (result) => {
  const done = result[STORAGE_KEY] === true
  if (!done) {
    injectOverlay()
  }
})

// Listen for quiz completion in another tab (storage change)
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes[STORAGE_KEY]?.newValue === true) {
    removeOverlay()
  }
})
