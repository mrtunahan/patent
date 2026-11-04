import Icon from './Icon'

export function PageHeader({ crumb, title, subtitle, addLabel, onAdd }: { crumb: string; title: string; subtitle: string; addLabel?: string; onAdd?: () => void }) {
  return (
    <div className="flex flex-col justify-between gap-space-md lg:flex-row lg:items-center">
      <div className="flex flex-col">
        <div className="flex items-center gap-space-xs text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant lg:hidden">
          <span>TTO Otomasyonu</span>
          <Icon name="chevron_right" className="text-[14px]" />
          <span className="font-semibold text-primary">{crumb}</span>
        </div>
        <h1 className="mt-space-xs text-2xl font-semibold tracking-tight lg:mt-0 lg:text-3xl text-on-surface">{title}</h1>
        <p className="font-body-md text-body-md text-on-surface-variant">{subtitle}</p>
      </div>
      {addLabel && onAdd && (
        <button
          type="button"
          onClick={onAdd}
          className="flex h-10 items-center justify-center gap-space-xs self-start rounded-xl bg-surface px-space-lg font-label-lg text-label-lg font-semibold text-primary shadow-raised transition-all hover:shadow-raised-sm active:shadow-inset-sm lg:self-auto"
        >
          <Icon name="add_circle" className="text-[20px]" />
          {addLabel}
        </button>
      )}
    </div>
  )
}
