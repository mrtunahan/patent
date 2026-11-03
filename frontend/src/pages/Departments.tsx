import { useState } from 'react'
import { createDepartment, listDepartmentSummary, removeDepartment, updateDepartment } from '../api/lookups'
import type { IdName, LookupSummary, PatentRef } from '../api/types'
import ConfirmDialog from '../components/ConfirmDialog'
import DrawerShell from '../components/DrawerShell'
import { Field, controlClass } from '../components/formStyles'
import EntityListLayout from '../components/EntityListLayout'
import { PageHeader } from '../components/ListPage'
import { wordInitials } from '../lib/format'
import SummaryModal from '../components/SummaryModal'
import { useToast } from '../components/Toast'
import { useLookups } from '../lib/lookups'
import { describeError, useList, useRowDelete } from '../lib/hooks'

function DepartmentDrawer({ record, onClose, onSaved, onDeleteFailed }: { record: IdName | null; onClose: () => void; onSaved: (message: string) => void; onDeleteFailed: (message: string) => void }) {
  const [name, setName] = useState(record?.name ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const save = async () => {
    if (!name.trim()) {
      setFieldErrors({ name: 'Bu alan zorunludur.' })
      setError('Zorunlu alanları doldurun.')
      return
    }
    setSaving(true)
    setError('')
    setFieldErrors({})
    try {
      const body = { name: name.trim() }
      if (record) await updateDepartment(record.id, body)
      else await createDepartment(body)
      onSaved(record ? 'Kayıt güncellendi.' : 'Kayıt eklendi.')
    } catch (err) {
      const info = describeError(err)
      setError(info.message)
      setFieldErrors(info.fieldErrors)
      setSaving(false)
    }
  }

  const remove = async () => {
    if (!record) return
    setSaving(true)
    try {
      await removeDepartment(record.id)
      onSaved('Kayıt silindi.')
    } catch (err) {
      onDeleteFailed(describeError(err).notFound ? 'Kayıt bulunamadı.' : describeError(err).message)
    }
  }

  return (
    <DrawerShell title={record ? 'Bölüm / Birim Düzenle' : 'Yeni Bölüm / Birim'} subtitle="Bölüm / birim kaydı" icon="domain" isNew={!record} saving={saving} error={error} formId="departmentForm" onClose={onClose} onSubmit={() => void save()} onDelete={() => void remove()}>
      <Field id="departmentName" text="Bölüm / Birim Adı *" error={fieldErrors.name}>
        <input id="departmentName" type="text" value={name} maxLength={200} disabled={saving} onChange={(e) => setName(e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
      </Field>
    </DrawerShell>
  )
}

interface Panel {
  name: string
  kind: string
  patents: PatentRef[]
}

export default function Departments() {
  const toast = useToast()
  const { reload: reloadLookups } = useLookups()
  const list = useList(listDepartmentSummary)
  const [panel, setPanel] = useState<Panel | null>(null)
  const [drawer, setDrawer] = useState<null | 'new' | LookupSummary>(null)

  // ortak lookup listesi de yenilenir (filtre çubuğu ve patent çekmecesi yeni durumu görsün)
  const refresh = () => {
    list.reload()
    void reloadLookups().catch(() => {})
  }
  const del = useRowDelete<LookupSummary>(removeDepartment, refresh)
  const finish = (message: string) => {
    toast(message)
    setDrawer(null)
    refresh()
  }

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <PageHeader crumb="Bölümler" title="Bölümler / Birimler" subtitle="Patent kayıtlarında kullanılan bölüm ve birimler" addLabel="Yeni Bölüm Ekle" onAdd={() => setDrawer('new')} />
      <EntityListLayout
        title="Bölüm / Birim Listesi"
        icon="domain"
        searchPlaceholder="Bölüm / birim ara..."
        items={list.items}
        status={list.status}
        errorMessage={list.errorMessage}
        onRetry={list.reload}
        rowKey={(d) => d.id}
        nameHeader="Bölüm / Birim Adı"
        nameOf={(d) => d.name}
        searchTexts={(d) => [d.name]}
        countOf={(d) => d.patent_count}
        patentsOf={(d) => d.patents}
        monogramOf={(d) => wordInitials(d.name)}
        onSummary={(d) => setPanel({ name: d.name, kind: 'Bölüm / Birim', patents: d.patents })}
        onEdit={setDrawer}
        onDelete={del.setTarget}
      />

      {panel && <SummaryModal name={panel.name} kind={panel.kind} patents={panel.patents} onClose={() => setPanel(null)} />}
      {drawer && (
        <DepartmentDrawer
          key={drawer === 'new' ? 'new' : drawer.id}
          record={drawer === 'new' ? null : drawer}
          onClose={() => setDrawer(null)}
          onSaved={finish}
          onDeleteFailed={finish}
        />
      )}
      <ConfirmDialog open={del.target !== null} message="Bu kayıt silinsin mi?" confirmLabel="Sil" tone="danger" busy={del.busy} onCancel={() => del.setTarget(null)} onConfirm={() => void del.confirm()} />
    </div>
  )
}
