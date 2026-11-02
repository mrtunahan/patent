import { Fragment, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createDepartment, listDepartmentSummary, removeDepartment, updateDepartment } from '../api/lookups'
import type { IdName, LookupSummary } from '../api/types'
import ConfirmDialog from '../components/ConfirmDialog'
import DrawerShell from '../components/DrawerShell'
import { Field, controlClass } from '../components/formStyles'
import { CountToggle, PageHeader, PatentsRow, RowActions, SearchCard, TableCard, cell } from '../components/ListPage'
import { useToast } from '../components/Toast'
import { useLookups } from '../lib/lookups'
import { describeError, matchesQuery, useList, useRowDelete, useToggleSet } from '../lib/hooks'

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

export default function Departments() {
  const toast = useToast()
  const { reload: reloadLookups } = useLookups()
  const navigate = useNavigate()
  const list = useList(listDepartmentSummary)
  const expanded = useToggleSet()
  const [q, setQ] = useState('')
  const [drawer, setDrawer] = useState<null | 'new' | LookupSummary>(null)

  const visible = (list.items ?? []).filter((d) => matchesQuery(q, d.name))
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
      <SearchCard value={q} onChange={setQ} placeholder="Bölüm / birim ara..." count={list.status === 'ready' ? visible.length : null} />
      <TableCard
        title="Bölüm / Birim Listesi"
        icon="domain"
        status={list.status}
        errorMessage={list.errorMessage}
        isEmpty={visible.length === 0}
        colSpan={4}
        minWidth="560px"
        onRetry={list.reload}
        head={
          <>
            <th className={`${cell} w-[80px]`}>No</th>
            <th className={cell}>Bölüm / Birim Adı</th>
            <th className={`${cell} w-[140px]`}>Patent Sayısı</th>
            <th className={`${cell} w-[110px] text-center`}>İşlemler</th>
          </>
        }
      >
        {visible.map((d, index) => (
          <Fragment key={d.id}>
            <tr onClick={() => setDrawer(d)} className={`cursor-pointer transition-colors hover:bg-surface-bright ${index % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface'}`}>
              <td className={`${cell} font-label-md text-label-md text-on-surface-variant`}>{index + 1}</td>
              <td className={`${cell} font-medium text-on-surface`}>{d.name}</td>
              <td className={cell}>
                <CountToggle count={d.patent_count} open={expanded.open.has(d.id)} onToggle={() => expanded.toggle(d.id)} />
              </td>
              <td className={cell}>
                <RowActions onEdit={() => setDrawer(d)} onDelete={() => del.setTarget(d)} />
              </td>
            </tr>
            {expanded.open.has(d.id) && d.patent_count > 0 && <PatentsRow colSpan={4} patents={d.patents} onOpen={(id) => navigate(`/patents/${id}`)} />}
          </Fragment>
        ))}
      </TableCard>

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
