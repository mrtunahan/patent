import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import type { PatentRef } from '../api/types'
import type { Status } from '../lib/hooks'
import { matchesQuery } from '../lib/hooks'
import Icon from './Icon'
import MonogramBadge from './MonogramBadge'
import Pagination from './Pagination'
import TypeChips from './TypeChips'

type SortMode = 'name' | 'most' | 'least'
const SORT_OPTIONS: { mode: SortMode; label: string }[] = [
  { mode: 'name', label: 'Ad (A-Z)' },
  { mode: 'most', label: 'En çok patent' },
  { mode: 'least', label: 'En az patent' },
]

const cell = 'px-space-md py-space-md'
const iconButton = 'flex h-8 w-8 items-center justify-center rounded-lg bg-surface text-on-surface-variant shadow-raised-sm transition-all'

export interface ExtraColumn<T> {
  header: string
  className?: string
  render: (item: T) => ReactNode
}

interface Props<T> {
  title: string
  icon: string
  searchPlaceholder: string
  items: T[] | null
  status: Status
  errorMessage: string
  onRetry: () => void
  rowKey: (item: T) => string | number
  nameOf: (item: T) => string
  searchTexts: (item: T) => (string | null | undefined)[]
  countOf: (item: T) => number
  patentsOf: (item: T) => PatentRef[]
  monogramOf: (item: T) => string
  nameHeader: string
  extraColumns?: ExtraColumn<T>[]
  onSummary: (item: T) => void
  // verilmezse satır tıklaması ve İşlemler sütunu yoktur (salt okunur liste)
  onEdit?: (item: T) => void
  onDelete?: (item: T) => void
}

// Dört modülün (Bölümler, Başvuru Sahipleri, Vekil Firmalar, Ortaklar) ortak liste görünümü:
// filtre kartı (arama, sıralama, temizle), tablo kartı ve istemci tarafı sayfalama.
export default function EntityListLayout<T>(props: Props<T>) {
  const { items, status, nameOf, countOf, onEdit, onDelete, extraColumns = [] } = props
  const [q, setQ] = useState('')
  const [sort, setSort] = useState<SortMode>('name')
  const [menuOpen, setMenuOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const menuRef = useRef<HTMLDivElement>(null)
  const editable = Boolean(onEdit && onDelete)

  useEffect(() => {
    if (!menuOpen) return
    const onPointer = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) setMenuOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [menuOpen])

  const rows = useMemo(() => {
    const filtered = (items ?? []).filter((item) => matchesQuery(q, ...props.searchTexts(item)))
    if (sort === 'name') return filtered // backend sırası
    const dir = sort === 'most' ? -1 : 1
    return [...filtered].sort((a, b) => dir * (countOf(a) - countOf(b)) || nameOf(a).localeCompare(nameOf(b), 'tr'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, q, sort])

  const maxCount = useMemo(() => Math.max(0, ...(items ?? []).map(countOf)), [items]) // eslint-disable-line react-hooks/exhaustive-deps
  const last = Math.max(1, Math.ceil(rows.length / pageSize))
  const current = Math.min(page, last) // silme sonrası sayfa aşımında son geçerli sayfa
  const offset = (current - 1) * pageSize
  const pageRows = rows.slice(offset, offset + pageSize)
  const colSpan = 4 + extraColumns.length + (editable ? 1 : 0)
  const filterActive = q !== '' || sort !== 'name'

  const reset = () => {
    setQ('')
    setSort('name')
    setPage(1)
  }

  const message = (content: ReactNode) => (
    <tr>
      <td colSpan={colSpan} className="px-space-md py-space-xl text-on-surface-variant">
        <div className="sticky left-space-md inline-flex flex-wrap items-center gap-space-sm">{content}</div>
      </td>
    </tr>
  )

  return (
    <>
      <div className="flex flex-wrap items-center gap-space-sm rounded-xl bg-surface p-5 shadow-card">
        <div className="relative min-w-[220px] flex-1">
          <Icon name="search" className="absolute left-space-md top-1/2 -translate-y-1/2 text-[20px] text-on-surface-variant" />
          <input
            type="text"
            value={q}
            onChange={(event) => {
              setQ(event.target.value)
              setPage(1)
            }}
            placeholder={props.searchPlaceholder}
            aria-label="Ara"
            className="h-10 w-full rounded-xl bg-surface pl-11 pr-space-md font-body-md text-body-md text-on-surface shadow-inset placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <div ref={menuRef} className="relative">
          <button
            type="button"
            title="Sırala"
            aria-label="Sırala"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-surface text-on-surface-variant shadow-raised-sm transition-colors hover:text-primary"
          >
            <Icon name="swap_vert" className="text-[20px]" />
          </button>
          {menuOpen && (
            <div role="menu" className="absolute left-0 top-12 z-20 min-w-[170px] rounded-xl bg-surface py-space-xs shadow-modal">
              {SORT_OPTIONS.map((option) => (
                <button
                  key={option.mode}
                  type="button"
                  role="menuitemradio"
                  aria-checked={sort === option.mode}
                  onClick={() => {
                    setSort(option.mode)
                    setPage(1)
                    setMenuOpen(false)
                  }}
                  className={`flex w-full items-center gap-space-sm px-space-md py-space-sm text-left font-label-lg text-label-lg transition-colors hover:bg-surface-bright/60 ${sort === option.mode ? 'font-semibold text-primary' : 'text-on-surface'}`}
                >
                  <Icon name="check" className={`text-[18px] ${sort === option.mode ? '' : 'invisible'}`} />
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={reset}
          disabled={!filterActive}
          className="h-10 rounded-xl bg-surface px-space-md font-label-lg text-label-lg font-medium text-secondary shadow-raised-sm transition-colors hover:text-on-surface disabled:opacity-50 disabled:shadow-none"
        >
          Temizle
        </button>
        <span className="ml-auto font-label-lg text-label-lg text-on-surface-variant">{status === 'ready' ? `${rows.length} kayıt` : '-'}</span>
      </div>

      <div className="flex min-w-0 flex-col overflow-hidden rounded-xl bg-surface shadow-raised">
        <div className="flex items-center gap-space-sm p-space-md">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface text-primary shadow-inset-sm">
            <Icon name={props.icon} className="text-[20px]" />
          </div>
          <span className="font-title-md text-title-md font-semibold text-on-surface">{props.title}</span>
        </div>
        <div className="w-full overflow-x-auto">
          <table className="w-full min-w-[820px] border-collapse text-left">
            <thead>
              <tr className="select-none bg-surface-container-low text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">
                <th className={`${cell} w-[70px]`}>No</th>
                <th className={cell}>{props.nameHeader}</th>
                {extraColumns.map((col) => (
                  <th key={col.header} className={`${cell} ${col.className ?? ''}`}>
                    {col.header}
                  </th>
                ))}
                <th className={`${cell} w-[240px]`}>Tür Dağılımı</th>
                <th className={`${cell} w-[130px]`}>Patent Sayısı</th>
                {editable && <th className={`${cell} w-[110px] text-center`}>İşlemler</th>}
              </tr>
            </thead>
            <tbody className="font-body-md text-body-md">
              {status === 'error' &&
                message(
                  <>
                    <span>{props.errorMessage}</span>
                    <button type="button" onClick={props.onRetry} className="rounded-xl bg-surface px-space-md py-space-xs font-label-md text-label-md font-semibold text-primary shadow-raised-sm">
                      Yeniden dene
                    </button>
                  </>,
                )}
              {status === 'loading' && message('Yükleniyor...')}
              {status === 'ready' && rows.length === 0 && message('Kayıt bulunamadı.')}
              {status === 'ready' &&
                pageRows.map((item, index) => {
                  const count = countOf(item)
                  const top = count > 0 && count === maxCount
                  return (
                    <tr
                      key={props.rowKey(item)}
                      onClick={onEdit ? () => onEdit(item) : undefined}
                      className={`border-b border-surface-variant/30 transition-colors hover:bg-surface-bright/50 ${onEdit ? 'cursor-pointer' : ''}`}
                    >
                      <td className={`${cell} font-label-md text-label-md text-on-surface-variant`}>{offset + index + 1}</td>
                      <td className={cell}>
                        <div className="flex items-center gap-space-sm">
                          <MonogramBadge text={props.monogramOf(item)} strong={top} />
                          <span className="font-medium text-on-surface">{nameOf(item)}</span>
                        </div>
                      </td>
                      {extraColumns.map((col) => (
                        <td key={col.header} className={`${cell} text-on-surface-variant`}>
                          {col.render(item)}
                        </td>
                      ))}
                      <td className={cell}>
                        <TypeChips patents={props.patentsOf(item)} />
                      </td>
                      <td className={cell}>
                        <button
                          type="button"
                          title="Patentleri göster"
                          onClick={(event) => {
                            event.stopPropagation()
                            props.onSummary(item)
                          }}
                          className={`inline-flex min-w-[44px] items-center justify-center rounded-full bg-surface px-space-sm py-1 font-label-md text-label-md font-semibold shadow-inset-sm transition-colors hover:text-primary-container ${top ? 'text-tertiary' : 'text-primary'}`}
                        >
                          {count}
                        </button>
                      </td>
                      {editable && (
                        <td className={cell}>
                          <div className="flex items-center justify-center gap-1">
                            <button
                              type="button"
                              title="Düzenle"
                              aria-label="Düzenle"
                              onClick={(event) => {
                                event.stopPropagation()
                                onEdit?.(item)
                              }}
                              className={`${iconButton} hover:text-primary`}
                            >
                              <Icon name="edit" className="text-[18px]" />
                            </button>
                            <button
                              type="button"
                              title="Sil"
                              aria-label="Sil"
                              onClick={(event) => {
                                event.stopPropagation()
                                onDelete?.(item)
                              }}
                              className={`${iconButton} hover:text-error`}
                            >
                              <Icon name="delete" className="text-[18px]" />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
        {status === 'ready' && rows.length > 0 && (
          <Pagination
            page={current}
            pageSize={pageSize}
            total={rows.length}
            onPage={setPage}
            onPageSize={(size) => {
              setPageSize(size)
              setPage(1)
            }}
          />
        )}
      </div>
    </>
  )
}
