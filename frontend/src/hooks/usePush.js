import { useState, useEffect, useCallback } from 'react'

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)))
}

export function usePush() {
  const [status, setStatus] = useState('idle') // idle | unsupported | denied | subscribed | unsubscribed
  const [loading, setLoading] = useState(false)

  const checkStatus = useCallback(async () => {
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
      setStatus('unsupported')
      return
    }
    if (Notification.permission === 'denied') {
      setStatus('denied')
      return
    }
    try {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      setStatus(sub ? 'subscribed' : 'unsubscribed')
    } catch {
      setStatus('unsubscribed')
    }
  }, [])

  useEffect(() => { checkStatus() }, [checkStatus])

  const subscribe = useCallback(async () => {
    setLoading(true)
    try {
      const keyRes = await fetch('/api/push/vapid-key')
      if (!keyRes.ok) throw new Error('Push not configured on server')
      const { public_key } = await keyRes.json()

      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        setStatus('denied')
        return false
      }

      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(public_key),
      })

      const keys = sub.toJSON().keys
      await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: sub.endpoint,
          p256dh: keys.p256dh,
          auth: keys.auth,
        }),
      })

      setStatus('subscribed')
      return true
    } catch (err) {
      console.error('Push subscribe error:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const unsubscribe = useCallback(async () => {
    setLoading(true)
    try {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      if (sub) {
        await fetch(`/api/push/unsubscribe?endpoint=${encodeURIComponent(sub.endpoint)}`, { method: 'DELETE' })
        await sub.unsubscribe()
      }
      setStatus('unsubscribed')
      return true
    } catch (err) {
      console.error('Push unsubscribe error:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  return { status, loading, subscribe, unsubscribe }
}
