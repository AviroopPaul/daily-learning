const APP_URL = 'https://daily-learning-taxnvq53va-uc.a.run.app'
const TODAY = new Date().toISOString().slice(0, 10)

document.getElementById('open-app-btn').href = APP_URL
document.getElementById('open-app-btn').addEventListener('click', (e) => {
  e.preventDefault()
  chrome.tabs.create({ url: APP_URL })
  window.close()
})

chrome.storage.local.get([TODAY + '_quiz_done', 'streak_count'], (result) => {
  const done = result[TODAY + '_quiz_done'] === true
  const streak = result['streak_count'] || 0

  const iconEl = document.getElementById('status-icon')
  const textEl = document.getElementById('status-text')
  const streakArea = document.getElementById('streak-area')
  const streakLabel = document.getElementById('streak-label')

  if (done) {
    iconEl.textContent = '✅'
    iconEl.classList.add('status-icon--done')
    textEl.textContent = "Today's quiz complete!"
    textEl.classList.add('status-text--done')
  } else {
    iconEl.textContent = '📝'
    textEl.textContent = "Quiz pending — YouTube is blocked"
  }

  if (streak > 0) {
    streakArea.style.display = 'flex'
    streakLabel.textContent = `${streak} day streak`
  }
})
