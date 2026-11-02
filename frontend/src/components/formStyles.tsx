import type { ReactNode } from 'react'

export const labelClass = 'font-label-lg text-label-lg font-semibold text-on-surface'
// Form alanları: beyaz zemin, ince koyu çerçeve; odakta çerçeve primary olur ve ring çıkar.
export const controlClass =
  'rounded-lg border border-on-surface/80 bg-surface-container-lowest text-on-surface font-body-md text-body-md placeholder:text-on-surface-variant focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/40'

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
