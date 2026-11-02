import { useEffect, useState } from 'react'
import type { Lookups } from '../api/types'
import Icon from './Icon'

export interface Filters {
  q: string
  fsmhTypeId: string
  applicantId: string
  departmentId: string
  attorneyFirmId: string
  hasAttorney: '' | 'true' | 'false'
  dateFrom: string
}

export const EMPTY_FILTERS: Filters = {
  q: '', fsmhTypeId: '', applicantId: '', departmentId: '', attorneyFirmId: '', hasAttorney: '', dateFrom: '',
}

interface Props {
  filters: Filters
  lookups: Lookups | null
  total: number | null
  onChange: (patch: Partial<Filters>) => void
  onReset: () => void
}

const selectClass =
  'h-11 w-full min-w-0 cursor-pointer rounded-lg bg-surface-container-lowest px-space-md font-label-lg text-label-lg text-on-surface focus:outline-none'

export default function FilterBar({ filters, lookups, total, onChange, onReset }: Props) {
  const [qInput, setQInput] = useState(filters.q)

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
    <div className="flex min-w-0 flex-col gap-space-md rounded-xl bg-surface-container p-space-md border border-primary-container/30 shadow-card">
      <div className="flex flex-col items-stretch gap-space-md lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Icon name="search" className="absolute left-space-md top-1/2 -translate-y-1/2 text-[20px] text-on-surface-variant" />
          <input
            type="text"
            value={qInput}
            onChange={(event) => setQInput(event.target.value)}
            placeholder="Buluş başlığı, başvuru sahibi, ortak veya not ara..."
            aria-label="Ara"
            className="h-11 w-full rounded-lg bg-surface-container-lowest pl-11 pr-space-md font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant focus:bg-surface-bright focus:outline-none"
          />
        </div>
        <button
          type="button"
          onClick={() => {
            setQInput('')
            onReset()
          }}
          title="Filtreleri Temizle"
          className="flex h-11 items-center justify-center gap-space-xs rounded-lg bg-secondary-container px-space-md font-label-md text-label-md text-on-secondary-container transition-colors hover:bg-surface-container-high"
        >
          <Icon name="clear_all" className="text-[18px]" />
          Temizle
        </button>
      </div>

      <div className="grid grid-cols-1 gap-space-sm sm:grid-cols-2 xl:grid-cols-5">
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
        <select aria-label="Vekil Firma" value={filters.attorneyFirmId} onChange={(e) => onChange({ attorneyFirmId: e.target.value })} className={selectClass}>
          <option value="">Vekil Firma: Tümü</option>
          {options(lookups?.attorneyFirms, (f) => f.name)}
        </select>
        <select
          aria-label="Vekil Durumu"
          value={filters.hasAttorney}
          onChange={(e) => onChange({ hasAttorney: e.target.value as Filters['hasAttorney'] })}
          className={selectClass}
        >
          <option value="">Vekil Durumu: Tümü</option>
          <option value="true">Vekilli</option>
          <option value="false">Vekilsiz</option>
        </select>
      </div>

      <div className="flex flex-wrap items-end gap-space-md">
        <label className="flex flex-col gap-space-xs font-label-sm text-label-sm text-on-surface-variant">
          Başvuru tarihinden itibaren
          <input type="date" value={filters.dateFrom} onChange={(e) => onChange({ dateFrom: e.target.value })} className="h-10 rounded-lg bg-surface-container-lowest px-space-sm font-body-md text-body-md text-on-surface focus:outline-none" />
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-space-sm pt-space-xs font-label-sm text-label-sm text-on-surface-variant">
        <span className="font-medium text-on-surface">Aktif Veri Görünümü:</span>
        <span className="rounded-full bg-surface-container-high px-space-sm py-0.5 text-on-surface">
          Kayıt: <strong>{total ?? '-'}</strong>
        </span>
      </div>
    </div>
  )
}
