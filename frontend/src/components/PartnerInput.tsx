import { useState } from 'react'
import { normalizeKey } from '../lib/format'
import { controlClass } from './formStyles'
import Icon from './Icon'

interface Props {
  value: string[]
  onChange: (value: string[]) => void
  disabled?: boolean
  error?: string
}

export default function PartnerInput({ value, onChange, disabled, error }: Props) {
  const [draft, setDraft] = useState('')
  const [warning, setWarning] = useState('')

  const add = () => {
    const name = draft.trim()
    if (!name) return
    if (value.some((existing) => normalizeKey(existing) === normalizeKey(name))) {
      setWarning('Bu ortak zaten eklendi.')
      return
    }
    onChange([...value, name])
    setDraft('')
    setWarning('')
  }

  return (
    <div className="flex flex-col gap-space-xs">
      <div className="flex gap-space-sm">
        <input
          id="formPartners"
          type="text"
          value={draft}
          maxLength={200}
          disabled={disabled}
          onChange={(event) => {
            setDraft(event.target.value)
            setWarning('')
          }}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault() // formu göndermesin
              add()
            }
          }}
          placeholder="Ortak kurum adı (örn. Ankara Üni.)"
          className={`h-10 min-w-0 flex-1 px-space-sm ${controlClass}`}
        />
        <button
          type="button"
          onClick={add}
          disabled={disabled || !draft.trim()}
          className="flex h-10 items-center gap-space-xs rounded-xl bg-surface px-space-md font-label-lg text-label-lg font-semibold text-primary shadow-raised-sm transition-colors hover:text-primary-container disabled:opacity-50"
        >
          <Icon name="add" className="text-[18px]" />
          Ekle
        </button>
      </div>
      {(warning || error) && <span className="font-label-sm text-label-sm text-error">{warning || error}</span>}
      {value.length > 0 && (
        <ul className="flex flex-wrap gap-space-xs">
          {value.map((name, index) => (
            <li
              key={`${name}-${index}`}
              className="flex items-center gap-space-xs rounded-lg bg-surface py-1 pl-space-sm pr-1 font-label-md text-label-md font-medium text-primary shadow-inset-sm"
            >
              {name}
              <button
                type="button"
                aria-label={`${name} ortağını çıkar`}
                disabled={disabled}
                onClick={() => onChange(value.filter((_, i) => i !== index))}
                className="flex h-5 w-5 items-center justify-center rounded-full hover:text-error"
              >
                <Icon name="close" className="text-[14px]" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
