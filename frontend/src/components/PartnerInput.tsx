import { useState } from 'react'
import { normalizeKey } from '../lib/format'
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
          className="h-10 min-w-0 flex-1 rounded-lg bg-surface-container-lowest px-space-sm font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant focus:bg-surface-bright focus:outline-none"
        />
        <button
          type="button"
          onClick={add}
          disabled={disabled || !draft.trim()}
          className="flex h-10 items-center gap-space-xs rounded-lg bg-secondary-container px-space-md font-label-lg text-label-lg text-on-secondary-container transition-colors hover:bg-surface-container disabled:opacity-50"
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
              className="flex items-center gap-space-xs rounded-full bg-secondary-container py-1 pl-space-sm pr-1 font-label-md text-label-md text-on-secondary-container"
            >
              {name}
              <button
                type="button"
                aria-label={`${name} ortağını çıkar`}
                disabled={disabled}
                onClick={() => onChange(value.filter((_, i) => i !== index))}
                className="flex h-5 w-5 items-center justify-center rounded-full hover:bg-surface-container-high"
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
