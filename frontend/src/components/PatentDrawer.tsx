import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { ApiError } from '../api/client'
import { createPatent, getPatent, removePatent, updatePatent } from '../api/patents'
import type { Lookups, PatentIn } from '../api/types'
import ConfirmDialog from './ConfirmDialog'
import Icon from './Icon'
import PartnerInput from './PartnerInput'

interface Props {
  mode: 'new' | number
  lookups: Lookups | null
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
  notes: string
}

const EMPTY: FormState = {
  title: '', applicantId: '', departmentId: '', fsmhTypeId: '', attorneyFirmId: '', partners: [], applicationDate: '', notes: '',
}

const label = 'font-label-lg text-label-lg font-semibold text-on-surface'
const control =
  'rounded-lg bg-surface-container-lowest text-on-surface font-body-md text-body-md placeholder:text-on-surface-variant focus:bg-surface-bright focus:outline-none'

function Field({ id, text, error, children }: { id: string; text: string; error?: string; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-space-xs">
      <label htmlFor={id} className={label}>
        {text}
      </label>
      {children}
      {error && <span className="font-label-sm text-label-sm text-error">{error}</span>}
    </div>
  )
}

export default function PatentDrawer({ mode, lookups, onClose, onSaved, onNotFound }: Props) {
  const isNew = mode === 'new'
  const [form, setForm] = useState<FormState>(EMPTY)
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [visible, setVisible] = useState(false)
  const [duplicateIds, setDuplicateIds] = useState<number[] | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((prev) => ({ ...prev, [key]: value }))

  // Açılış animasyonu
  useEffect(() => {
    const frame = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(frame)
  }, [])

  const close = useCallback(() => {
    setVisible(false)
    window.setTimeout(onClose, 250)
  }, [onClose])

  // Esc kapatır (açık bir onay penceresi varsa o kapanır, çekmece değil)
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && duplicateIds === null && !confirmDelete) close()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [close, duplicateIds, confirmDelete])

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

  const buildPayload = (): PatentIn => ({
    title: form.title.trim(),
    applicant_id: Number(form.applicantId),
    fsmh_type_id: Number(form.fsmhTypeId),
    department_id: form.departmentId ? Number(form.departmentId) : null,
    attorney_firm_id: form.attorneyFirmId ? Number(form.attorneyFirmId) : null,
    application_date: form.applicationDate || null,
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
      setConfirmDelete(false)
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
      <div
        className={`fixed inset-0 z-50 bg-inverse-surface/40 backdrop-blur-[2px] transition-opacity duration-300 ${visible ? 'opacity-100' : 'opacity-0'}`}
        onClick={close}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={isNew ? 'Yeni Patent Ekle' : 'Patent Düzenle'}
        className={`fixed right-0 top-0 z-50 flex h-full w-full max-w-2xl flex-col justify-between overflow-hidden bg-surface-container-high shadow-2xl transition-transform duration-300 ease-out ${
          visible ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between bg-surface-container-highest p-space-lg">
          <div className="flex items-center gap-space-sm">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-on-primary">
              <Icon name="post_add" className="text-[22px]" />
            </div>
            <div className="flex flex-col">
              <h2 className="font-headline-sm text-headline-sm text-on-surface">{isNew ? 'Yeni Patent Ekle' : 'Patent Düzenle'}</h2>
              <span className="font-label-sm text-label-sm text-on-surface-variant">Patent / FSMH kaydı</span>
            </div>
          </div>
          <button
            type="button"
            onClick={close}
            aria-label="Kapat"
            className="flex h-9 w-9 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container"
          >
            <Icon name="close" className="text-[24px]" />
          </button>
        </div>

        <form
          id="patentForm"
          noValidate
          onSubmit={(event) => {
            event.preventDefault()
            void save()
          }}
          className="flex flex-1 flex-col gap-space-lg overflow-y-auto p-space-lg"
        >
          {error && (
            <div role="alert" className="flex items-start gap-space-sm rounded-lg bg-error-container p-space-sm font-body-md text-body-md text-on-error-container">
              <Icon name="error" className="mt-0.5 text-[20px]" />
              <span>{error}</span>
            </div>
          )}
          {loading ? (
            <p className="text-on-surface-variant">Yükleniyor...</p>
          ) : (
            <>
              <Field id="formTitle" text="1. Buluş Başlığı *" error={fieldErrors.title}>
                <textarea
                  id="formTitle"
                  rows={2}
                  value={form.title}
                  maxLength={500}
                  disabled={busy}
                  onChange={(e) => set('title', e.target.value)}
                  className={`w-full p-space-sm ${control}`}
                />
              </Field>
              <div className="grid grid-cols-1 gap-space-md md:grid-cols-2">
                <Field id="formApplicant" text="2. Başvuru Sahibi *" error={fieldErrors.applicant_id}>
                  <select id="formApplicant" value={form.applicantId} disabled={busy} onChange={(e) => set('applicantId', e.target.value)} className={`h-10 px-space-sm ${control}`}>
                    <option value="">Seçiniz</option>
                    {lookups?.applicants.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.full_name}
                        {a.is_active ? '' : ' (pasif)'}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field id="formDepartment" text="3. Bölüm / Birim" error={fieldErrors.department_id}>
                  <select id="formDepartment" value={form.departmentId} disabled={busy} onChange={(e) => set('departmentId', e.target.value)} className={`h-10 px-space-sm ${control}`}>
                    <option value="">-</option>
                    {lookups?.departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              <div className="grid grid-cols-1 gap-space-md md:grid-cols-2">
                <Field id="formType" text="4. FSMH Türü *" error={fieldErrors.fsmh_type_id}>
                  <select id="formType" value={form.fsmhTypeId} disabled={busy} onChange={(e) => set('fsmhTypeId', e.target.value)} className={`h-10 px-space-sm ${control}`}>
                    <option value="">Seçiniz</option>
                    {lookups?.fsmhTypes.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field id="formAgentFirm" text="5. Vekil Firma" error={fieldErrors.attorney_firm_id}>
                  <select id="formAgentFirm" value={form.attorneyFirmId} disabled={busy} onChange={(e) => set('attorneyFirmId', e.target.value)} className={`h-10 px-space-sm ${control}`}>
                    <option value="">-</option>
                    {lookups?.attorneyFirms.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.name}
                        {f.is_active ? '' : ' (pasif)'}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              <div className="flex flex-col gap-space-xs">
                <label htmlFor="formPartners" className={label}>
                  6. Ortaklar &amp; Oranları
                </label>
                <PartnerInput value={form.partners} onChange={(v) => set('partners', v)} disabled={busy} error={fieldErrors.partners} />
              </div>
              <Field id="formApplicationDate" text="7. Başvuru Tarihi" error={fieldErrors.application_date}>
                <input id="formApplicationDate" type="date" value={form.applicationDate} disabled={busy} onChange={(e) => set('applicationDate', e.target.value)} className={`h-10 px-space-sm md:max-w-xs ${control}`} />
              </Field>
              <Field id="formNotes" text="8. Notlar / Açıklama" error={fieldErrors.notes}>
                <textarea id="formNotes" rows={3} value={form.notes} disabled={busy} onChange={(e) => set('notes', e.target.value)} className={`w-full p-space-sm ${control}`} />
              </Field>
            </>
          )}
        </form>

        <div className="flex items-center justify-between gap-space-sm bg-surface-container-highest p-space-lg">
          <div className="flex items-center gap-space-sm">
            <button type="button" onClick={close} disabled={saving} className="h-10 rounded-lg bg-surface-container px-space-md font-label-lg text-label-lg text-on-surface transition-colors hover:bg-surface-container-lowest disabled:opacity-50">
              Vazgeç
            </button>
            {!isNew && (
              <button type="button" onClick={() => setConfirmDelete(true)} disabled={busy} className="flex h-10 items-center gap-space-xs rounded-lg px-space-md font-label-lg text-label-lg text-error transition-colors hover:bg-error-container disabled:opacity-50">
                <Icon name="delete" className="text-[18px]" />
                Sil
              </button>
            )}
          </div>
          <button type="submit" form="patentForm" disabled={busy} className="flex h-10 items-center gap-space-xs rounded-lg bg-primary px-space-lg font-label-lg text-label-lg text-on-primary shadow-md transition-all hover:bg-primary/95 disabled:opacity-60">
            <Icon name="check" className="text-[18px]" />
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
        </div>
      </div>

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
      <ConfirmDialog
        open={confirmDelete}
        message="Bu kayıt silinsin mi?"
        confirmLabel="Sil"
        tone="danger"
        busy={saving}
        onCancel={() => setConfirmDelete(false)}
        onConfirm={() => void remove()}
      />
    </>
  )
}
