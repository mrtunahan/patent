import type { ReactNode } from 'react'

export const labelClass = 'font-label-lg text-label-lg font-semibold text-on-surface'
// Form alanları (TTO Otomasyonu): çerçevesiz, zemine gömük (inset) yüzey; odakta indigo halka çıkar.
export const controlClass =
  'rounded-xl bg-surface shadow-inset text-on-surface font-body-md text-body-md placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-60'

export function Field({ id, text, error, children }: { id: string; text: string; error?: string; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-space-xs">
      <label htmlFor={id} className={labelClass}>
        {text}
      </label>
      {children}
      {error && <span className="font-label-sm text-label-sm text-error">{error}</span>}
    </div>
  )
}
