import Icon from './Icon'

export const PAGE_SIZES = [10, 25, 50, 100]

interface Props {
  page: number
  pageSize: number
  total: number
  onPage: (page: number) => void
  onPageSize: (size: number) => void
}

// En fazla ~5 numara: geçerli sayfa etrafında pencere.
function pageNumbers(page: number, last: number): number[] {
  const size = Math.min(5, last)
  let start = Math.max(1, page - Math.floor(size / 2))
  start = Math.min(start, last - size + 1)
  return Array.from({ length: size }, (_, i) => start + i)
}

const navButton =
  'flex h-8 w-8 items-center justify-center rounded-lg bg-surface text-on-surface-variant shadow-raised-sm transition-all hover:text-primary disabled:cursor-not-allowed disabled:opacity-50'

export default function Pagination({ page, pageSize, total, onPage, onPageSize }: Props) {
  const last = Math.max(1, Math.ceil(total / pageSize))
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1
  const to = Math.min(page * pageSize, total)

  return (
    <div className="flex flex-col items-center justify-between gap-space-md bg-surface-container-low px-6 py-4 font-label-md text-label-md text-on-surface-variant sm:flex-row">
      <div className="flex flex-wrap items-center gap-space-sm">
        <span>Sayfa Başına Göster:</span>
        <select
          aria-label="Sayfa başına kayıt"
          value={pageSize}
          onChange={(event) => onPageSize(Number(event.target.value))}
          className="h-8 rounded-lg bg-surface px-space-sm font-semibold text-on-surface shadow-inset-sm focus:outline-none"
        >
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
        <span>
          Toplam <strong>{total}</strong> kayıttan {from}-{to} arası gösteriliyor
        </span>
      </div>
      <div className="flex items-center gap-space-xs">
        <button type="button" aria-label="Önceki sayfa" disabled={page <= 1} onClick={() => onPage(page - 1)} className={navButton}>
          <Icon name="chevron_left" className="text-[18px]" />
        </button>
        {pageNumbers(page, last).map((n) => (
          <button
            key={n}
            type="button"
            aria-current={n === page ? 'page' : undefined}
            onClick={() => onPage(n)}
            className={
              n === page
                ? 'flex h-8 w-8 items-center justify-center rounded-lg bg-surface font-semibold text-primary shadow-inset-sm'
                : navButton
            }
          >
            {n}
          </button>
        ))}
        <button type="button" aria-label="Sonraki sayfa" disabled={page >= last} onClick={() => onPage(page + 1)} className={navButton}>
          <Icon name="chevron_right" className="text-[18px]" />
        </button>
      </div>
    </div>
  )
}
