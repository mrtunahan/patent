import { useMemo, useState } from 'react'
import { createApplicant, listApplicants, listDepartments, removeApplicant, updateApplicant } from '../api/lookups'
import type { ApplicantRead, DepartmentRead } from '../api/types'
import ConfirmDialog from '../components/ConfirmDialog'
import DrawerShell from '../components/DrawerShell'
import { Field, controlClass } from '../components/formStyles'
import { PageHeader, RowActions, SearchCard, StatusPill, TableCard, cell } from '../components/ListPage'
import { useToast } from '../components/Toast'
import { describeError, matchesQuery, useList, useRowDelete } from '../lib/hooks'

function ApplicantDrawer({ record, departments, onClose, onSaved, onDeleteFailed }: { record: ApplicantRead | null; departments: DepartmentRead[]; onClose: () => void; onSaved: (message: string) => void; onDeleteFailed: (message: string) => void }) {
  const [name, setName] = useState(record?.full_name ?? '')
  const [departmentId, setDepartmentId] = useState(record?.department_id ? String(record.department_id) : '')
  const [email, setEmail] = useState(record?.email ?? '')
  const [active, setActive] = useState(record?.is_active ?? true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const save = async () => {
    if (!name.trim()) {
      setFieldErrors({ full_name: 'Bu alan zorunludur.' })
      setError('Zorunlu alanları doldurun.')
      return
    }
    setSaving(true)
    setError('')
    setFieldErrors({})
    try {
      const body = {
        full_name: name.trim(),
        department_id: departmentId ? Number(departmentId) : null,
        email: email.trim() || null,
        is_active: active,
      }
      if (record) await updateApplicant(record.id, body)
      else await createApplicant(body)
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
      await removeApplicant(record.id)
      onSaved('Kayıt silindi.')
    } catch (err) {
      onDeleteFailed(describeError(err).notFound ? 'Kayıt bulunamadı.' : describeError(err).message)
    }
  }

  return (
    <DrawerShell title={record ? 'Başvuru Sahibi Düzenle' : 'Yeni Başvuru Sahibi'} subtitle="Başvuru sahibi kaydı" icon="person" isNew={!record} saving={saving} error={error} formId="applicantForm" onClose={onClose} onSubmit={() => void save()} onDelete={() => void remove()}>
      <Field id="applicantName" text="Ad Soyad *" error={fieldErrors.full_name}>
        <input id="applicantName" type="text" value={name} maxLength={200} disabled={saving} onChange={(e) => setName(e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
      </Field>
      <Field id="applicantDepartment" text="Varsayılan Bölüm" error={fieldErrors.department_id}>
        <select id="applicantDepartment" value={departmentId} disabled={saving} onChange={(e) => setDepartmentId(e.target.value)} className={`h-10 px-space-sm ${controlClass}`}>
          <option value="">-</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </Field>
      <Field id="applicantEmail" text="E-posta" error={fieldErrors.email}>
        <input id="applicantEmail" type="text" value={email} maxLength={200} disabled={saving} onChange={(e) => setEmail(e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
      </Field>
      <label className="flex items-center gap-space-sm font-label-lg text-label-lg font-semibold text-on-surface">
        <input type="checkbox" checked={active} disabled={saving} onChange={(e) => setActive(e.target.checked)} className="h-4 w-4 accent-primary" />
        Aktif
      </label>
    </DrawerShell>
  )
}

export default function Applicants() {
  const toast = useToast()
  const list = useList(listApplicants)
  const departments = useList(listDepartments)
  const [q, setQ] = useState('')
  const [drawer, setDrawer] = useState<null | 'new' | ApplicantRead>(null)
  const del = useRowDelete<ApplicantRead>(removeApplicant, list.reload)

  const departmentName = useMemo(() => new Map((departments.items ?? []).map((d) => [d.id, d.name])), [departments.items])
  const nameOf = (a: ApplicantRead) => (a.department_id ? departmentName.get(a.department_id) ?? '' : '')
  const visible = (list.items ?? []).filter((a) => matchesQuery(q, a.full_name, nameOf(a), a.email))
  const finish = (message: string) => {
    toast(message)
    setDrawer(null)
    list.reload()
  }

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <PageHeader crumb="Başvuru Sahipleri" title="Başvuru Sahipleri" subtitle="Patent / FSMH başvurularının sahipleri" addLabel="Yeni Başvuru Sahibi Ekle" onAdd={() => setDrawer('new')} />
      <SearchCard value={q} onChange={setQ} placeholder="Ad, bölüm veya e-posta ara..." count={list.status === 'ready' ? visible.length : null} />
      <TableCard
        title="Başvuru Sahibi Listesi"
        icon="person"
        status={list.status}
        errorMessage={list.errorMessage}
        isEmpty={visible.length === 0}
        colSpan={6}
        minWidth="860px"
        onRetry={list.reload}
        head={
          <>
            <th className={`${cell} w-[80px]`}>No</th>
            <th className={`${cell} w-[240px]`}>Ad Soyad</th>
            <th className={`${cell} w-[220px]`}>Varsayılan Bölüm</th>
            <th className={cell}>E-posta</th>
            <th className={`${cell} w-[120px]`}>Durum</th>
            <th className={`${cell} w-[110px] text-center`}>İşlemler</th>
          </>
        }
      >
        {visible.map((a, index) => (
          <tr key={a.id} onClick={() => setDrawer(a)} className={`cursor-pointer transition-colors hover:bg-surface-bright ${index % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface'}`}>
            <td className={`${cell} font-label-md text-label-md text-on-surface-variant`}>{index + 1}</td>
            <td className={`${cell} font-medium text-on-surface`}>{a.full_name}</td>
            <td className={`${cell} text-on-surface-variant`}>{nameOf(a) || '-'}</td>
            <td className={`${cell} text-on-surface-variant`}>{a.email || '-'}</td>
            <td className={cell}>
              <StatusPill active={a.is_active} />
            </td>
            <td className={cell}>
              <RowActions onEdit={() => setDrawer(a)} onDelete={() => del.setTarget(a)} />
            </td>
          </tr>
        ))}
      </TableCard>

      {drawer && (
        <ApplicantDrawer
          key={drawer === 'new' ? 'new' : drawer.id}
          record={drawer === 'new' ? null : drawer}
          departments={departments.items ?? []}
          onClose={() => setDrawer(null)}
          onSaved={finish}
          onDeleteFailed={finish}
        />
      )}
      <ConfirmDialog open={del.target !== null} message="Bu kayıt silinsin mi?" confirmLabel="Sil" tone="danger" busy={del.busy} onCancel={() => del.setTarget(null)} onConfirm={() => void del.confirm()} />
    </div>
  )
}
