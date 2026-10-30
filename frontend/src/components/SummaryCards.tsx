import { useEffect, useState } from 'react'
import { isAbort } from '../api/client'
import { listPatents } from '../api/patents'
import type { FsmhTypeRead } from '../api/types'
import { fsmhTypeStyle } from '../lib/format'
import Icon from './Icon'

interface Summary {
  total: number
  byType: { id: number; name: string; count: number }[]
  withAttorney: number
  withoutAttorney: number
}

const count = (params: Parameters<typeof listPatents>[0], signal: AbortSignal) =>
  listPatents({ ...params, page_size: 1 }, signal).then((page) => page.total)

function Card({ title, icon, iconClass, children }: { title: string; icon: string; iconClass: string; children: React.ReactNode }) {
  return (
    <div className="relative flex min-w-0 flex-col justify-between overflow-hidden rounded-xl bg-surface-container p-space-md shadow-sm">
      <div className="flex items-center justify-between">
        <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">{title}</span>
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconClass}`}>
          <Icon name={icon} className="text-[20px]" />
        </div>
      </div>
      {children}
    </div>
  )
}

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
      count({ has_attorney: true }, signal),
      count({ has_attorney: false }, signal),
    ])
      .then(([total, perType, withAttorney, withoutAttorney]) =>
        setSummary({
          total,
          byType: fsmhTypes.map((type, index) => ({ id: type.id, name: type.name, count: perType[index] })),
          withAttorney,
          withoutAttorney,
        }),
      )
      .catch((err) => {
        if (!isAbort(err)) setError(true)
      })
    return () => controller.abort()
  }, [fsmhTypes, refreshKey])

  const value = (n: number | undefined) => (n === undefined ? '-' : n)

  return (
    <div className="grid grid-cols-1 gap-space-md md:grid-cols-2 xl:grid-cols-3">
      <Card title="Toplam Kayıt" icon="folder_special" iconClass="bg-primary-fixed text-on-primary-fixed">
        <div className="mt-space-md flex items-baseline gap-space-sm">
          <span className="font-display-lg text-display-lg font-bold tracking-tight text-on-surface">{value(summary?.total)}</span>
          <span className="font-label-md text-label-md text-on-surface-variant">aktif kayıt</span>
        </div>
        {error && <span className="mt-space-sm font-label-sm text-label-sm text-error">Özet yüklenemedi.</span>}
        <div className="pointer-events-none absolute -bottom-4 -right-4 h-24 w-24 rounded-full bg-primary/5" />
      </Card>
      <Card title="Türe Göre" icon="category" iconClass="bg-secondary-fixed text-on-secondary-fixed">
        <ul className="mt-space-md grid grid-cols-2 gap-x-space-md gap-y-space-xs">
          {(summary?.byType ?? fsmhTypes?.map((type) => ({ id: type.id, name: type.name, count: undefined })) ?? []).map((item) => (
            <li key={item.id} className="flex items-center justify-between gap-space-sm font-label-md text-label-md text-on-surface">
              <span className="flex min-w-0 items-center gap-space-xs">
                <span className={`h-2 w-2 shrink-0 rounded-full ${fsmhTypeStyle(item.name).dot}`} />
                <span className="truncate">{item.name}</span>
              </span>
              <strong className="font-title-sm text-title-sm">{value(item.count)}</strong>
            </li>
          ))}
        </ul>
        <div className="pointer-events-none absolute -bottom-4 -right-4 h-24 w-24 rounded-full bg-secondary/5" />
      </Card>
      <Card title="Vekil Durumu" icon="business_center" iconClass="bg-tertiary-fixed text-on-tertiary-fixed">
        <div className="mt-space-md flex items-baseline gap-space-lg">
          <div className="flex items-baseline gap-space-xs">
            <span className="font-display-lg text-display-lg font-bold tracking-tight text-on-surface">{value(summary?.withAttorney)}</span>
            <span className="font-label-md text-label-md text-on-surface-variant">vekilli</span>
          </div>
          <div className="flex items-baseline gap-space-xs">
            <span className="font-headline-md text-headline-md font-semibold text-on-surface-variant">{value(summary?.withoutAttorney)}</span>
            <span className="font-label-md text-label-md text-on-surface-variant">vekilsiz</span>
          </div>
        </div>
        <div className="pointer-events-none absolute -bottom-4 -right-4 h-24 w-24 rounded-full bg-tertiary/5" />
      </Card>
    </div>
  )
}
