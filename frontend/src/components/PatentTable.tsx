import type { ReactNode } from 'react'
import type { PatentRead, SortDir, SortField } from '../api/types'
import { formatDate, statusStyle, typeStyle } from '../lib/format'
import Avatar from './Avatar'
import Icon from './Icon'

interface Props {
  items: PatentRead[] | null
  status: 'loading' | 'error' | 'ready'
  errorMessage: string
  page: number
  pageSize: number
  sortBy: SortField
  sortDir: SortDir
  onSort: (field: SortField) => void
  onEdit: (id: number) => void
  onDelete: (patent: PatentRead) => void
  onRetry: () => void
}

const dash = <span className="text-on-surface-variant">-</span>

interface Column {
  key: string
  label: string
  width: string
  sortField?: SortField
  hiddenInList?: boolean // yalnızca listede gizli; çekmece, Excel dışa aktarma ve API etkilenmez
  render: (patent: PatentRead) => ReactNode
}

// Veri sütunları (No ve İşlemler tabloda ayrıca çizilir). hiddenInList sütunların kodu korunur.
const COLUMNS: Column[] = [
  {
    key: 'title',
    label: 'Buluş Başlığı',
    width: 'w-[340px]',
    sortField: 'title',
    render: (p) => <span className="font-title-sm text-title-sm font-semibold text-primary group-hover:underline">{p.title}</span>,
  },
  {
    key: 'applicant',
    label: 'Başvuru Sahibi',
    width: 'w-[230px]',
    sortField: 'applicant',
    render: (p) => (
      <div className="flex items-center gap-space-sm">
        <Avatar name={p.applicant.full_name} />
        <span className="font-medium text-on-surface">{p.applicant.full_name}</span>
      </div>
    ),
  },
  {
    key: 'department',
    label: 'Bölüm / Birim',
    width: 'w-[210px]',
    sortField: 'department',
    render: (p) =>
      p.department ? (
        <span className="inline-block rounded-lg bg-surface px-space-sm py-0.5 shadow-inset-sm font-label-md text-label-md text-on-surface-variant">{p.department.name}</span>
      ) : (
        dash
      ),
  },
  {
    key: 'fsmh_type',
    label: 'FSMH Türü',
    width: 'w-[170px]',
    sortField: 'fsmh_type',
    render: (p) => {
      const style = typeStyle(p.fsmh_type.name)
      return (
        <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-space-sm py-1 font-label-sm text-label-sm font-semibold ${style.pill}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
          {p.fsmh_type.name}
        </span>
      )
    },
  },
  {
    key: 'status',
    label: 'Durum',
    width: 'w-[180px]',
    render: (p) =>
      p.status ? (
        <span className={`inline-flex whitespace-nowrap rounded-full px-space-sm py-1 font-label-sm text-label-sm font-semibold ${statusStyle(p.status)}`}>{p.status}</span>
      ) : (
        dash
      ),
  },
  { key: 'attorney_firm', label: 'Vekil Firma', width: 'w-[170px]', sortField: 'attorney_firm', hiddenInList: true, render: (p) => p.attorney_firm?.name ?? dash },
  {
    key: 'partners',
    label: 'Ortaklar & Oranları',
    width: 'w-[220px]',
    hiddenInList: true,
    render: (p) =>
      p.partners.length === 0 ? (
        dash
      ) : (
        <div className="flex flex-col gap-0.5 font-label-sm text-label-sm text-on-surface">
          {p.partners.map((name, i) => (
            <span key={`${name}-${i}`}>{name}</span>
          ))}
        </div>
      ),
  },
  { key: 'application_date', label: 'Başvuru Tarihi', width: 'w-[150px]', sortField: 'application_date', hiddenInList: true, render: (p) => formatDate(p.application_date) },
  { key: 'registration_date', label: 'Tescil Tarihi', width: 'w-[150px]', hiddenInList: true, render: (p) => formatDate(p.registration_date) },
  { key: 'notes', label: 'Notlar / Açıklama', width: 'w-[230px]', hiddenInList: true, render: (p) => p.notes || dash },
]

const VISIBLE = COLUMNS.filter((column) => !column.hiddenInList)
const th = 'px-space-md py-space-md'

function SortHeader({ column, index, sortBy, sortDir, onSort }: { column: Column; index: number } & Pick<Props, 'sortBy' | 'sortDir' | 'onSort'>) {
  const badge = (
    <span className="flex h-5 min-w-[22px] shrink-0 items-center justify-center rounded bg-surface px-1 font-label-sm text-[10px] font-bold text-primary shadow-inset-sm">
      {String(index + 1).padStart(2, '0')}
    </span>
  )
  if (!column.sortField) {
    return (
      <span className="flex items-center gap-space-xs">
        {badge}
        <span>{column.label}</span>
      </span>
    )
  }
  const field = column.sortField
  const active = sortBy === field
  const icon = !active ? 'unfold_more' : sortDir === 'asc' ? 'arrow_upward' : 'arrow_downward'
  return (
    <button type="button" onClick={() => onSort(field)} className="flex w-full items-center justify-between gap-space-xs text-left uppercase tracking-wider hover:text-primary">
      <span className="flex items-center gap-space-xs">
        {badge}
        <span>{column.label}</span>
      </span>
      <Icon name={icon} className={`text-[16px] ${active ? 'text-primary' : 'text-on-surface-variant'}`} />
    </button>
  )
}

export default function PatentTable({ items, status, errorMessage, page, pageSize, sortBy, sortDir, onSort, onEdit, onDelete, onRetry }: Props) {
  const ariaSort = (field?: SortField) => (field && sortBy === field ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none')
  const colSpan = VISIBLE.length + 2
  const message = (text: string, action?: ReactNode) => (
    <tr>
      <td colSpan={colSpan} className="px-space-md py-space-xl text-on-surface-variant">
        <div className="sticky left-space-md inline-flex flex-wrap items-center gap-space-sm">
          <span>{text}</span>
          {action}
        </div>
      </td>
    </tr>
  )

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[1100px] border-collapse text-left">
        <thead>
          <tr className="select-none bg-surface-container-low text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">
            <th className={`${th} w-[70px]`}>No</th>
            {VISIBLE.map((column, index) => (
              <th key={column.key} aria-sort={ariaSort(column.sortField)} className={`${th} ${column.width}`}>
                <SortHeader column={column} index={index} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
              </th>
            ))}
            <th className={`${th} w-[110px] text-center`}>İşlemler</th>
          </tr>
        </thead>
        <tbody className={`font-body-md text-body-md ${status === 'loading' && items ? 'opacity-60' : ''}`}>
          {status === 'error' &&
            message(
              errorMessage,
              <button type="button" onClick={onRetry} className="rounded-xl bg-surface px-space-md py-space-xs font-label-md text-label-md font-semibold text-primary shadow-raised-sm">
                Yeniden dene
              </button>,
            )}
          {status === 'loading' && !items && message('Yükleniyor...')}
          {status !== 'error' && items && items.length === 0 && message('Kayıt bulunamadı.')}
          {status !== 'error' &&
            items?.map((patent, index) => (
              <tr key={patent.id} onClick={() => onEdit(patent.id)} className={`group cursor-pointer border-b border-surface-variant/30 transition-colors hover:bg-surface-bright/50`}>
                <td className="px-space-md py-space-md font-label-md text-label-md text-on-surface-variant">{(page - 1) * pageSize + index + 1}</td>
                {VISIBLE.map((column) => (
                  <td key={column.key} className="px-space-md py-space-md text-on-surface">
                    {column.render(patent)}
                  </td>
                ))}
                <td className="px-space-md py-space-md text-center">
                  <div className="flex items-center justify-center gap-1">
                    <button
                      type="button"
                      title="Düzenle"
                      aria-label="Düzenle"
                      onClick={(event) => {
                        event.stopPropagation()
                        onEdit(patent.id)
                      }}
                      className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface text-on-surface-variant shadow-raised-sm transition-all hover:text-primary"
                    >
                      <Icon name="edit" className="text-[18px]" />
                    </button>
                    <button
                      type="button"
                      title="Sil"
                      aria-label="Sil"
                      onClick={(event) => {
                        event.stopPropagation()
                        onDelete(patent)
                      }}
                      className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface text-on-surface-variant shadow-raised-sm transition-all hover:text-error"
                    >
                      <Icon name="delete" className="text-[18px]" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}
