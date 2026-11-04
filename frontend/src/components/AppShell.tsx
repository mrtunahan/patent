import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
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
                <span className="text-sm font-semibold text-on-surface">TTO Otomasyonu</span>
                <span className="text-[11px] text-on-surface-variant">Patent &amp; FSMH Takibi</span>
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
              <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">
                <span>TTO Otomasyonu</span>
                <Icon name="chevron_right" className="text-[14px]" />
                <span className="text-primary">{current?.label ?? 'Patent Takip'}</span>
              </div>
              <div className="flex items-center gap-5">
                <div className="flex items-center gap-2 rounded-xl bg-surface px-3 py-1.5 text-xs text-on-surface shadow-raised">
                  <Icon name="calendar_today" className="text-[18px] text-primary" />
                  <span className="font-medium">{today}</span>
                </div>
                <div className="h-6 w-px bg-surface-variant" />
                <div className="flex items-center gap-2 text-xs">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span className="font-medium text-primary">Patent &amp; FSMH</span>
                </div>
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
