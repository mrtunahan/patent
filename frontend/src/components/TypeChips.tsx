import type { PatentRef } from '../api/types'
import { typeStyle } from '../lib/format'

const MAX_CHIPS = 3

// Özet uçlarındaki patents[] listesinden türe göre sayım (çok olan önce, eşitlikte Türkçe ada göre).
export function countByType(patents: PatentRef[]): { name: string; count: number }[] {
  const counts = new Map<string, number>()
  for (const p of patents) counts.set(p.fsmh_type_name, (counts.get(p.fsmh_type_name) ?? 0) + 1)
  return [...counts].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'tr'))
}

// Tür Dağılımı hücresi: en fazla 3 küçük chip + "+K", altında segmentli oran çubuğu.
export default function TypeChips({ patents }: { patents: PatentRef[] }) {
  const types = countByType(patents)
  if (types.length === 0) return <span className="text-on-surface-variant">-</span>
  const shown = types.slice(0, MAX_CHIPS)
  const rest = types.length - shown.length
  return (
    <div className="flex min-w-[160px] flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-1">
        {shown.map((t) => (
          <span key={t.name} className={`rounded-full px-space-sm py-0.5 font-label-sm text-label-sm font-semibold ${typeStyle(t.name).pill}`}>
            {t.count} {t.name}
          </span>
        ))}
        {rest > 0 && <span className="font-label-sm text-label-sm font-semibold text-on-surface-variant">+{rest}</span>}
      </div>
      <div className="flex h-1 w-full overflow-hidden rounded-full bg-surface-container-high" aria-hidden>
        {types.map((t) => (
          <span key={t.name} className={typeStyle(t.name).dot} style={{ width: `${(t.count / patents.length) * 100}%` }} />
        ))}
      </div>
    </div>
  )
}
