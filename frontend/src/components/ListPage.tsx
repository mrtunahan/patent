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
        <h1 className="mt-space-xs font-headline-lg text-headline-lg font-bold tracking-tight text-on-surface">{title}</h1>
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
