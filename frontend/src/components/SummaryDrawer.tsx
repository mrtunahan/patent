import { useCallback, useEffect, useState } from 'react'
import type { PatentRef } from '../api/types'
import Icon from './Icon'

interface Props {
  title: string
  patents: PatentRef[]
  onClose: () => void
  onOpenPatent: (id: number) => void
}

// Sağdan açılan salt okunur özet paneli (DrawerShell stili): kayda bağlı patent başlıkları.
export default function SummaryDrawer({ title, patents, onClose, onOpenPatent }: Props) {
  const [visible, setVisible] = useState(false)

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
      if (event.key === 'Escape') close()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [close])

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
          <div className="flex min-w-0 items-center gap-space-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-on-primary">
              <Icon name="folder_special" className="text-[22px]" />
            </div>
            <div className="flex min-w-0 flex-col">
              <h2 className="truncate font-headline-sm text-headline-sm text-on-surface">{title}</h2>
              <span className="font-label-sm text-label-sm text-on-surface-variant">{patents.length} patent</span>
            </div>
          </div>
          <button type="button" onClick={close} aria-label="Kapat" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container">
            <Icon name="close" className="text-[24px]" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-space-lg">
          {patents.length === 0 ? (
            <p className="text-on-surface-variant">Bu kayda bağlı patent yok.</p>
          ) : (
            <ul className="flex flex-col gap-space-xs">
              {patents.map((patent) => (
                <li key={patent.id}>
                  <button
                    type="button"
                    onClick={() => onOpenPatent(patent.id)}
                    className="w-full rounded-lg bg-surface-container-lowest px-space-md py-space-sm text-left font-body-md text-body-md text-primary transition-colors hover:bg-surface-bright hover:underline"
                  >
                    {patent.title}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex items-center justify-start bg-surface-container-highest p-space-lg">
          <button type="button" onClick={close} className="h-10 rounded-lg bg-surface-container px-space-md font-label-lg text-label-lg text-on-surface transition-colors hover:bg-surface-container-lowest">
            Kapat
          </button>
        </div>
      </div>
    </>
  )
}
