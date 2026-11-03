import { useMemo, useState } from 'react'
import { createAttorneyFirm, listAttorneyFirmSummary, listAttorneyFirms, removeAttorneyFirm, updateAttorneyFirm } from '../api/lookups'
import type { AttorneyFirmRead, PatentRef } from '../api/types'
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
  const [drawer, setDrawer] = useState<null | 'new' | AttorneyFirmRead>(null)

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
      <EntityListLayout
        title="Vekil Firma Listesi"
        icon="business_center"
        searchPlaceholder="Firma adı, vergi no veya e-posta ara..."
        items={list.items}
        status={list.status}
        errorMessage={list.errorMessage}
        onRetry={list.reload}
        rowKey={(f) => f.id}
        nameHeader="Firma"
        nameOf={(f) => f.name}
        searchTexts={(f) => [f.name, f.tax_no, f.email]}
        countOf={(f) => stats.get(f.id)?.patent_count ?? 0}
        patentsOf={(f) => stats.get(f.id)?.patents ?? []}
        monogramOf={(f) => wordInitials(f.name)}
        extraColumns={[
          { header: 'Vergi No', className: 'w-[130px]', render: (f) => f.tax_no || '-' },
          { header: 'E-posta', className: 'w-[200px]', render: (f) => f.email || '-' },
        ]}
        onSummary={(f) => setPanel({ name: f.name, kind: 'Vekil Firma', patents: stats.get(f.id)?.patents ?? [] })}
        onEdit={setDrawer}
        onDelete={del.setTarget}
      />

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
