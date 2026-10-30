import { useState } from 'react'
import { createAttorneyFirm, listAttorneyFirms, removeAttorneyFirm, updateAttorneyFirm } from '../api/lookups'
import type { AttorneyFirmRead } from '../api/types'
import ConfirmDialog from '../components/ConfirmDialog'
import DrawerShell from '../components/DrawerShell'
import { Field, controlClass } from '../components/formStyles'
import { PageHeader, RowActions, SearchCard, StatusPill, TableCard, cell } from '../components/ListPage'
import { useToast } from '../components/Toast'
import { describeError, matchesQuery, useList, useRowDelete } from '../lib/hooks'

function FirmDrawer({ record, onClose, onSaved, onDeleteFailed }: { record: AttorneyFirmRead | null; onClose: () => void; onSaved: (message: string) => void; onDeleteFailed: (message: string) => void }) {
  const [name, setName] = useState(record?.name ?? '')
  const [contact, setContact] = useState(record?.contact_info ?? '')
  const [active, setActive] = useState(record?.is_active ?? true)
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
      const body = { name: name.trim(), contact_info: contact.trim() || null, is_active: active }
      if (record) await updateAttorneyFirm(record.id, body)
      else await createAttorneyFirm(body)
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
      await removeAttorneyFirm(record.id)
      onSaved('Kayıt silindi.')
    } catch (err) {
      onDeleteFailed(describeError(err).notFound ? 'Kayıt bulunamadı.' : describeError(err).message)
    }
  }

  return (
    <DrawerShell title={record ? 'Vekil Firma Düzenle' : 'Yeni Vekil Firma'} subtitle="Vekil firma kaydı" icon="business_center" isNew={!record} saving={saving} error={error} formId="firmForm" onClose={onClose} onSubmit={() => void save()} onDelete={() => void remove()}>
      <Field id="firmName" text="Firma Adı *" error={fieldErrors.name}>
        <input id="firmName" type="text" value={name} maxLength={200} disabled={saving} onChange={(e) => setName(e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
      </Field>
      <Field id="firmContact" text="İletişim Bilgisi" error={fieldErrors.contact_info}>
        <textarea id="firmContact" rows={3} value={contact} disabled={saving} onChange={(e) => setContact(e.target.value)} className={`w-full p-space-sm ${controlClass}`} />
      </Field>
      <label className="flex items-center gap-space-sm font-label-lg text-label-lg font-semibold text-on-surface">
        <input type="checkbox" checked={active} disabled={saving} onChange={(e) => setActive(e.target.checked)} className="h-4 w-4 accent-primary" />
        Aktif
      </label>
    </DrawerShell>
  )
}

export default function AttorneyFirms() {
  const toast = useToast()
  const list = useList(listAttorneyFirms)
  const [q, setQ] = useState('')
  const [drawer, setDrawer] = useState<null | 'new' | AttorneyFirmRead>(null)
  const del = useRowDelete<AttorneyFirmRead>(removeAttorneyFirm, list.reload)

  const visible = (list.items ?? []).filter((f) => matchesQuery(q, f.name, f.contact_info))
  const finish = (message: string) => {
    toast(message)
    setDrawer(null)
    list.reload()
  }

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <PageHeader crumb="Vekil Firmalar" title="Vekil Firmalar" subtitle="Patent / FSMH başvurularında görev alan vekil firmalar" addLabel="Yeni Vekil Firma Ekle" onAdd={() => setDrawer('new')} />
      <SearchCard value={q} onChange={setQ} placeholder="Firma adı veya iletişim bilgisi ara..." count={list.status === 'ready' ? visible.length : null} />
      <TableCard
        title="Vekil Firma Listesi"
        icon="business_center"
        status={list.status}
        errorMessage={list.errorMessage}
        isEmpty={visible.length === 0}
        colSpan={5}
        minWidth="760px"
        onRetry={list.reload}
        head={
          <>
            <th className={`${cell} w-[80px]`}>No</th>
            <th className={`${cell} w-[240px]`}>Firma Adı</th>
            <th className={cell}>İletişim Bilgisi</th>
            <th className={`${cell} w-[120px]`}>Durum</th>
            <th className={`${cell} w-[110px] text-center`}>İşlemler</th>
          </>
        }
      >
        {visible.map((f, index) => (
          <tr key={f.id} onClick={() => setDrawer(f)} className={`cursor-pointer transition-colors hover:bg-surface-bright ${index % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface'}`}>
            <td className={`${cell} font-label-md text-label-md text-on-surface-variant`}>{index + 1}</td>
            <td className={`${cell} font-medium text-on-surface`}>{f.name}</td>
            <td className={`${cell} max-w-xs truncate text-on-surface-variant`} title={f.contact_info ?? undefined}>
              {f.contact_info || '-'}
            </td>
            <td className={cell}>
              <StatusPill active={f.is_active} />
            </td>
            <td className={cell}>
              <RowActions onEdit={() => setDrawer(f)} onDelete={() => del.setTarget(f)} />
            </td>
          </tr>
        ))}
      </TableCard>

      {drawer && (
        <FirmDrawer
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
