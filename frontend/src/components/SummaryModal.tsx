import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { PatentRef } from '../api/types'
import { PATENT_STATUSES } from '../api/types'
import { formatDate, statusStyle, typeStyle } from '../lib/format'
import Avatar from './Avatar'
import Icon from './Icon'

interface Props {
  name: string
  kind: string // alt satır: başvuru sahibi için bölüm adı; bölüm / firma / ortak için sabit etiket (boşsa gizlenir)
  patents: PatentRef[]
  onClose: () => void
}

const chipBase = 'inline-flex items-center gap-1 rounded-full px-space-md py-1 font-label-md text-label-md font-semibold'

// Sayfa ortasında açılan salt okunur özet penceresi: kayda bağlı patentler; yalnızca "Düzenle" çekmeceye gider.
export default function SummaryModal({ name, kind, patents, onClose }: Props) {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [type, setType] = useState('') // '' = Tümü
  const [open, setOpen] = useState<Set<number>>(new Set())

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const counts = useMemo(() => {
    const byStatus = new Map<string, number>()
    const byType = new Map<string, number>()
    let unset = 0
    for (const patent of patents) {
      if (patent.status) byStatus.set(patent.status, (byStatus.get(patent.status) ?? 0) + 1)
      else unset += 1
      byType.set(patent.fsmh_type_name, (byType.get(patent.fsmh_type_name) ?? 0) + 1)
    }
    return { byStatus, unset, types: [...byType.entries()].sort((a, b) => a[0].localeCompare(b[0], 'tr')) }
  }, [patents])

  const needle = q.trim().toLocaleLowerCase('tr')
  const visible = patents.filter((p) => (!type || p.fsmh_type_name === type) && (!needle || p.title.toLocaleLowerCase('tr').includes(needle)))
  const toggle = (id: number) =>
    setOpen((prev) => {
      const next = new Set(prev)
      if (!next.delete(id)) next.add(id)
      return next
    })
  const go = (path: string) => {
    onClose()
    navigate(path)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-space-md">
      <div className="absolute inset-0 bg-on-surface/20 backdrop-blur-sm" onClick={onClose} />
      <div role="dialog" aria-modal="true" aria-label={name} className="relative flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-surface shadow-modal">
        <div className="flex flex-col gap-space-md bg-surface p-6 shadow-header">
          <div className="flex items-start justify-between gap-space-md">
            <div className="flex min-w-0 items-center gap-space-md">
              <Avatar name={name} size="lg" />
              <div className="flex min-w-0 flex-col">
                <h2 className="break-words text-lg font-semibold text-on-surface">{name}</h2>
                {kind && <span className="font-label-md text-label-md text-on-surface-variant">{kind}</span>}
              </div>
            </div>
            <button type="button" onClick={onClose} aria-label="Kapat" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-surface text-on-surface-variant shadow-raised-sm transition-colors hover:text-on-surface">
              <Icon name="close" className="text-[20px]" />
            </button>
          </div>
          <div className="flex flex-wrap gap-space-xs">
            <span className={`${chipBase} bg-surface text-primary shadow-inset-sm`}>{patents.length} Toplam Dosya</span>
            {PATENT_STATUSES.map((status) => (
              <span key={status} className={`${chipBase} ${statusStyle(status)}`}>
                {counts.byStatus.get(status) ?? 0} {status}
              </span>
            ))}
            {counts.unset > 0 && <span className={`${chipBase} bg-surface text-on-surface-variant shadow-inset-sm`}>{counts.unset} Durum Girilmemiş</span>}
          </div>
        </div>

        <div className="flex flex-col gap-space-sm px-space-lg pt-space-md">
          <div className="relative">
            <Icon name="search" className="absolute left-space-md top-1/2 -translate-y-1/2 text-[20px] text-on-surface-variant" />
            <input
              type="text"
              value={q}
              onChange={(event) => setQ(event.target.value)}
              placeholder="Başlıkta ara..."
              aria-label="Başlıkta ara"
              className="h-10 w-full rounded-xl bg-surface pl-11 pr-space-md font-body-md text-body-md text-on-surface shadow-inset placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div className="flex flex-wrap gap-space-xs">
            {[['', 'Tümü', patents.length] as const, ...counts.types.map(([n, c]) => [n, n, c] as const)].map(([value, label, count]) => (
              <button
                key={label}
                type="button"
                aria-pressed={type === value}
                onClick={() => setType(value)}
                className={`${chipBase} bg-surface transition-all ${type === value ? 'text-primary shadow-inset-sm' : 'text-on-surface-variant shadow-raised-sm hover:text-on-surface'}`}
              >
                {label} {count}
              </button>
            ))}
          </div>
        </div>

        <div className="min-h-[120px] flex-1 overflow-y-auto p-space-lg">
          {patents.length === 0 ? (
            <p className="text-on-surface-variant">Bu kayda bağlı patent yok.</p>
          ) : visible.length === 0 ? (
            <p className="text-on-surface-variant">Eşleşen patent yok.</p>
          ) : (
            <ul className="flex flex-col gap-space-sm">
              {visible.map((patent) => {
                const style = typeStyle(patent.fsmh_type_name)
                const expanded = open.has(patent.id)
                const year = patent.application_date?.slice(0, 4)
                return (
                  <li key={patent.id} className={`overflow-hidden rounded-xl border-l-4 bg-surface shadow-raised ${style.stripe}`}>
                    <div className="flex items-center gap-space-sm p-space-sm">
                      <span aria-hidden className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg font-label-md text-label-md font-bold ${style.box}`}>
                        {patent.fsmh_type_name.slice(0, 2).toLocaleUpperCase('tr')}
                      </span>
                      <button type="button" aria-expanded={expanded} onClick={() => toggle(patent.id)} className="flex min-w-0 flex-1 flex-wrap items-center gap-x-space-sm gap-y-1 text-left">
                        <span className="font-title-sm text-title-sm font-semibold text-on-surface">{patent.title}</span>
                        <span className={`rounded-full px-space-sm py-0.5 font-label-sm text-label-sm font-semibold ${style.pill}`}>{patent.fsmh_type_name}</span>
                        {patent.status && <span className={`rounded-full px-space-sm py-0.5 font-label-sm text-label-sm font-semibold ${statusStyle(patent.status)}`}>{patent.status}</span>}
                        {year && <span className="font-label-sm text-label-sm text-on-surface-variant">{year}</span>}
                      </button>
                      <button type="button" aria-label={expanded ? 'Daralt' : 'Genişlet'} onClick={() => toggle(patent.id)} className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface text-on-surface-variant shadow-raised-sm hover:text-primary">
                        <Icon name={expanded ? 'expand_less' : 'expand_more'} className="text-[22px]" />
                      </button>
                    </div>
                    {expanded && (
                      <div className="flex flex-wrap items-end gap-space-sm border-t border-surface-variant/40 p-space-sm">
                        <div className="min-w-[140px] rounded-xl bg-surface px-space-md py-space-xs shadow-inset-sm">
                          <div className="font-label-sm text-label-sm text-on-surface-variant">Başvuru Tarihi</div>
                          <div className="font-label-lg text-label-lg text-on-surface">{formatDate(patent.application_date)}</div>
                        </div>
                        <div className="min-w-[140px] rounded-xl bg-surface px-space-md py-space-xs shadow-inset-sm">
                          <div className="font-label-sm text-label-sm text-on-surface-variant">Tescil Tarihi</div>
                          <div className="font-label-lg text-label-lg text-on-surface">{formatDate(patent.registration_date)}</div>
                        </div>
                        <button type="button" onClick={() => go(`/patents/${patent.id}`)} className="ml-auto flex h-10 items-center gap-space-xs rounded-xl bg-surface px-space-md font-label-lg text-label-lg font-semibold text-primary shadow-raised transition-all hover:shadow-raised-sm active:shadow-inset-sm">
                          <Icon name="edit" className="text-[18px]" />
                          Düzenle
                        </button>
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        <div className="flex items-center justify-between gap-space-sm bg-surface p-6 shadow-[0_-4px_12px_rgba(0,0,0,0.03)]">
          <button type="button" onClick={onClose} className="h-10 rounded-xl bg-surface px-space-md font-label-lg text-label-lg font-medium text-on-surface-variant shadow-raised-sm transition-colors hover:text-on-surface">
            Kapat
          </button>
          <button type="button" onClick={() => go('/patents/new')} className="flex h-10 items-center gap-space-xs rounded-xl bg-surface px-space-md font-label-lg text-label-lg font-semibold text-primary shadow-raised transition-all hover:shadow-raised-sm active:shadow-inset-sm">
            <Icon name="add_circle" className="text-[18px]" />
            Yeni Patent Ekle
          </button>
        </div>
      </div>
    </div>
  )
}
