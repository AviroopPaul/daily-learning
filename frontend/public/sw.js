// Service Worker for SysDesign Daily push notifications

self.addEventListener('install', (event) => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('push', (event) => {
  if (!event.data) return

  let data = {}
  try {
    data = event.data.json()
  } catch {
    data = { title: 'SysDesign Daily', body: event.data.text() }
  }

  const title = data.title || '📐 SysDesign Daily'
  const options = {
    body: data.body || 'New topic available',
    icon: data.icon || '/favicon.svg',
    badge: '/favicon.svg',
    data: { url: data.url || '/' },
    vibrate: [100, 50, 100],
    requireInteraction: false,
    tag: 'sysdesign-daily',
    renotify: true,
  }

  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = event.notification.data?.url || '/'

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url)
          return client.focus()
        }
      }
      return self.clients.openWindow(url)
    })
  )
})
