import { useEffect, useState } from 'react'
import type { Lookups } from '../api/types'
import Icon from './Icon'

export interface Filters {
  q: string
  fsmhTypeId: string
  applicantId: string
  departmentId: string
}

export const EMPTY_FILTERS: Filters = {
  q: '', fsmhTypeId: '', applicantId: '', departmentId: '',
}

interface Props {
  filters: Filters
  lookups: Lookups | null
  total: number | null
  onChange: (patch: Partial<Filters>) => void
  onReset: () => void
}

const selectClass =
  'h-11 w-full min-w-0 cursor-pointer rounded-xl bg-surface shadow-inset px-space-md font-label-lg text-label-lg text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30'

export default function FilterBar({ filters, lookups, total, onChange, onReset }: Props) {
  const [qInput, setQInput] = useState(filters.q)

  // Arama dışarıdan (üst çubuk, Temizle) değişirse kutu da güncellenir.
  useEffect(() => setQInput(filters.q), [filters.q])

  // 300 ms debounce: yazım durunca arama filtreye işlenir.
  useEffect(() => {
    if (qInput === filters.q) return
    const timer = window.setTimeout(() => onChange({ q: qInput }), 300)
    return () => window.clearTimeout(timer)
  }, [qInput, filters.q, onChange])

  const options = <T extends { id: number }>(items: T[] | undefined, label: (item: T) => string) =>
    (items ?? []).map((item) => (
      <option key={item.id} value={item.id}>
        {label(item)}
      </option>
    ))

  return (
    <div className="flex min-w-0 flex-col gap-space-md rounded-xl bg-surface p-5 shadow-card">
      <div className="flex flex-col items-stretch gap-space-md lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Icon name="search" className="absolute left-space-md top-1/2 -translate-y-1/2 text-[20px] text-on-surface-variant" />
          <input
            type="text"
            value={qInput}
            onChange={(event) => setQInput(event.target.value)}
            placeholder="Buluş başlığı, başvuru sahibi, ortak veya not ara..."
            aria-label="Ara"
            className="h-11 w-full rounded-xl bg-surface shadow-inset pl-11 pr-space-md font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <button
          type="button"
          onClick={() => {
            setQInput('')
            onReset()
          }}
          title="Filtreleri Temizle"
          className="flex h-11 items-center justify-center gap-space-xs rounded-xl bg-surface px-space-md font-label-md text-label-md font-semibold text-secondary shadow-raised-sm transition-colors hover:text-on-surface"
        >
          <Icon name="clear_all" className="text-[18px]" />
          Temizle
        </button>
      </div>

      <div className="grid grid-cols-1 gap-space-sm sm:grid-cols-3">
        <select aria-label="FSMH Türü" value={filters.fsmhTypeId} onChange={(e) => onChange({ fsmhTypeId: e.target.value })} className={selectClass}>
          <option value="">FSMH Türü: Tümü</option>
          {options(lookups?.fsmhTypes, (t) => t.name)}
        </select>
        <select aria-label="Başvuru Sahibi" value={filters.applicantId} onChange={(e) => onChange({ applicantId: e.target.value })} className={selectClass}>
          <option value="">Başvuru Sahibi: Tümü</option>
          {options(lookups?.applicants, (a) => a.full_name)}
        </select>
        <select aria-label="Bölüm / Birim" value={filters.departmentId} onChange={(e) => onChange({ departmentId: e.target.value })} className={selectClass}>
          <option value="">Bölüm / Birim: Tümü</option>
          {options(lookups?.departments, (d) => d.name)}
        </select>
      </div>

      <div className="flex flex-wrap items-center gap-space-sm pt-space-xs font-label-sm text-label-sm text-on-surface-variant">
        <span className="font-medium text-on-surface">Aktif Veri Görünümü:</span>
        <span className="rounded-lg bg-surface px-2.5 py-1 font-medium text-primary shadow-inset-sm">
          Kayıt: <strong>{total ?? '-'}</strong>
        </span>
      </div>
    </div>
  )
}
