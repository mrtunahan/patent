import { useCallback, useEffect, useState } from 'react'
import { ApiError, isAbort } from '../api/client'
import { useToast } from '../components/Toast'

export type Status = 'loading' | 'error' | 'ready'

// Küçük liste yükleyici (fetcher modül düzeyinde sabit bir fonksiyon olmalı).
export function useList<T>(fetcher: (signal: AbortSignal) => Promise<T[]>) {
  const [items, setItems] = useState<T[] | null>(null)
  const [status, setStatus] = useState<Status>('loading')
  const [errorMessage, setErrorMessage] = useState('')
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setStatus('loading')
    fetcher(controller.signal)
      .then((result) => {
        setItems(result)
        setStatus('ready')
      })
      .catch((err) => {
        if (isAbort(err)) return
        setErrorMessage(err instanceof ApiError ? err.detail : 'Liste yüklenemedi.')
        setStatus('error')
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick])

  const reload = useCallback(() => setTick((n) => n + 1), [])
  return { items, status, errorMessage, reload }
}

export function describeError(err: unknown): { message: string; fieldErrors: Record<string, string>; notFound: boolean } {
  if (err instanceof ApiError) return { message: err.detail, fieldErrors: err.fieldErrors, notFound: err.status === 404 }
  return { message: 'Beklenmeyen bir hata oluştu.', fieldErrors: {}, notFound: false }
}

// Tablodaki sil ikonu: onay -> DELETE -> toast -> liste yenile (409 dahil backend mesajı toast'ta).
export function useRowDelete<T extends { id: number }>(remove: (id: number) => Promise<void>, onDone: () => void) {
  const toast = useToast()
  const [target, setTarget] = useState<T | null>(null)
  const [busy, setBusy] = useState(false)

  const confirm = async () => {
    if (!target) return
    setBusy(true)
    try {
      await remove(target.id)
      toast('Kayıt silindi.')
    } catch (err) {
      const { message, notFound } = describeError(err)
      toast(notFound ? 'Kayıt bulunamadı.' : message)
    }
    setBusy(false)
    setTarget(null)
    onDone()
  }
  return { target, setTarget, busy, confirm }
}

// İstemci tarafı arama: Türkçe büyük/küçük harf duyarsız.
export const matchesQuery = (q: string, ...texts: (string | null | undefined)[]) => {
  const needle = q.trim().toLocaleLowerCase('tr')
  return !needle || texts.some((text) => (text ?? '').toLocaleLowerCase('tr').includes(needle))
}
