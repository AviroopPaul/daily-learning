const APP_URL = 'https://daily-learning-taxnvq53va-uc.a.run.app'

// ── Helpers ──────────────────────────────────────────────────────────────

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

async function isQuizDoneToday() {
  const key = todayStr() + '_quiz_done'
  return new Promise((resolve) => {
    chrome.storage.local.get(key, (result) => {
      resolve(result[key] === true)
    })
  })
}

async function sendQuizNudge() {
  const done = await isQuizDoneToday()
  if (done) return

  chrome.notifications.create('quiz-nudge-' + Date.now(), {
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: 'Daily Learning',
    message: "Complete today's quiz to unlock YouTube!",
    priority: 1,
  })
}

// ── Install / startup ─────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  // Set up three daily nudge alarms: 9AM, 12PM, 6PM
  // Chrome alarms fire relative to wall clock; we schedule them by hour
  scheduleAlarms()
})

chrome.runtime.onStartup.addListener(() => {
  scheduleAlarms()
})

function scheduleAlarms() {
  chrome.alarms.clearAll(() => {
    const now = new Date()

    // Helper: get next occurrence of a given hour today or tomorrow
    function nextOccurrence(hour) {
      const d = new Date()
      d.setHours(hour, 0, 0, 0)
      if (d <= now) d.setDate(d.getDate() + 1)
      return d.getTime()
    }

    chrome.alarms.create('nudge-morning', {
      when: nextOccurrence(9),
      periodInMinutes: 1440,
    })
    chrome.alarms.create('nudge-noon', {
      when: nextOccurrence(12),
      periodInMinutes: 1440,
    })
    chrome.alarms.create('nudge-evening', {
      when: nextOccurrence(18),
      periodInMinutes: 1440,
    })
  })
}

// ── Alarm handler ─────────────────────────────────────────────────────────

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name.startsWith('nudge-')) {
    sendQuizNudge()
  }
})

// ── Notification click ────────────────────────────────────────────────────

chrome.notifications.onClicked.addListener(() => {
  chrome.tabs.create({ url: APP_URL })
})

// ── Messages from content scripts ─────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'QUIZ_COMPLETED' && msg.date) {
    const key = msg.date + '_quiz_done'
    chrome.storage.local.set({ [key]: true })

    // Update streak count in storage
    chrome.storage.local.get('streak_count', (result) => {
      const prev = result.streak_count || 0
      chrome.storage.local.set({ streak_count: prev + 1 })
    })
  }
})
