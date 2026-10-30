import type { ReactNode } from 'react'

export const labelClass = 'font-label-lg text-label-lg font-semibold text-on-surface'
export const controlClass =
  'rounded-lg bg-surface-container-lowest text-on-surface font-body-md text-body-md placeholder:text-on-surface-variant focus:bg-surface-bright focus:outline-none'

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
