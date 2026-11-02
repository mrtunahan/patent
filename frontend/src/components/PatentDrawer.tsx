import { useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { createPatent, getPatent, removePatent, updatePatent } from '../api/patents'
import { createApplicant, createAttorneyFirm, createDepartment, createFsmhType } from '../api/lookups'
import { statusStyle } from '../lib/format'
import { PATENT_STATUSES, type PatentIn, type PatentStatus } from '../api/types'
import { useLookups } from '../lib/lookups'
import ConfirmDialog from './ConfirmDialog'
import DrawerShell from './DrawerShell'
import { Field, controlClass, labelClass } from './formStyles'
import LookupField from './LookupField'
import PartnerInput from './PartnerInput'

interface Props {
  mode: 'new' | number
  onClose: () => void
  onSaved: (message: string) => void
  onNotFound: () => void
}

interface FormState {
  title: string
  applicantId: string
  departmentId: string
  fsmhTypeId: string
  attorneyFirmId: string
  partners: string[]
  applicationDate: string
  registrationDate: string
  status: string
  notes: string
}

const EMPTY: FormState = {
  title: '', applicantId: '', departmentId: '', fsmhTypeId: '', attorneyFirmId: '', partners: [], applicationDate: '', registrationDate: '', status: '', notes: '',
}

// Tarih kutusu yıl yazılırken ara değerler üretir; yalnızca tam ve makul tarih (YYYY-MM-DD, >= 1900) gönderilir.
const fullDate = (value: string) => (/^\d{4}-\d{2}-\d{2}$/.test(value) && value >= '1900-01-01' ? value : null)

export default function PatentDrawer({ mode, onClose, onSaved, onNotFound }: Props) {
  const isNew = mode === 'new'
  const { lookups, reload } = useLookups()
  const [form, setForm] = useState<FormState>(EMPTY)
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [duplicateIds, setDuplicateIds] = useState<number[] | null>(null)

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((prev) => ({ ...prev, [key]: value }))

  // Düzenleme: kayıt GET /api/patents/{id} ile yüklenir
  useEffect(() => {
    if (isNew) return
    const controller = new AbortController()
    setLoading(true)
    setError('')
    getPatent(mode, controller.signal)
      .then((patent) => {
        setForm({
          title: patent.title,
          applicantId: String(patent.applicant.id),
          departmentId: patent.department ? String(patent.department.id) : '',
          fsmhTypeId: String(patent.fsmh_type.id),
          attorneyFirmId: patent.attorney_firm ? String(patent.attorney_firm.id) : '',
          partners: patent.partners,
          applicationDate: patent.application_date ?? '',
          registrationDate: patent.registration_date ?? '',
          status: patent.status ?? '',
          notes: patent.notes ?? '',
        })
        setLoading(false)
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === 'AbortError') return
        if (err instanceof ApiError && err.status === 404) {
          onNotFound()
          return
        }
        setError(err instanceof ApiError ? err.detail : 'Kayıt yüklenemedi.')
        setLoading(false)
      })
    return () => controller.abort()
  }, [isNew, mode, onNotFound])

  // Kaydı oluşturur, ortak lookup listesini yeniler; yeni id'yi döner (hata çağırana, mini satıra gider).
  const create = async (post: () => Promise<{ id: number }>) => {
    const { id } = await post()
    await reload()
    return id
  }

  const buildPayload = (): PatentIn => ({
    title: form.title.trim(),
    applicant_id: Number(form.applicantId),
    fsmh_type_id: Number(form.fsmhTypeId),
    department_id: form.departmentId ? Number(form.departmentId) : null,
    attorney_firm_id: form.attorneyFirmId ? Number(form.attorneyFirmId) : null,
    application_date: fullDate(form.applicationDate),
    registration_date: fullDate(form.registrationDate),
    status: (form.status || null) as PatentStatus | null,
    notes: form.notes.trim() || null,
    partners: form.partners,
  })

  const save = async (confirmDuplicate = false) => {
    const required: Record<string, string> = {}
    if (!form.title.trim()) required.title = 'Bu alan zorunludur.'
    if (!form.applicantId) required.applicant_id = 'Bu alan zorunludur.'
    if (!form.fsmhTypeId) required.fsmh_type_id = 'Bu alan zorunludur.'
    if (Object.keys(required).length) {
      setFieldErrors(required)
      setError('Zorunlu alanları doldurun.')
      return
    }
    setSaving(true)
    setError('')
    setFieldErrors({})
    try {
      if (isNew) await createPatent(buildPayload(), confirmDuplicate)
      else await updatePatent(mode, buildPayload(), confirmDuplicate)
      onSaved(isNew ? 'Kayıt eklendi.' : 'Kayıt güncellendi.')
    } catch (err) {
      if (err instanceof ApiError && err.duplicate) {
        setDuplicateIds(err.existingIds)
      } else if (err instanceof ApiError) {
        setError(err.detail)
        setFieldErrors(err.fieldErrors)
      } else {
        setError('Beklenmeyen bir hata oluştu.')
      }
      setSaving(false)
    }
  }

  const remove = async () => {
    if (isNew) return
    setSaving(true)
    setError('')
    try {
      await removePatent(mode)
      onSaved('Kayıt silindi.')
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        onNotFound()
        return
      }
      setError(err instanceof ApiError ? err.detail : 'Silinemedi.')
      setSaving(false)
    }
  }

  const busy = saving || loading
  return (
    <>
      <DrawerShell
        title={isNew ? 'Yeni Patent Ekle' : 'Patent Düzenle'}
        subtitle="Patent / FSMH kaydı"
        isNew={isNew}
        loading={loading}
        saving={saving}
        error={error}
        formId="patentForm"
        escDisabled={duplicateIds !== null}
        onClose={onClose}
        onSubmit={() => void save()}
        onDelete={() => void remove()}
      >
        <Field id="formTitle" text="1. Buluş Başlığı *" error={fieldErrors.title}>
          <textarea id="formTitle" rows={2} value={form.title} maxLength={500} disabled={busy} onChange={(e) => set('title', e.target.value)} className={`w-full p-space-sm ${controlClass}`} />
        </Field>
        <div className="grid grid-cols-1 gap-space-md md:grid-cols-2">
          <LookupField
            id="formApplicant"
            text="2. Başvuru Sahibi *"
            value={form.applicantId}
            options={(lookups?.applicants ?? []).map((a) => ({ id: a.id, label: a.full_name + (a.is_active ? '' : ' (pasif)') }))}
            emptyLabel="Seçiniz"
            disabled={busy}
            error={fieldErrors.applicant_id}
            addedMessage="Başvuru sahibi eklendi."
            onChange={(value) => {
              // Bölüm boşsa seçilen kişinin bölümü gelir; kullanıcı değiştirebilir.
              const defaultDepartment = lookups?.applicants.find((a) => String(a.id) === value)?.department_id
              setForm((prev) => ({ ...prev, applicantId: value, departmentId: prev.departmentId || (defaultDepartment ? String(defaultDepartment) : '') }))
            }}
            onCreate={(name) => create(() => createApplicant({ full_name: name }))}
          />
          <LookupField
            id="formDepartment"
            text="3. Bölüm / Birim"
            value={form.departmentId}
            options={(lookups?.departments ?? []).map((d) => ({ id: d.id, label: d.name }))}
            emptyLabel="Seçiniz"
            disabled={busy}
            error={fieldErrors.department_id}
            addedMessage="Bölüm eklendi."
            onChange={(value) => set('departmentId', value)}
            onCreate={(name) => create(() => createDepartment({ name }))}
          />
        </div>
        <div className="grid grid-cols-1 gap-space-md md:grid-cols-2">
          <LookupField
            id="formType"
            text="4. FSMH Türü *"
            value={form.fsmhTypeId}
            options={(lookups?.fsmhTypes ?? []).map((t) => ({ id: t.id, label: t.name }))}
            emptyLabel="Seçiniz"
            disabled={busy}
            error={fieldErrors.fsmh_type_id}
            addedMessage="FSMH türü eklendi."
            onChange={(value) => set('fsmhTypeId', value)}
            onCreate={(name) =>
              create(() => createFsmhType({ name, sort_order: Math.max(0, ...(lookups?.fsmhTypes ?? []).map((t) => t.sort_order)) + 1 }))
            }
          />
          <LookupField
            id="formAgentFirm"
            text="5. Vekil Firma"
            value={form.attorneyFirmId}
            options={(lookups?.attorneyFirms ?? []).map((f) => ({ id: f.id, label: f.name + (f.is_active ? '' : ' (pasif)') }))}
            emptyLabel="Seçiniz"
            disabled={busy}
            error={fieldErrors.attorney_firm_id}
            addedMessage="Vekil firma eklendi."
            onChange={(value) => set('attorneyFirmId', value)}
            onCreate={(name) => create(() => createAttorneyFirm({ name }))}
          />
        </div>
        <div className="flex flex-col gap-space-xs">
          <label htmlFor="formPartners" className={labelClass}>
            6. Ortaklar &amp; Oranları
          </label>
          <PartnerInput value={form.partners} onChange={(v) => set('partners', v)} disabled={busy} error={fieldErrors.partners} />
        </div>
        <div className="grid grid-cols-1 gap-space-md md:grid-cols-2">
          <Field id="formApplicationDate" text="7. Başvuru Tarihi" error={fieldErrors.application_date}>
            <input id="formApplicationDate" type="date" value={form.applicationDate} disabled={busy} onChange={(e) => set('applicationDate', e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
          </Field>
          <Field id="formRegistrationDate" text="Tescil Tarihi" error={fieldErrors.registration_date}>
            <input id="formRegistrationDate" type="date" value={form.registrationDate} disabled={busy} onChange={(e) => set('registrationDate', e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
          </Field>
        </div>
        <div className="flex flex-col gap-space-xs">
          <span id="formStatusLabel" className={labelClass}>
            8. Durum
          </span>
          <div role="radiogroup" aria-labelledby="formStatusLabel" className="flex flex-wrap gap-space-sm">
            {PATENT_STATUSES.map((status) => {
              const selected = form.status === status
              return (
                <button
                  key={status}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  disabled={busy}
                  onClick={() => set('status', selected ? '' : status)} // seçiliye tekrar tıklamak seçimi kaldırır
                  className={`h-10 rounded-lg border px-space-md font-label-lg text-label-lg font-semibold transition-colors disabled:opacity-60 ${
                    selected ? `border-transparent ${statusStyle(status)}` : 'border-outline-variant bg-surface-container-lowest text-on-surface-variant hover:bg-surface-bright'
                  }`}
                >
                  {status}
                </button>
              )
            })}
          </div>
          {fieldErrors.status && <span className="font-label-sm text-label-sm text-error">{fieldErrors.status}</span>}
        </div>
        <Field id="formNotes" text="9. Notlar / Açıklama" error={fieldErrors.notes}>
          <textarea id="formNotes" rows={3} value={form.notes} disabled={busy} onChange={(e) => set('notes', e.target.value)} className={`w-full p-space-sm ${controlClass}`} />
        </Field>
      </DrawerShell>

      <ConfirmDialog
        open={duplicateIds !== null}
        title="Mükerrer kayıt uyarısı"
        message={`Aynı başlık, başvuru sahibi ve tarihle kayıt var (kayıt no: ${duplicateIds?.join(', ') ?? ''}). Yine de kaydedilsin mi?`}
        confirmLabel="Yine de kaydet"
        onCancel={() => {
          setDuplicateIds(null)
          setSaving(false)
        }}
        onConfirm={() => {
          setDuplicateIds(null)
          void save(true)
        }}
      />
    </>
  )
}
