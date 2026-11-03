import { useState } from 'react'
import { listPartners } from '../api/lookups'
import type { PatentRef } from '../api/types'
import EntityListLayout from '../components/EntityListLayout'
import { PageHeader } from '../components/ListPage'
import { wordInitials } from '../lib/format'
import SummaryModal from '../components/SummaryModal'
import { useList } from '../lib/hooks'

interface Panel {
  name: string
  kind: string
  patents: PatentRef[]
}

export default function Partners() {
  const list = useList(listPartners)
  const [panel, setPanel] = useState<Panel | null>(null)

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <PageHeader crumb="Ortaklar" title="Ortaklar" subtitle="Ortaklar patent kayıtlarından derlenir." />
      <EntityListLayout
        title="Ortak Kurum Listesi"
        icon="handshake"
        searchPlaceholder="Ortak kurum ara..."
        items={list.items}
        status={list.status}
        errorMessage={list.errorMessage}
        onRetry={list.reload}
        rowKey={(p) => p.name}
        nameHeader="Ortak Kurum"
        nameOf={(p) => p.name}
        searchTexts={(p) => [p.name]}
        countOf={(p) => p.patent_count}
        patentsOf={(p) => p.patents}
        monogramOf={(p) => wordInitials(p.name)}
        onSummary={(p) => setPanel({ name: p.name, kind: 'Ortak Kurum', patents: p.patents })}
      />
      {panel && <SummaryModal name={panel.name} kind={panel.kind} patents={panel.patents} onClose={() => setPanel(null)} />}
    </div>
  )
}
