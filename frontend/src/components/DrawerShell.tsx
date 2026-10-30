import { useCallback, useEffect, useState, type ReactNode } from 'react'
import ConfirmDialog from './ConfirmDialog'
import Icon from './Icon'

interface Props {
  title: string
  subtitle: string
  icon?: string
  isNew: boolean
  loading?: boolean
  saving: boolean
  error: string
  formId: string
  escDisabled?: boolean // açık bir ek onay penceresi varsa Esc çekmeceyi kapatmaz
  onClose: () => void
  onSubmit: () => void
  onDelete: () => void
  children: ReactNode
}

// Sağdan açılan çekmece kabuğu: örtü, Esc, başlık, hata kutusu, Vazgeç / Sil / Kaydet. Alanlar children ile gelir.
export default function DrawerShell({
  title, subtitle, icon = 'post_add', isNew, loading = false, saving, error, formId, escDisabled = false,
  onClose, onSubmit, onDelete, children,
}: Props) {
  const [visible, setVisible] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  useEffect(() => {
    const frame = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(frame)
  }, [])

  const close = useCallback(() => {
    setVisible(false)
    window.setTimeout(onClose, 250)
  }, [onClose])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !escDisabled && !confirmDelete) close()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [close, escDisabled, confirmDelete])

  const busy = saving || loading
  return (
    <>
      <div
        className={`fixed inset-0 z-50 bg-inverse-surface/40 backdrop-blur-[2px] transition-opacity duration-300 ${visible ? 'opacity-100' : 'opacity-0'}`}
        onClick={close}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`fixed right-0 top-0 z-50 flex h-full w-full max-w-2xl flex-col justify-between overflow-hidden bg-surface-container-high shadow-2xl transition-transform duration-300 ease-out ${
          visible ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between bg-surface-container-highest p-space-lg">
          <div className="flex items-center gap-space-sm">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-on-primary">
              <Icon name={icon} className="text-[22px]" />
            </div>
            <div className="flex flex-col">
              <h2 className="font-headline-sm text-headline-sm text-on-surface">{title}</h2>
              <span className="font-label-sm text-label-sm text-on-surface-variant">{subtitle}</span>
            </div>
          </div>
          <button type="button" onClick={close} aria-label="Kapat" className="flex h-9 w-9 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container">
            <Icon name="close" className="text-[24px]" />
          </button>
        </div>

        <form
          id={formId}
          noValidate
          onSubmit={(event) => {
            event.preventDefault()
            onSubmit()
          }}
          className="flex flex-1 flex-col gap-space-lg overflow-y-auto p-space-lg"
        >
          {error && (
            <div role="alert" className="flex items-start gap-space-sm rounded-lg bg-error-container p-space-sm font-body-md text-body-md text-on-error-container">
              <Icon name="error" className="mt-0.5 text-[20px]" />
              <span>{error}</span>
            </div>
          )}
          {loading ? <p className="text-on-surface-variant">Yükleniyor...</p> : children}
        </form>

        <div className="flex items-center justify-between gap-space-sm bg-surface-container-highest p-space-lg">
          <div className="flex items-center gap-space-sm">
            <button type="button" onClick={close} disabled={saving} className="h-10 rounded-lg bg-surface-container px-space-md font-label-lg text-label-lg text-on-surface transition-colors hover:bg-surface-container-lowest disabled:opacity-50">
              Vazgeç
            </button>
            {!isNew && (
              <button type="button" onClick={() => setConfirmDelete(true)} disabled={busy} className="flex h-10 items-center gap-space-xs rounded-lg px-space-md font-label-lg text-label-lg text-error transition-colors hover:bg-error-container disabled:opacity-50">
                <Icon name="delete" className="text-[18px]" />
                Sil
              </button>
            )}
          </div>
          <button type="submit" form={formId} disabled={busy} className="flex h-10 items-center gap-space-xs rounded-lg bg-primary px-space-lg font-label-lg text-label-lg text-on-primary shadow-md transition-all hover:bg-primary/95 disabled:opacity-60">
            <Icon name="check" className="text-[18px]" />
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
        </div>
      </div>

      <ConfirmDialog
        open={confirmDelete}
        message="Bu kayıt silinsin mi?"
        confirmLabel="Sil"
        tone="danger"
        onCancel={() => setConfirmDelete(false)}
        onConfirm={() => {
          setConfirmDelete(false)
          onDelete()
        }}
      />
    </>
  )
}
