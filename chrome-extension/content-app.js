// Runs on the daily_learning app domain — bridges postMessage to chrome.runtime

window.addEventListener('message', (event) => {
  // Only accept messages from same origin
  if (event.origin !== window.location.origin) return
  if (!event.data || event.data.type !== 'QUIZ_COMPLETED') return

  chrome.runtime.sendMessage({
    type: 'QUIZ_COMPLETED',
    date: event.data.date,
  })
})
