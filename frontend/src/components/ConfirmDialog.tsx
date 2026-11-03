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
  const confirmClass = tone === 'danger' ? 'bg-error text-on-error' : 'bg-primary text-on-primary'
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-inverse-surface/50 p-space-md" onClick={onCancel}>
      <div
        role="dialog"
        aria-modal="true"
        className="w-full max-w-md rounded-xl bg-surface-container-high p-space-lg shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        {title && <h3 className="font-headline-sm text-title-md font-bold tracking-tight text-on-surface">{title}</h3>}
        <p className="mt-space-sm font-body-md text-body-md text-on-surface-variant">{message}</p>
        <div className="mt-space-lg flex justify-end gap-space-sm">
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="h-10 rounded-lg bg-surface-container px-space-md font-label-lg text-label-lg text-on-surface transition-colors hover:bg-surface-container-lowest disabled:opacity-50"
          >
            Vazgeç
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className={`h-10 rounded-lg px-space-lg font-label-lg text-label-lg shadow-md transition-all hover:opacity-95 disabled:opacity-50 ${confirmClass}`}
          >
            {busy ? 'İşleniyor...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
