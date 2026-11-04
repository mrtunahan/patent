import { useEffect, useState } from 'react'
import { isAbort } from '../api/client'
import { listPatents } from '../api/patents'
import type { FsmhTypeRead } from '../api/types'
import { percent, typeStyle } from '../lib/format'
import Icon from './Icon'

interface Summary {
  total: number
  byType: { id: number; name: string; count: number }[]
}

const count = (params: Parameters<typeof listPatents>[0], signal: AbortSignal) =>
  listPatents({ ...params, page_size: 1 }, signal).then((page) => page.total)

const pillClass =
  'emboss-text inline-flex items-center gap-space-xs rounded-full bg-surface px-space-md py-1 text-[11px] font-semibold uppercase tracking-wider text-primary shadow-inset-sm'
const cardClass = 'relative flex min-w-0 flex-col overflow-hidden rounded-xl bg-surface p-5 shadow-card'

export default function SummaryCards({ fsmhTypes, refreshKey }: { fsmhTypes: FsmhTypeRead[] | null; refreshKey: number }) {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!fsmhTypes) return
    const controller = new AbortController()
    const { signal } = controller
    setError(false)
    Promise.all([
      count({}, signal),
      Promise.all(fsmhTypes.map((type) => count({ fsmh_type_id: type.id }, signal))),
    ])
      .then(([total, perType]) =>
        setSummary({
          total,
          byType: fsmhTypes.map((type, index) => ({ id: type.id, name: type.name, count: perType[index] })),
        }),
      )
      .catch((err) => {
        if (!isAbort(err)) setError(true)
      })
    return () => controller.abort()
  }, [fsmhTypes, refreshKey])

  const value = (n: number | undefined) => (n === undefined ? '-' : n)
  const total = summary?.total ?? 0
  const rows = summary?.byType ?? fsmhTypes?.map((type) => ({ id: type.id, name: type.name, count: undefined as number | undefined })) ?? []
  const leader = summary ? summary.byType.reduce<(typeof summary.byType)[number] | null>((best, item) => (item.count > 0 && (!best || item.count > best.count) ? item : best), null) : null

  return (
    <div className="grid grid-cols-1 gap-space-md lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
      <div className={cardClass}>
        <div className="flex items-center justify-between gap-space-sm">
          <span className={pillClass}>
            <Icon name="folder_special" className="text-[16px]" />
            Toplam Başvuru Dosyası
          </span>
        </div>
        <div className="mt-space-md flex items-baseline gap-space-sm border-t border-surface-variant/40 pt-space-md">
          <span className="text-4xl font-semibold tracking-tight text-primary">{value(summary?.total)}</span>
          <span className="font-label-md text-label-md font-semibold text-on-surface-variant">Aktif Dosya</span>
        </div>
        <p className="mt-space-xs font-label-sm text-label-sm text-on-surface-variant">Takip listesindeki aktif başvuru kayıtları</p>
        {error && <span className="mt-space-sm font-label-sm text-label-sm text-error">Özet yüklenemedi.</span>}
      </div>

      <div className={cardClass}>
        <div className="flex flex-wrap items-center gap-space-sm">
          <span className={pillClass}>
            <Icon name="category" className="text-[16px]" />
            Türe Göre Portföy Dağılımı
          </span>
          <span className="font-label-md text-label-md text-on-surface-variant">· {fsmhTypes?.length ?? 0} kategori</span>
        </div>
        <ul className="mt-space-md grid grid-cols-1 gap-x-space-lg gap-y-space-md border-t border-surface-variant/40 pt-space-md md:grid-cols-2">
          {rows.map((item) => {
            const style = typeStyle(item.name)
            const share = item.count === undefined ? 0 : total > 0 ? (item.count / total) * 100 : 0
            return (
              <li key={item.id} className="flex min-w-0 flex-col gap-space-xs">
                <div className="flex items-center justify-between gap-space-sm">
                  <span className={`inline-flex min-w-0 items-center gap-1.5 rounded-full px-space-sm py-1 font-label-sm text-label-sm font-semibold ${style.pill}`}>
                    <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${style.dot}`} />
                    <span className="truncate">{item.name}</span>
                  </span>
                  <span className="flex shrink-0 items-baseline gap-space-xs">
                    <strong className="font-title-sm text-title-sm text-on-surface">{value(item.count)}</strong>
                    {item.count !== undefined && <span className="font-label-sm text-label-sm text-on-surface-variant">%{percent(item.count, total)}</span>}
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface shadow-inset-sm">
                  <div className={`h-full rounded-full ${style.dot}`} style={{ width: `${share}%` }} />
                </div>
                {leader?.id === item.id && (
                  <span className="self-start rounded-full bg-surface px-space-sm py-0.5 font-label-sm text-label-sm font-semibold text-tertiary shadow-inset-sm">
                    %{percent(item.count ?? 0, total)} Portföy Lideri
                  </span>
                )}
              </li>
            )
          })}
        </ul>
        <div className="mt-space-md flex items-center justify-between border-t border-surface-variant/40 pt-space-sm font-label-md text-label-md text-on-surface-variant">
          <span>
            Toplam <strong className="text-on-surface">{value(summary?.total)}</strong> kayıt
          </span>
        </div>
      </div>
    </div>
  )
}
