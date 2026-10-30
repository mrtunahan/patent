import type { PatentRead, SortDir, SortField } from '../api/types'
import { formatDate, fsmhTypeStyle } from '../lib/format'
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

const th = 'px-space-md py-space-md'
const dash = <span className="text-on-surface-variant">-</span>

function SortHeader({ label, field, sortBy, sortDir, onSort }: { label: string; field: SortField } & Pick<Props, 'sortBy' | 'sortDir' | 'onSort'>) {
  const active = sortBy === field
  const icon = !active ? 'unfold_more' : sortDir === 'asc' ? 'arrow_upward' : 'arrow_downward'
  return (
    <button
      type="button"
      onClick={() => onSort(field)}
      className="flex w-full items-center justify-between gap-space-xs text-left uppercase tracking-wider hover:text-primary"
    >
      <span>{label}</span>
      <Icon name={icon} className={`text-[16px] ${active ? 'text-primary' : 'text-on-surface-variant'}`} />
    </button>
  )
}

export default function PatentTable({
  items, status, errorMessage, page, pageSize, sortBy, sortDir, onSort, onEdit, onDelete, onRetry,
}: Props) {
  const sortProps = { sortBy, sortDir, onSort }
  const ariaSort = (field: SortField) => (sortBy === field ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none')
  const message = (text: string, action?: React.ReactNode) => (
    <tr>
      <td colSpan={10} className="bg-surface-container-lowest px-space-md py-space-xl text-on-surface-variant">
        <div className="sticky left-space-md inline-flex flex-wrap items-center gap-space-sm">
          <span>{text}</span>
          {action}
        </div>
      </td>
    </tr>
  )

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[1500px] border-collapse text-left">
        <thead>
          <tr className="select-none bg-surface-container-highest font-label-sm text-label-sm uppercase tracking-wider text-on-surface">
            <th className={`${th} w-[70px]`}>No</th>
            <th aria-sort={ariaSort('title')} className={`${th} sticky left-0 z-20 w-[300px] bg-surface-container-highest`}>
              <SortHeader label="Buluş Başlığı" field="title" {...sortProps} />
            </th>
            <th aria-sort={ariaSort('applicant')} className={`${th} w-[190px]`}>
              <SortHeader label="Başvuru Sahibi" field="applicant" {...sortProps} />
            </th>
            <th aria-sort={ariaSort('department')} className={`${th} w-[170px]`}>
              <SortHeader label="Bölüm / Birim" field="department" {...sortProps} />
            </th>
            <th aria-sort={ariaSort('fsmh_type')} className={`${th} w-[150px]`}>
              <SortHeader label="FSMH Türü" field="fsmh_type" {...sortProps} />
            </th>
            <th aria-sort={ariaSort('attorney_firm')} className={`${th} w-[170px]`}>
              <SortHeader label="Vekil Firma" field="attorney_firm" {...sortProps} />
            </th>
            <th className={`${th} w-[220px]`}>Ortaklar &amp; Oranları</th>
            <th aria-sort={ariaSort('application_date')} className={`${th} w-[150px]`}>
              <SortHeader label="Başvuru Tarihi" field="application_date" {...sortProps} />
            </th>
            <th className={`${th} w-[230px]`}>Notlar / Açıklama</th>
            <th className={`${th} sticky right-0 z-20 w-[110px] bg-surface-container-highest text-center`}>İşlemler</th>
          </tr>
        </thead>
        <tbody className={`font-body-md text-body-md ${status === 'loading' && items ? 'opacity-60' : ''}`}>
          {status === 'error' &&
            message(
              errorMessage,
              <button type="button" onClick={onRetry} className="rounded-lg bg-primary px-space-md py-space-xs font-label-md text-label-md text-on-primary">
                Yeniden dene
              </button>,
            )}
          {status === 'loading' && !items && message('Yükleniyor...')}
          {status !== 'error' && items && items.length === 0 && message('Kayıt bulunamadı.')}
          {status !== 'error' &&
            items?.map((patent, index) => {
              const bg = index % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface'
              const style = fsmhTypeStyle(patent.fsmh_type.name)
              return (
                <tr key={patent.id} onClick={() => onEdit(patent.id)} className={`group cursor-pointer transition-colors hover:bg-surface-bright ${bg}`}>
                  <td className="px-space-md py-space-md font-label-md text-label-md text-on-surface-variant">
                    {(page - 1) * pageSize + index + 1}
                  </td>
                  <td className={`sticky left-0 z-10 px-space-md py-space-md font-semibold text-on-surface group-hover:bg-surface-bright ${bg}`}>
                    <span className="font-title-sm text-title-sm text-primary group-hover:underline">{patent.title}</span>
                  </td>
                  <td className="px-space-md py-space-md text-on-surface">
                    <div className="flex items-center gap-space-xs">
                      <Icon name="person" className="shrink-0 text-[18px] text-secondary" />
                      <span className="font-medium">{patent.applicant.full_name}</span>
                    </div>
                  </td>
                  <td className="px-space-md py-space-md text-on-surface-variant">{patent.department?.name ?? dash}</td>
                  <td className="px-space-md py-space-md">
                    <span className={`inline-flex items-center gap-1 rounded-full px-space-sm py-1 font-label-sm text-label-sm font-semibold ${style.pill}`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
                      {patent.fsmh_type.name}
                    </span>
                  </td>
                  <td className="px-space-md py-space-md text-on-surface">{patent.attorney_firm?.name ?? dash}</td>
                  <td className="px-space-md py-space-md">
                    {patent.partners.length === 0 ? (
                      dash
                    ) : (
                      <div className="flex flex-col gap-0.5 font-label-sm text-label-sm text-on-surface">
                        {patent.partners.map((name, i) => (
                          <span key={`${name}-${i}`}>{name}</span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-space-md py-space-md font-label-md text-label-md text-on-surface">{formatDate(patent.application_date)}</td>
                  <td className="max-w-xs truncate px-space-md py-space-md font-body-sm text-body-sm text-on-surface-variant" title={patent.notes ?? undefined}>
                    {patent.notes || dash}
                  </td>
                  <td className={`sticky right-0 z-10 px-space-md py-space-md text-center group-hover:bg-surface-bright ${bg}`}>
                    <div className="flex items-center justify-center gap-1">
                      <button
                        type="button"
                        title="Düzenle"
                        aria-label="Düzenle"
                        onClick={(event) => {
                          event.stopPropagation()
                          onEdit(patent.id)
                        }}
                        className="flex h-8 w-8 items-center justify-center rounded-full text-secondary transition-colors hover:bg-secondary-container"
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
                        className="flex h-8 w-8 items-center justify-center rounded-full text-error transition-colors hover:bg-error-container"
                      >
                        <Icon name="delete" className="text-[18px]" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
        </tbody>
      </table>
    </div>
  )
}
