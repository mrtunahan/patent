import { useEffect, useRef, useState, type FormEvent } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { isAbort } from '../api/client'
import { listPatents } from '../api/patents'
import type { PatentRead } from '../api/types'
import { formatDate } from '../lib/format'
import Icon from './Icon'
import { LookupsProvider } from '../lib/lookups'
import { ToastProvider } from './Toast'

// Kabuk, Offline Asistan > TTO Modülü içindeki "TTO Otomasyonu" kabuğuyla aynı tasarımdadır:
// açık neumorfik kenar menü (kabarık öğeler, etkin öğe gömük + indigo), üstte sabit başlık çubuğu.
// Patent Formu sekme değildir (çekmece); /patents/* iken "Patent Listesi" vurgulu kalır.
const menu = [
  { to: '/', label: 'Patent Listesi', icon: 'verified', end: true },
  { to: '/applicants', label: 'Başvuru Sahipleri', icon: 'person' },
  { to: '/departments', label: 'Bölümler', icon: 'domain' },
  { to: '/attorney-firms', label: 'Vekil Firmalar', icon: 'business_center' },
  { to: '/partners', label: 'Ortaklar', icon: 'handshake' },
]

const STORAGE_KEY = 'sidebarCollapsed'

function readCollapsed(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    return false // localStorage yoksa menü açık
  }
}

// Ana sisteme (Offline Asistan > Patent & FSMH modülü) aynı kökenden iframe ile gömülü mü?
// Gömülüyken "Buluş Bildirimleri" ve "Offline Asistan'a dön" düğmeleri görünür; ana sayfaya
// postMessage ile haber verir (yalnız aynı köken hedeflenir, ana sayfa da kaynağı denetler).
const EMBEDDED = (() => {
  try {
    return window.self !== window.top
  } catch {
    return true // farklı kökenli üst pencereye erişim hata verir: yine de gömülüdür
  }
})()
const MESSAGE_SOURCE = 'patent-takip'
function notifyHost(tip: 'don' | 'bildirimler') {
  window.parent.postMessage({ kaynak: MESSAGE_SOURCE, tip }, window.location.origin)
}

const today = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })

export default function AppShell() {
  const { pathname } = useLocation()
  const [collapsed, setCollapsed] = useState(readCollapsed)
  const toggle = () =>
    setCollapsed((prev) => {
      try {
        window.localStorage.setItem(STORAGE_KEY, prev ? '0' : '1')
      } catch {
        /* kalıcılık yoksa yalnızca bu oturumda geçerli */
      }
      return !prev
    })
  const hide = collapsed ? 'lg:hidden' : '' // daralmış menüde (yalnızca lg+) yazılar gizlenir
  const isActive = (item: (typeof menu)[number]) =>
    item.end ? pathname === item.to || (item.to === '/' && pathname.startsWith('/patents')) : pathname.startsWith(item.to)
  const current = menu.find(isActive)

  return (
    <ToastProvider>
      <LookupsProvider>
        <div className="min-h-screen bg-surface text-on-surface">
          {/* Kenar menü (lg+); küçük ekranda üstte yatay çubuk */}
          <aside
            className={`z-50 flex items-center gap-space-md bg-surface px-margin-mobile py-space-sm shadow-header transition-[width] duration-300 lg:fixed lg:left-0 lg:top-0 lg:h-full lg:flex-col lg:items-stretch lg:gap-0 lg:overflow-hidden lg:py-6 lg:shadow-sidebar ${
              collapsed ? 'lg:w-20 lg:px-3' : 'lg:w-72 lg:px-6'
            }`}
          >
            <div className={`flex shrink-0 items-center gap-3 lg:mb-10 ${collapsed ? 'lg:justify-center lg:px-0' : 'lg:px-2'}`}>
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
                <Icon name="verified_user" className="text-[18px] text-on-primary" />
              </div>
              <div className={`flex flex-col ${hide}`}>
                <span className="text-sm font-semibold text-on-surface">Patent &amp; FSMH Takibi</span>
              </div>
            </div>

            <div className={`mb-6 hidden px-2 lg:flex lg:items-center lg:justify-between ${collapsed ? 'lg:justify-center lg:px-0' : ''}`}>
              <span className={`text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant ${hide}`}>Ana Menü</span>
              <button
                type="button"
                onClick={toggle}
                title={collapsed ? 'Menüyü aç' : 'Menüyü kapat'}
                aria-label={collapsed ? 'Menüyü aç' : 'Menüyü kapat'}
                aria-expanded={!collapsed}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface text-on-surface-variant shadow-raised-sm transition-colors hover:text-primary"
              >
                <Icon name={collapsed ? 'menu' : 'menu_open'} className="text-[18px]" />
              </button>
            </div>

            <nav aria-label="Ana gezinme" className="flex min-w-0 flex-1 gap-3 overflow-x-auto p-1 lg:flex-col lg:overflow-visible lg:p-0">
              {menu.map((item) => {
                const active = isActive(item)
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    title={item.label}
                    aria-label={item.label}
                    aria-current={active ? 'page' : undefined}
                    className={`flex shrink-0 items-center gap-3 whitespace-nowrap rounded-xl px-4 py-3 text-sm transition-all duration-200 ${collapsed ? 'lg:justify-center lg:px-0' : ''} ${
                      active ? 'font-semibold text-primary shadow-inset' : 'text-on-surface-variant shadow-raised hover:text-on-surface'
                    }`}
                  >
                    <Icon name={item.icon} className="text-[20px]" />
                    <span className={hide}>{item.label}</span>
                  </NavLink>
                )
              })}
            </nav>
            {EMBEDDED && (
              <button
                type="button"
                onClick={() => notifyHost('don')}
                title="Offline Asistan'a dön"
                aria-label="Offline Asistan'a dön"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-surface text-on-surface-variant shadow-raised lg:hidden"
              >
                <Icon name="logout" className="text-[18px]" />
              </button>
            )}

            {EMBEDDED && (
              <div className="mb-4 mt-6 hidden flex-col gap-3 lg:flex">
                <div className={`px-2 ${hide}`}>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">Offline Asistan</span>
                </div>
                <button
                  type="button"
                  onClick={() => notifyHost('bildirimler')}
                  title="Buluş Bildirimleri"
                  className={`flex items-center gap-3 rounded-xl px-4 py-3 text-left text-sm text-on-surface-variant shadow-raised transition-all duration-200 hover:text-on-surface ${collapsed ? 'lg:justify-center lg:px-0' : ''}`}
                >
                  <Icon name="inbox" className="text-[20px]" />
                  <span className={hide}>Buluş Bildirimleri</span>
                </button>
              </div>
            )}

            <div className={`mt-auto hidden rounded-xl bg-surface p-4 shadow-inset lg:block ${collapsed ? 'lg:p-3' : ''}`}>
              <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
                <Icon name="verified_user" className="text-[22px] text-primary" />
                <div className={`flex flex-col ${hide}`}>
                  <span className="text-xs font-semibold text-on-surface">Patent Takip</span>
                  <span className="text-[10px] text-on-surface-variant">v1.0 · Aktif</span>
                </div>
              </div>
            </div>
          </aside>

          {/* İçerik */}
          <div className={`min-w-0 transition-[padding] duration-300 ${collapsed ? 'lg:pl-20' : 'lg:pl-72'}`}>
            <header
              className={`hidden h-20 items-center justify-between bg-surface px-8 shadow-header transition-[left] duration-300 lg:fixed lg:right-0 lg:top-0 lg:z-40 lg:flex ${
                collapsed ? 'lg:left-20' : 'lg:left-72'
              }`}
            >
              <HeaderSearch />
              <div className="flex items-center gap-5">
                <div className="hidden items-center gap-2 rounded-xl bg-surface px-3 py-1.5 text-xs text-on-surface shadow-raised xl:flex">
                  <Icon name="calendar_today" className="text-[18px] text-primary" />
                  <span className="font-medium">{today}</span>
                </div>
                <NotificationBell refreshKey={pathname} />
                <div className="h-6 w-px bg-surface-variant" />
                <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span className="text-primary">{current?.label ?? 'Patent Takip'}</span>
                </div>
                {EMBEDDED && (
                  <button
                    type="button"
                    onClick={() => notifyHost('don')}
                    title="Offline Asistan'a dön"
                    aria-label="Offline Asistan'a dön"
                    className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface text-on-surface-variant shadow-raised transition-colors hover:text-error"
                  >
                    <Icon name="logout" className="text-[18px]" />
                  </button>
                )}
              </div>
            </header>
            <main className="min-w-0 px-margin-mobile pb-12 pt-space-lg sm:px-8 lg:pt-28">
              <Outlet />
            </main>
          </div>
        </div>
      </LookupsProvider>
    </ToastProvider>
  )
}

// Üst çubuk araması: Enter ile Patent Listesi'ne gider ve aramayı liste filtresine uygular.
function HeaderSearch() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const submit = (event: FormEvent) => {
    event.preventDefault()
    navigate('/', { state: { search: q.trim(), at: Date.now() } })
  }
  return (
    <form role="search" onSubmit={submit} className="w-96 max-w-[40%]">
      <div className="flex w-full items-center gap-2 rounded-xl bg-surface px-3 py-2 shadow-inset">
        <Icon name="search" className="text-[18px] text-on-surface-variant" />
        <input
          type="search"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          placeholder="Patent, başvuru sahibi veya ortak ara…"
          aria-label="Patentlerde ara"
          className="w-full bg-transparent text-xs text-on-surface placeholder:text-on-surface-variant focus:outline-none"
        />
      </div>
    </form>
  )
}

const RECENT_DAYS = 7

// Bildirimler: son eklenen patent kayıtları; rozet son 7 günde eklenen kayıt sayısını gösterir.
function NotificationBell({ refreshKey }: { refreshKey: string }) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<PatentRead[] | null>(null)
  const [failed, setFailed] = useState(false)
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const controller = new AbortController()
    listPatents({ sort_by: 'created_at', sort_dir: 'desc', page: 1, page_size: 5 }, controller.signal)
      .then((page) => {
        setItems(page.items)
        setFailed(false)
      })
      .catch((err) => {
        if (!isAbort(err)) setFailed(true)
      })
    return () => controller.abort()
  }, [refreshKey])

  useEffect(() => {
    if (!open) return
    const onPointer = (event: MouseEvent) => {
      if (!box.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const since = Date.now() - RECENT_DAYS * 24 * 60 * 60 * 1000
  const fresh = (items ?? []).filter((p) => Date.parse(p.created_at) >= since).length

  return (
    <div ref={box} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        title="Bildirimler"
        aria-label={fresh > 0 ? `Bildirimler: ${fresh} yeni kayıt` : 'Bildirimler'}
        aria-haspopup="dialog"
        aria-expanded={open}
        className={`relative flex h-9 w-9 items-center justify-center rounded-xl bg-surface transition-colors hover:text-primary ${open ? 'text-primary shadow-inset-sm' : 'text-on-surface-variant shadow-raised'}`}
      >
        <Icon name="notifications" className="text-[20px]" />
        {fresh > 0 && (
          <span className="absolute -right-1 -top-1 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-on-primary">
            {fresh}
          </span>
        )}
      </button>
      {open && (
        <div role="dialog" aria-label="Bildirimler" className="absolute right-0 top-12 z-50 w-80 rounded-2xl bg-surface p-4 shadow-modal">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold text-on-surface">Son Eklenen Kayıtlar</span>
            {fresh > 0 && <span className="rounded-lg bg-surface px-2 py-0.5 text-[10px] font-semibold text-primary shadow-inset-sm">{fresh} yeni</span>}
          </div>
          {failed ? (
            <p className="text-xs text-error">Bildirimler yüklenemedi.</p>
          ) : items === null ? (
            <p className="text-xs text-on-surface-variant">Yükleniyor…</p>
          ) : items.length === 0 ? (
            <p className="text-xs text-on-surface-variant">Henüz kayıt yok.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {items.map((p) => {
                const isFresh = Date.parse(p.created_at) >= since
                return (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setOpen(false)
                        navigate(`/patents/${p.id}`)
                      }}
                      className="flex w-full items-start gap-3 rounded-xl px-3 py-2 text-left transition-colors hover:bg-surface-bright/60"
                    >
                      <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${isFresh ? 'bg-primary' : 'bg-surface-variant'}`} />
                      <span className="flex min-w-0 flex-col">
                        <span className="truncate text-xs font-semibold text-on-surface">{p.title}</span>
                        <span className="truncate text-[11px] text-on-surface-variant">
                          {p.applicant.full_name} · {p.fsmh_type.name} · {formatDate(p.created_at)}
                        </span>
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
