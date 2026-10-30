import { useCallback, useEffect, useState } from 'react'
import { useMatch, useNavigate, useParams } from 'react-router-dom'
import { ApiError, isAbort } from '../api/client'
import { listApplicants, listAttorneyFirms, listDepartments, listFsmhTypes } from '../api/lookups'
import { listPatents, removePatent } from '../api/patents'
import type { Lookups, Page, PatentListParams, PatentRead, SortDir, SortField } from '../api/types'
import ConfirmDialog from '../components/ConfirmDialog'
import FilterBar, { EMPTY_FILTERS, dateRangeInvalid, type Filters } from '../components/FilterBar'
import Icon from '../components/Icon'
import Pagination from '../components/Pagination'
import PatentDrawer from '../components/PatentDrawer'
import PatentTable from '../components/PatentTable'
import SummaryCards from '../components/SummaryCards'
import { useToast } from '../components/Toast'

// Çekmece rotaları (/patents/new, /patents/:id) bu bileşeni yeniden kullandığından görünüm durumu
// (filtre, sıralama, sayfa) modül düzeyinde de tutulur; böylece çekmece açılıp kapanınca liste sıfırlanmaz.
const view = { filters: EMPTY_FILTERS, sortBy: 'id' as SortField, sortDir: 'asc' as SortDir, page: 1, pageSize: 25 }

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
  const [lookups, setLookups] = useState<Lookups | null>(null)
  const [lookupError, setLookupError] = useState(false)
  const [lookupTick, setLookupTick] = useState(0)
  const [deleteTarget, setDeleteTarget] = useState<PatentRead | null>(null)
  const [deleting, setDeleting] = useState(false)

  Object.assign(view, { filters, sortBy, sortDir, page, pageSize })

  useEffect(() => {
    const controller = new AbortController()
    setLookupError(false)
    Promise.all([
      listApplicants(controller.signal),
      listDepartments(controller.signal),
      listFsmhTypes(controller.signal),
      listAttorneyFirms(controller.signal),
    ])
      .then(([applicants, departments, fsmhTypes, attorneyFirms]) => setLookups({ applicants, departments, fsmhTypes, attorneyFirms }))
      .catch((err) => {
        if (!isAbort(err)) setLookupError(true)
      })
    return () => controller.abort()
  }, [lookupTick])

  const invalidDates = dateRangeInvalid(filters)

  useEffect(() => {
    if (invalidDates) return // tarih aralığı geçersizse istek atılmaz
    const controller = new AbortController()
    const params: PatentListParams = {
      q: filters.q.trim() || undefined,
      applicant_id: toNumber(filters.applicantId),
      department_id: toNumber(filters.departmentId),
      fsmh_type_id: toNumber(filters.fsmhTypeId),
      attorney_firm_id: toNumber(filters.attorneyFirmId),
      has_attorney: filters.hasAttorney ? filters.hasAttorney === 'true' : undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
      page,
      page_size: pageSize,
    }
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
  }, [filters, sortBy, sortDir, page, pageSize, refreshKey, invalidDates])

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

  const drawerMode: 'new' | number | null = isNew ? 'new' : editId

  return (
    <div className="flex min-w-0 flex-col gap-space-lg">
      <div className="flex flex-col justify-between gap-space-md lg:flex-row lg:items-center">
        <div className="flex flex-col">
          <div className="flex items-center gap-space-xs font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
            <span>TTO Portalı</span>
            <Icon name="chevron_right" className="text-[14px]" />
            <span className="font-semibold text-primary">Patent Takip</span>
          </div>
          <h1 className="mt-space-xs font-headline-lg text-headline-lg tracking-tight text-on-surface">Patent Takip Listesi</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">Patent / FSMH başvurularının takip listesi</p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/patents/new')}
          className="flex h-10 items-center justify-center gap-space-xs self-start rounded-lg bg-primary px-space-lg font-label-lg text-label-lg text-on-primary shadow-md transition-all hover:bg-primary/95 lg:self-auto"
        >
          <Icon name="add_circle" className="text-[20px]" />
          Yeni Patent Ekle
        </button>
      </div>

      <SummaryCards fsmhTypes={lookups?.fsmhTypes ?? null} refreshKey={refreshKey} />

      {lookupError && (
        <div role="alert" className="flex items-center justify-between gap-space-md rounded-lg bg-error-container p-space-sm font-body-md text-body-md text-on-error-container">
          <span>Filtre listeleri yüklenemedi.</span>
          <button type="button" onClick={() => setLookupTick((n) => n + 1)} className="rounded-lg bg-primary px-space-md py-space-xs font-label-md text-label-md text-on-primary">
            Yeniden dene
          </button>
        </div>
      )}

      <FilterBar filters={filters} lookups={lookups} total={data?.total ?? null} onChange={updateFilters} onReset={resetFilters} />

      <div className="flex min-w-0 flex-col overflow-hidden rounded-xl bg-surface-container shadow-md">
        <div className="flex items-center justify-between bg-surface-container-high p-space-md">
          <div className="flex items-center gap-space-sm">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-on-primary">
              <Icon name="view_timeline" className="text-[18px]" />
            </div>
            <span className="font-title-sm text-title-sm font-bold text-on-surface">Patent Takip Listesi</span>
          </div>
          <div className="flex items-center gap-space-xs font-label-sm text-label-sm text-on-surface-variant">
            <span>Yatay kaydırma: aktif</span>
            <Icon name="swap_horiz" className="text-[16px]" />
          </div>
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
        <PatentDrawer key={String(drawerMode)} mode={drawerMode} lookups={lookups} onClose={closeDrawer} onSaved={drawerSaved} onNotFound={drawerNotFound} />
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
