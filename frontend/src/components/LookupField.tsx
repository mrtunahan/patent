import { useRef, useState } from 'react'
import { describeError } from '../lib/hooks'
import { Field, controlClass } from './formStyles'
import Icon from './Icon'
import { useToast } from './Toast'

interface Props {
  id: string
  text: string
  value: string
  options: { id: number; label: string }[]
  emptyLabel: string
  disabled: boolean
  error?: string
  addedMessage: string // "Başvuru sahibi eklendi."
  onChange: (value: string) => void
  onCreate: (name: string) => Promise<number> // kaydı oluşturur, lookup listesini yeniler, yeni id'yi döner
}

// Select + küçük "+" düğmesi: alanın altında mini satırla (iç içe çekmece yok) hızlı kayıt ekleme.
export default function LookupField({ id, text, value, options, emptyLabel, disabled, error, addedMessage, onChange, onCreate }: Props) {
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [addError, setAddError] = useState('')
  const input = useRef<HTMLInputElement>(null)

  const close = () => {
    setOpen(false)
    setName('')
    setAddError('')
  }

  const add = async () => {
    const trimmed = name.trim()
    if (!trimmed || busy) return
    setBusy(true)
    setAddError('')
    try {
      onChange(String(await onCreate(trimmed)))
      toast(addedMessage)
      close()
    } catch (err) {
      setAddError(describeError(err).message)
      input.current?.focus()
    }
    setBusy(false)
  }

  return (
    <Field id={id} text={text} error={error}>
      <div className="flex items-center gap-space-xs">
        <select id={id} value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} className={`h-10 min-w-0 flex-1 px-space-sm ${controlClass}`}>
          <option value="">{emptyLabel}</option>
          {options.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          title="Yeni ekle"
          aria-label={`${text}: yeni ekle`}
          disabled={disabled}
          onClick={() => (open ? close() : setOpen(true))}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-surface text-primary shadow-raised-sm transition-colors hover:text-primary-container disabled:opacity-50"
        >
          <Icon name="add" className="text-[20px]" />
        </button>
      </div>
      {open && (
        <div className="flex flex-col gap-space-xs">
          <div className="flex items-center gap-space-xs">
            <input
              ref={input}
              autoFocus
              type="text"
              value={name}
              maxLength={200}
              disabled={busy}
              placeholder="Yeni kayıt adı"
              aria-label={`${text}: yeni kayıt adı`}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault() // formu göndermesin
                  void add()
                } else if (e.key === 'Escape') {
                  e.stopPropagation() // çekmeceyi değil, yalnızca mini satırı kapatır
                  close()
                }
              }}
              className={`h-9 min-w-0 flex-1 px-space-sm ${controlClass}`}
            />
            <button type="button" disabled={busy || !name.trim()} onClick={() => void add()} className="h-9 rounded-xl bg-surface px-space-md font-label-md text-label-md font-semibold text-primary shadow-raised-sm disabled:opacity-50">
              {busy ? 'Ekleniyor...' : 'Ekle'}
            </button>
            <button type="button" disabled={busy} onClick={close} className="h-9 rounded-xl bg-surface px-space-md font-label-md text-label-md text-on-surface-variant shadow-raised-sm hover:text-on-surface disabled:opacity-50">
              İptal
            </button>
          </div>
          {addError && <span role="alert" className="font-label-sm text-label-sm text-error">{addError}</span>}
        </div>
      )}
    </Field>
  )
}
