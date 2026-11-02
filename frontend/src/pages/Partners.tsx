import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listPartners } from '../api/lookups'
import type { PartnerSummary } from '../api/types'
import { CountToggle, PageHeader, SearchCard, TableCard, cell } from '../components/ListPage'
import SummaryDrawer from '../components/SummaryDrawer'
import { matchesQuery, useList } from '../lib/hooks'

export default function Partners() {
  const navigate = useNavigate()
  const list = useList(listPartners)
  const [panel, setPanel] = useState<PartnerSummary | null>(null)
  const [q, setQ] = useState('')
  const visible = (list.items ?? []).filter((p) => matchesQuery(q, p.name))

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <PageHeader crumb="Ortaklar" title="Ortaklar" subtitle="Ortaklar patent kayıtlarından derlenir." />
      <SearchCard value={q} onChange={setQ} placeholder="Ortak kurum ara..." count={list.status === 'ready' ? visible.length : null} />
      <TableCard
        title="Ortak Kurum Listesi"
        icon="handshake"
        status={list.status}
        errorMessage={list.errorMessage}
        isEmpty={visible.length === 0}
        colSpan={3}
        minWidth="520px"
        onRetry={list.reload}
        head={
          <>
            <th className={`${cell} w-[80px]`}>No</th>
            <th className={cell}>Ortak Kurum</th>
            <th className={`${cell} w-[140px]`}>Patent Sayısı</th>
          </>
        }
      >
        {visible.map((p, index) => (
          <tr key={p.name} className={index % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface'}>
            <td className={`${cell} font-label-md text-label-md text-on-surface-variant`}>{index + 1}</td>
            <td className={`${cell} font-medium text-on-surface`}>{p.name}</td>
            <td className={cell}>
              <CountToggle count={p.patent_count} onClick={() => setPanel(p)} />
            </td>
          </tr>
        ))}
      </TableCard>
      {panel && <SummaryDrawer title={panel.name} patents={panel.patents} onClose={() => setPanel(null)} onOpenPatent={(id) => navigate(`/patents/${id}`)} />}
    </div>
  )
}
