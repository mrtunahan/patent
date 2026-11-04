import { useCallback, useEffect, useState } from 'react'
import { useMatch, useNavigate, useParams } from 'react-router-dom'
import { ApiError, isAbort } from '../api/client'
import { exportPatents, listPatents, removePatent } from '../api/patents'
import type { Page, PatentListParams, PatentRead, SortDir, SortField } from '../api/types'
import ConfirmDialog from '../components/ConfirmDialog'
import FilterBar, { EMPTY_FILTERS, type Filters } from '../components/FilterBar'
import Icon from '../components/Icon'
import Pagination from '../components/Pagination'
import PatentDrawer from '../components/PatentDrawer'
import PatentTable from '../components/PatentTable'
import SummaryCards from '../components/SummaryCards'
import { useToast } from '../components/Toast'
import { view } from '../lib/listView'
import { useLookups } from '../lib/lookups'

const toNumber = (value: string) => (value ? Number(value) : undefined)

export default function PatentList() {
  const navigate = useNavigate()
  const toast = useToast()
  const { id } = useParams()
  const isNew = useMatch('/patents/new') !== null
  const editId = id && /^\d+$/.test(id) ? Number(id) : null
  const badId = id !== undefined && editId === null

  const [filters, setFilters] = useState<Filters>(view.filters)
  const [sortBy, setSortBy] = useState<SortField>(view.sortBy)
  const [sortDir, setSortDir] = useState<SortDir>(view.sortDir)
  const [page, setPage] = useState(view.page)
  const [pageSize, setPageSize] = useState(view.pageSize)
  const [data, setData] = useState<Page<PatentRead> | null>(null)
  const [status, setStatus] = useState<'loading' | 'error' | 'ready'>('loading')
  const [errorMessage, setErrorMessage] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const { lookups, error: lookupError, reload: reloadLookups } = useLookups()
  const [deleteTarget, setDeleteTarget] = useState<PatentRead | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [exporting, setExporting] = useState(false)

  Object.assign(view, { filters, sortBy, sortDir, page, pageSize })


  // Liste ve Excel dışa aktarma aynı filtre / sıralama parametrelerini kullanır.
  const filterParams = (): Omit<PatentListParams, 'page' | 'page_size'> => ({
    q: filters.q.trim() || undefined,
    applicant_id: toNumber(filters.applicantId),
    department_id: toNumber(filters.departmentId),
    fsmh_type_id: toNumber(filters.fsmhTypeId),
    sort_by: sortBy,
    sort_dir: sortDir,
  })

  useEffect(() => {
    const controller = new AbortController()
    const params: PatentListParams = { ...filterParams(), page, page_size: pageSize }
    setStatus('loading')
    listPatents(params, controller.signal)
      .then((result) => {
        if (result.items.length === 0 && result.total > 0 && page > 1) {
          setPage(Math.max(1, Math.ceil(result.total / pageSize))) // sayfa aşımı: son geçerli sayfaya git
          return
        }
        setData(result)
        setStatus('ready')
      })
      .catch((err) => {
        if (isAbort(err)) return // eski isteğin yanıtı yenisini ezmez
        setErrorMessage(err instanceof ApiError ? err.detail : 'Liste yüklenemedi.')
        setStatus('error')
      })
    return () => controller.abort()
  }, [filters, sortBy, sortDir, page, pageSize, refreshKey])

  // Geçersiz /patents/abc adresi
  useEffect(() => {
    if (badId) {
      toast('Patent bulunamadı.')
      navigate('/', { replace: true })
    }
  }, [badId, navigate, toast])

  const updateFilters = useCallback((patch: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...patch }))
    setPage(1)
  }, [])
  const resetFilters = useCallback(() => {
    setFilters(EMPTY_FILTERS)
    setPage(1)
  }, [])

  const onSort = (field: SortField) => {
    if (field === sortBy) setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'))
    else {
      setSortBy(field)
      setSortDir('asc')
    }
    setPage(1)
  }

  const refresh = () => setRefreshKey((key) => key + 1)
  const closeDrawer = useCallback(() => navigate('/'), [navigate])
  const drawerNotFound = useCallback(() => {
    toast('Patent bulunamadı.')
    navigate('/', { replace: true })
    setRefreshKey((key) => key + 1)
  }, [navigate, toast])
  const drawerSaved = useCallback(
    (message: string) => {
      toast(message)
      navigate('/')
      setRefreshKey((key) => key + 1)
    },
    [navigate, toast],
  )

  const confirmDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await removePatent(deleteTarget.id)
      toast('Kayıt silindi.')
    } catch (err) {
      toast(err instanceof ApiError && err.status !== 404 ? `Silinemedi: ${err.detail}` : 'Kayıt silinemedi.')
    }
    setDeleting(false)
    setDeleteTarget(null)
    refresh()
  }

  const runExport = async () => {
    setExporting(true)
    try {
      const { blob, filename } = await exportPatents(filterParams())
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename ?? `patent-takip-${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      toast(err instanceof ApiError ? `Dışa aktarılamadı: ${err.detail}` : 'Dışa aktarılamadı.')
    }
    setExporting(false)
  }

  const drawerMode: 'new' | number | null = isNew ? 'new' : editId

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <div className="flex flex-col justify-between gap-space-md lg:flex-row lg:items-center">
        <div className="flex flex-col">
          <div className="flex items-center gap-space-xs text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant lg:hidden">
            <span>TTO Otomasyonu</span>
            <Icon name="chevron_right" className="text-[14px]" />
            <span className="font-semibold text-primary">Patent Takip</span>
          </div>
          <h1 className="mt-space-xs text-2xl font-semibold tracking-tight lg:mt-0 lg:text-3xl text-on-surface">Patent Takip Listesi</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">Patent / FSMH başvurularının takip listesi</p>
        </div>
        <div className="flex flex-wrap items-center gap-space-sm self-start lg:self-auto">
          <button
            type="button"
            onClick={() => void runExport()}
            disabled={exporting}
            className="flex h-10 items-center justify-center gap-space-xs rounded-xl bg-surface px-space-lg font-label-lg text-label-lg font-semibold text-on-surface shadow-raised transition-all hover:shadow-raised-sm active:shadow-inset-sm disabled:opacity-60"
          >
            <Icon name="table_view" className="text-[20px] text-secondary" />
            {exporting ? 'Hazırlanıyor...' : 'Excel Dışa Aktar'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/patents/new')}
            className="flex h-10 items-center justify-center gap-space-xs rounded-xl bg-surface px-space-lg font-label-lg text-label-lg font-semibold text-primary shadow-raised transition-all hover:shadow-raised-sm active:shadow-inset-sm"
          >
            <Icon name="add_circle" className="text-[20px]" />
            Yeni Patent Ekle
          </button>
        </div>
      </div>

      <SummaryCards fsmhTypes={lookups?.fsmhTypes ?? null} refreshKey={refreshKey} />

      {lookupError && (
        <div role="alert" className="flex items-center justify-between gap-space-md rounded-xl bg-error-container p-space-sm font-body-md text-body-md text-on-error-container">
          <span>Filtre listeleri yüklenemedi.</span>
          <button type="button" onClick={() => void reloadLookups().catch(() => {})} className="rounded-xl bg-surface px-space-md py-space-xs font-label-md text-label-md font-semibold text-primary shadow-raised-sm">
            Yeniden dene
          </button>
        </div>
      )}

      <FilterBar filters={filters} lookups={lookups} total={data?.total ?? null} onChange={updateFilters} onReset={resetFilters} />

      <div className="flex min-w-0 flex-col overflow-hidden rounded-xl bg-surface shadow-raised">
        <div className="flex items-center gap-space-sm bg-surface p-space-md">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface text-primary shadow-inset-sm">
            <Icon name="view_timeline" className="text-[20px]" />
          </div>
          <span className="font-title-md text-title-md font-semibold text-on-surface">Fikri Hak Portföy Kütüğü</span>
        </div>
        <PatentTable
          items={data?.items ?? null}
          status={status}
          errorMessage={errorMessage}
          page={page}
          pageSize={pageSize}
          sortBy={sortBy}
          sortDir={sortDir}
          onSort={onSort}
          onEdit={(patentId) => navigate(`/patents/${patentId}`)}
          onDelete={setDeleteTarget}
          onRetry={refresh}
        />
        <Pagination
          page={page}
          pageSize={pageSize}
          total={data?.total ?? 0}
          onPage={setPage}
          onPageSize={(size) => {
            setPageSize(size)
            setPage(1)
          }}
        />
      </div>

      {drawerMode !== null && (
        <PatentDrawer key={String(drawerMode)} mode={drawerMode} onClose={closeDrawer} onSaved={drawerSaved} onNotFound={drawerNotFound} />
      )}
      <ConfirmDialog
        open={deleteTarget !== null}
        message="Bu kayıt silinsin mi?"
        confirmLabel="Sil"
        tone="danger"
        busy={deleting}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => void confirmDelete()}
      />
    </div>
  )
}
