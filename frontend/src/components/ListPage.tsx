import type { ReactNode } from 'react'
import type { Status } from '../lib/hooks'
import Icon from './Icon'

export function PageHeader({ crumb, title, subtitle, addLabel, onAdd }: { crumb: string; title: string; subtitle: string; addLabel?: string; onAdd?: () => void }) {
  return (
    <div className="flex flex-col justify-between gap-space-md lg:flex-row lg:items-center">
      <div className="flex flex-col">
        <div className="flex items-center gap-space-xs font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
          <span>TTO Portalı</span>
          <Icon name="chevron_right" className="text-[14px]" />
          <span className="font-semibold text-primary">{crumb}</span>
        </div>
        <h1 className="mt-space-xs font-headline-lg text-headline-lg tracking-tight text-on-surface">{title}</h1>
        <p className="font-body-md text-body-md text-on-surface-variant">{subtitle}</p>
      </div>
      {addLabel && onAdd && (
        <button
          type="button"
          onClick={onAdd}
          className="flex h-10 items-center justify-center gap-space-xs self-start rounded-lg bg-primary px-space-lg font-label-lg text-label-lg text-on-primary shadow-md transition-all hover:bg-primary/95 lg:self-auto"
        >
          <Icon name="add_circle" className="text-[20px]" />
          {addLabel}
        </button>
      )}
    </div>
  )
}

export function SearchCard({ value, onChange, placeholder, count }: { value: string; onChange: (v: string) => void; placeholder: string; count: number | null }) {
  return (
    <div className="flex min-w-0 flex-col gap-space-sm rounded-xl bg-surface-container p-space-md shadow-sm">
      <div className="relative">
        <Icon name="search" className="absolute left-space-md top-1/2 -translate-y-1/2 text-[20px] text-on-surface-variant" />
        <input
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          aria-label="Ara"
          className="h-11 w-full rounded-lg bg-surface-container-lowest pl-11 pr-space-md font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant focus:bg-surface-bright focus:outline-none"
        />
      </div>
      <div className="flex items-center gap-space-sm font-label-sm text-label-sm text-on-surface-variant">
        <span className="rounded-full bg-surface-container-high px-space-sm py-0.5 text-on-surface">
          Kayıt: <strong>{count ?? '-'}</strong>
        </span>
      </div>
    </div>
  )
}

interface TableCardProps {
  title: string
  icon: string
  status: Status
  errorMessage: string
  isEmpty: boolean
  colSpan: number
  minWidth: string
  onRetry: () => void
  head: ReactNode
  children: ReactNode
}

// Tablo kabuğu: başlık şeridi, yatay kaydırma yalnızca tablo kapsayıcısında; yükleniyor / hata / boş durumları.
export function TableCard({ title, icon, status, errorMessage, isEmpty, colSpan, minWidth, onRetry, head, children }: TableCardProps) {
  const message = (content: ReactNode) => (
    <tr>
      <td colSpan={colSpan} className="bg-surface-container-lowest px-space-md py-space-xl text-on-surface-variant">
        <div className="sticky left-space-md inline-flex flex-wrap items-center gap-space-sm">{content}</div>
      </td>
    </tr>
  )
  return (
    <div className="flex min-w-0 flex-col overflow-hidden rounded-xl bg-surface-container shadow-md">
      <div className="flex items-center gap-space-sm bg-surface-container-high p-space-md">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-on-primary">
          <Icon name={icon} className="text-[18px]" />
        </div>
        <span className="font-title-sm text-title-sm font-bold text-on-surface">{title}</span>
      </div>
      <div className="w-full overflow-x-auto">
        <table className="w-full border-collapse text-left" style={{ minWidth }}>
          <thead>
            <tr className="select-none bg-surface-container-highest font-label-sm text-label-sm uppercase tracking-wider text-on-surface">{head}</tr>
          </thead>
          <tbody className="font-body-md text-body-md">
            {status === 'error' &&
              message(
                <>
                  <span>{errorMessage}</span>
                  <button type="button" onClick={onRetry} className="rounded-lg bg-primary px-space-md py-space-xs font-label-md text-label-md text-on-primary">
                    Yeniden dene
                  </button>
                </>,
              )}
            {status === 'loading' && message('Yükleniyor...')}
            {status === 'ready' && isEmpty && message('Kayıt bulunamadı.')}
            {status === 'ready' && children}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export const cell = 'px-space-md py-space-md'

export function RowActions({ onEdit, onDelete }: { onEdit: () => void; onDelete: () => void }) {
  return (
    <div className="flex items-center justify-center gap-1">
      <button
        type="button"
        title="Düzenle"
        aria-label="Düzenle"
        onClick={(event) => {
          event.stopPropagation()
          onEdit()
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
          onDelete()
        }}
        className="flex h-8 w-8 items-center justify-center rounded-full text-error transition-colors hover:bg-error-container"
      >
        <Icon name="delete" className="text-[18px]" />
      </button>
    </div>
  )
}

export function StatusPill({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-space-sm py-1 font-label-sm text-label-sm font-semibold ${
        active ? 'bg-primary-fixed text-on-primary-fixed' : 'bg-surface-container-highest text-on-surface-variant'
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${active ? 'bg-primary' : 'bg-outline'}`} />
      {active ? 'Aktif' : 'Pasif'}
    </span>
  )
}

// Patent sayısı düğmesi: tıklayınca satırın altında patent başlıkları açılır / kapanır (satır tıklamasını tetiklemez).
export function CountToggle({ count, open, onToggle }: { count: number; open: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      disabled={count === 0}
      aria-expanded={open}
      title={count === 0 ? undefined : open ? 'Patentleri gizle' : 'Patentleri göster'}
      onClick={(event) => {
        event.stopPropagation()
        onToggle()
      }}
      className="inline-flex min-w-[44px] items-center justify-center gap-1 rounded-full bg-secondary-container px-space-sm py-1 font-label-md text-label-md font-semibold text-on-secondary-container transition-colors enabled:hover:bg-surface-container-high disabled:bg-surface-container-highest disabled:text-on-surface-variant"
    >
      {count}
      {count > 0 && <Icon name={open ? 'expand_less' : 'expand_more'} className="text-[16px]" />}
    </button>
  )
}

// Açılan satır: patent başlıkları; başlığa tıklayınca /patents/{id} (liste sayfası + düzenleme çekmecesi).
export function PatentsRow({ colSpan, patents, onOpen }: { colSpan: number; patents: { id: number; title: string }[]; onOpen: (id: number) => void }) {
  return (
    <tr className="bg-surface-container-low">
      <td colSpan={colSpan} className="px-space-md py-space-sm">
        <ul className="flex flex-col gap-1">
          {patents.map((patent) => (
            <li key={patent.id}>
              <button type="button" onClick={() => onOpen(patent.id)} className="text-left font-body-md text-body-md text-primary hover:underline">
                {patent.title}
              </button>
            </li>
          ))}
        </ul>
      </td>
    </tr>
  )
}
