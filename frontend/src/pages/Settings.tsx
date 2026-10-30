import { useEffect, useState } from 'react'
import { ApiError, isAbort } from '../api/client'
import { getSettings, saveSettings } from '../api/settings'
import type { Settings as SettingsMap } from '../api/types'
import Icon from '../components/Icon'
import { Field, controlClass } from '../components/formStyles'
import { PAGE_SIZES } from '../components/Pagination'
import { useToast } from '../components/Toast'
import { resetListDefaults } from '../lib/listView'

export default function Settings() {
  const toast = useToast()
  const [status, setStatus] = useState<'loading' | 'error' | 'ready'>('loading')
  const [loadError, setLoadError] = useState('')
  const [institutionName, setInstitutionName] = useState('')
  const [pageSize, setPageSize] = useState('25')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setStatus('loading')
    getSettings(controller.signal)
      .then((settings: SettingsMap) => {
        setInstitutionName(settings.institution_name ?? '')
        setPageSize(PAGE_SIZES.includes(Number(settings.default_page_size)) ? settings.default_page_size : '25')
        setStatus('ready')
      })
      .catch((err) => {
        if (isAbort(err)) return
        setLoadError(err instanceof ApiError ? err.detail : 'Ayarlar yüklenemedi.')
        setStatus('error')
      })
    return () => controller.abort()
  }, [tick])

  const save = async () => {
    setSaving(true)
    setError('')
    const values: SettingsMap = { default_page_size: pageSize }
    if (institutionName.trim()) values.institution_name = institutionName.trim() // boş kurum adı gönderilmez
    try {
      await saveSettings(values)
      resetListDefaults()
      toast('Ayarlar kaydedildi.')
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Ayarlar kaydedilemedi.')
    }
    setSaving(false)
  }

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <div className="flex flex-col">
        <div className="flex items-center gap-space-xs font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
          <span>TTO Portalı</span>
          <Icon name="chevron_right" className="text-[14px]" />
          <span className="font-semibold text-primary">Ayarlar</span>
        </div>
        <h1 className="mt-space-xs font-headline-lg text-headline-lg tracking-tight text-on-surface">Ayarlar</h1>
        <p className="font-body-md text-body-md text-on-surface-variant">Uygulama ayarları</p>
      </div>

      <div className="flex max-w-2xl min-w-0 flex-col overflow-hidden rounded-xl bg-surface-container shadow-md">
        <div className="flex items-center gap-space-sm bg-surface-container-high p-space-md">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-on-primary">
            <Icon name="settings" className="text-[18px]" />
          </div>
          <span className="font-title-sm text-title-sm font-bold text-on-surface">Genel Ayarlar</span>
        </div>
        {status === 'loading' && <p className="p-space-lg text-on-surface-variant">Yükleniyor...</p>}
        {status === 'error' && (
          <div className="flex flex-wrap items-center gap-space-sm p-space-lg text-on-surface-variant">
            <span>{loadError}</span>
            <button type="button" onClick={() => setTick((n) => n + 1)} className="rounded-lg bg-primary px-space-md py-space-xs font-label-md text-label-md text-on-primary">
              Yeniden dene
            </button>
          </div>
        )}
        {status === 'ready' && (
          <form
            noValidate
            onSubmit={(event) => {
              event.preventDefault()
              void save()
            }}
            className="flex flex-col gap-space-lg p-space-lg"
          >
            {error && (
              <div role="alert" className="flex items-start gap-space-sm rounded-lg bg-error-container p-space-sm font-body-md text-body-md text-on-error-container">
                <Icon name="error" className="mt-0.5 text-[20px]" />
                <span>{error}</span>
              </div>
            )}
            <Field id="institutionName" text="Kurum Adı">
              <input id="institutionName" type="text" value={institutionName} maxLength={200} disabled={saving} onChange={(e) => setInstitutionName(e.target.value)} className={`h-10 px-space-sm ${controlClass}`} />
            </Field>
            <Field id="defaultPageSize" text="Varsayılan Sayfa Boyutu">
              <select id="defaultPageSize" value={pageSize} disabled={saving} onChange={(e) => setPageSize(e.target.value)} className={`h-10 px-space-sm md:max-w-xs ${controlClass}`}>
                {PAGE_SIZES.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </Field>
            <div className="flex justify-end">
              <button type="submit" disabled={saving} className="flex h-10 items-center gap-space-xs rounded-lg bg-primary px-space-lg font-label-lg text-label-lg text-on-primary shadow-md transition-all hover:bg-primary/95 disabled:opacity-60">
                <Icon name="check" className="text-[18px]" />
                {saving ? 'Kaydediliyor...' : 'Kaydet'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
