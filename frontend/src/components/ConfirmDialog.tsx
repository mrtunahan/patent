import { useEffect } from 'react'

interface Props {
  open: boolean
  title?: string
  message: string
  confirmLabel: string
  tone?: 'primary' | 'danger'
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({ open, title, message, confirmLabel, tone = 'primary', busy, onConfirm, onCancel }: Props) {
  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onCancel])

  if (!open) return null
  const confirmClass = tone === 'danger' ? 'bg-error text-on-error' : 'bg-surface text-primary shadow-raised'
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-on-surface/20 p-space-md backdrop-blur-sm" onClick={onCancel}>
      <div
        role="dialog"
        aria-modal="true"
        className="w-full max-w-md rounded-2xl bg-surface p-6 shadow-modal"
        onClick={(event) => event.stopPropagation()}
      >
        {title && <h3 className="text-base font-semibold text-on-surface">{title}</h3>}
        <p className="mt-space-sm font-body-md text-body-md text-on-surface-variant">{message}</p>
        <div className="mt-space-lg flex justify-end gap-space-sm">
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="h-10 rounded-xl bg-surface px-space-md font-label-lg text-label-lg font-medium text-on-surface-variant shadow-raised-sm transition-colors hover:text-on-surface disabled:opacity-50"
          >
            Vazgeç
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className={`h-10 rounded-xl px-space-lg font-label-lg text-label-lg font-semibold transition-all hover:opacity-95 disabled:opacity-50 ${confirmClass}`}
          >
            {busy ? 'İşleniyor...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
