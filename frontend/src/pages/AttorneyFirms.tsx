import { useMemo, useState } from 'react'
import { createAttorneyFirm, listAttorneyFirmSummary, listAttorneyFirms, removeAttorneyFirm, updateAttorneyFirm } from '../api/lookups'
import type { AttorneyFirmRead, PatentRef } from '../api/types'
import ConfirmDialog from '../components/ConfirmDialog'
import DrawerShell from '../components/DrawerShell'
import { Field, controlClass } from '../components/formStyles'
import { CountToggle, PageHeader, RowActions, SearchCard, TableCard, cell } from '../components/ListPage'
import SummaryModal from '../components/SummaryModal'
import { useToast } from '../components/Toast'
import { useLookups } from '../lib/lookups'
import { describeError, matchesQuery, useList, useRowDelete } from '../lib/hooks'

function FirmDrawer({ record, onClose, onSaved, onDeleteFailed }: { record: AttorneyFirmRead | null; onClose: () => void; onSaved: (message: string) => void; onDeleteFailed: (message: string) => void }) {
  const [name, setName] = useState(record?.name ?? '')
  const [title, setTitle] = useState(record?.title ?? '')
  const [taxNo, setTaxNo] = useState(record?.tax_no ?? '')
  const [email, setEmail] = useState(record?.email ?? '')
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
      // arayüzde olmayan alanlar (iletişim bilgisi, aktiflik) mevcut değerleriyle geri gönderilir
      const body = {
        name: name.trim(),
        title: title.trim() || null,
        tax_no: taxNo.trim() || null,
        email: email.trim() || null,
        contact_info: record?.contact_info ?? null,
        is_active: record?.is_active ?? true,
      }
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
      <Field id="firmTitle" text="Unvan" error={fieldErrors.title}>
        <input id="firmTitle" type="text" value={title} maxLength={300} disabled={saving} onChange={(e) => setTitle(e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
      </Field>
      <div className="grid grid-cols-1 gap-space-md md:grid-cols-2">
        <Field id="firmTaxNo" text="Vergi No" error={fieldErrors.tax_no}>
          <input id="firmTaxNo" type="text" inputMode="numeric" value={taxNo} maxLength={11} disabled={saving} onChange={(e) => setTaxNo(e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
        </Field>
        <Field id="firmEmail" text="E-posta" error={fieldErrors.email}>
          <input id="firmEmail" type="text" value={email} maxLength={200} disabled={saving} onChange={(e) => setEmail(e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
        </Field>
      </div>
    </DrawerShell>
  )
}

interface Panel {
  name: string
  kind: string
  patents: PatentRef[]
}

export default function AttorneyFirms() {
  const toast = useToast()
  const { reload: reloadLookups } = useLookups()
  const firms = useList(listAttorneyFirms)
  const summary = useList(listAttorneyFirmSummary)
  const [panel, setPanel] = useState<Panel | null>(null)
  const list = { items: firms.items, status: firms.status === 'ready' && summary.status !== 'ready' ? summary.status : firms.status, errorMessage: firms.errorMessage || summary.errorMessage, reload: () => { firms.reload(); summary.reload() } }
  const stats = useMemo(() => new Map((summary.items ?? []).map((x) => [x.id, x])), [summary.items])
  const [q, setQ] = useState('')
  const [drawer, setDrawer] = useState<null | 'new' | AttorneyFirmRead>(null)

  const visible = (list.items ?? []).filter((f) => matchesQuery(q, f.name, f.tax_no, f.email))
  // ortak lookup listesi de yenilenir (filtre çubuğu ve patent çekmecesi yeni durumu görsün)
  const refresh = () => {
    list.reload()
    void reloadLookups().catch(() => {})
  }
  const del = useRowDelete<AttorneyFirmRead>(removeAttorneyFirm, refresh)
  const finish = (message: string) => {
    toast(message)
    setDrawer(null)
    refresh()
  }

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <PageHeader crumb="Vekil Firmalar" title="Vekil Firmalar" subtitle="Patent / FSMH başvurularında görev alan vekil firmalar" addLabel="Yeni Vekil Firma Ekle" onAdd={() => setDrawer('new')} />
      <SearchCard value={q} onChange={setQ} placeholder="Firma adı, vergi no veya e-posta ara..." count={list.status === 'ready' ? visible.length : null} />
      <TableCard
        title="Vekil Firma Listesi"
        icon="business_center"
        status={list.status}
        errorMessage={list.errorMessage}
        isEmpty={visible.length === 0}
        colSpan={6}
        minWidth="860px"
        onRetry={list.reload}
        head={
          <>
            <th className={`${cell} w-[80px]`}>No</th>
            <th className={cell}>Firma</th>
            <th className={`${cell} w-[130px]`}>Vergi No</th>
            <th className={`${cell} w-[200px]`}>E-posta</th>
            <th className={`${cell} w-[140px]`}>Patent Sayısı</th>
            <th className={`${cell} w-[110px] text-center`}>İşlemler</th>
          </>
        }
      >
        {visible.map((f, index) => {
          const stat = stats.get(f.id)
          const count = stat?.patent_count ?? 0
          return (
              <tr onClick={() => setDrawer(f)} className={`cursor-pointer transition-colors hover:bg-surface-bright ${index % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface'}`}>
                <td className={`${cell} font-label-md text-label-md text-on-surface-variant`}>{index + 1}</td>
                <td className={`${cell} font-medium text-on-surface`}>{f.name}</td>
                <td className={`${cell} text-on-surface-variant`}>{f.tax_no || '-'}</td>
                <td className={`${cell} text-on-surface-variant`}>{f.email || '-'}</td>
                <td className={cell}>
                  <CountToggle count={count} onClick={() => setPanel({ name: f.name, kind: 'Vekil Firma', patents: stat?.patents ?? [] })} />
                </td>
                <td className={cell}>
                  <RowActions onEdit={() => setDrawer(f)} onDelete={() => del.setTarget(f)} />
                </td>
              </tr>

          )
        })}
      </TableCard>

      {panel && <SummaryModal name={panel.name} kind={panel.kind} patents={panel.patents} onClose={() => setPanel(null)} />}
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
