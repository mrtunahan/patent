import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import Icon from './Icon'
import { LookupsProvider } from '../lib/lookups'
import { ToastProvider } from './Toast'

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

  return (
    <ToastProvider>
      <LookupsProvider>
      <div className="min-h-screen bg-surface-container-low text-on-surface">
        <aside className={`flex items-center gap-space-md bg-surface-container-low px-margin-mobile py-space-sm transition-[width] duration-300 lg:fixed lg:left-0 lg:top-0 lg:z-40 lg:h-full lg:flex-col lg:items-stretch lg:justify-start lg:gap-space-md lg:overflow-hidden lg:px-0 lg:py-space-lg ${collapsed ? 'lg:w-16' : 'lg:w-64'}`}>
          <div className={`flex shrink-0 items-center gap-space-sm ${collapsed ? 'lg:justify-center lg:px-0' : 'lg:px-space-lg'}`}>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Icon name="account_balance" className="text-[22px] text-on-primary" />
            </div>
            <div className={`flex flex-col ${hide}`}>
              <span className="font-title-sm text-title-sm leading-none tracking-tight text-on-surface">TTO PORTAL</span>
              <span className="font-label-sm text-label-sm text-on-surface-variant">Patent &amp; FSMH Takibi</span>
            </div>
          </div>
          <div className={`min-w-0 flex-1 lg:flex-none lg:pt-space-sm ${collapsed ? 'lg:px-space-xs' : 'lg:px-space-md'}`}>
            <button
              type="button"
              onClick={toggle}
              title={collapsed ? 'Menüyü aç' : 'Menüyü kapat'}
              aria-label={collapsed ? 'Menüyü aç' : 'Menüyü kapat'}
              aria-expanded={!collapsed}
              className={`mb-space-xs hidden h-10 items-center gap-space-sm rounded-lg px-space-md font-label-lg text-label-lg text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface lg:flex ${collapsed ? 'justify-center px-0' : ''}`}
            >
              <Icon name={collapsed ? 'menu' : 'menu_open'} className="text-[22px]" />
              <span className={`font-label-sm text-label-sm uppercase tracking-wider ${hide}`}>Menü</span>
            </button>
            <nav aria-label="Ana gezinme" className="flex gap-space-xs overflow-x-auto lg:flex-col lg:overflow-visible">
              {menu.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  title={item.label}
                  aria-label={item.label}
                  className={({ isActive }) => {
                    const active = isActive || (item.to === '/' && pathname.startsWith('/patents'))
                    return `flex shrink-0 items-center gap-space-sm whitespace-nowrap rounded-lg px-space-md py-space-sm font-label-lg text-label-lg transition-colors ${collapsed ? 'lg:justify-center lg:px-0' : ''} ${
                      active
                        ? 'bg-primary-container text-on-primary-container'
                        : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                    }`
                  }}
                >
                  <Icon name={item.icon} className="text-[20px]" />
                  <span className={hide}>{item.label}</span>
                </NavLink>
              ))}
            </nav>
          </div>
        </aside>
        <div className={`min-w-0 transition-[padding] duration-300 ${collapsed ? 'lg:pl-16' : 'lg:pl-64'}`}>
          <main className="min-w-0 px-margin-mobile pb-space-xl pt-space-lg sm:px-margin lg:pt-space-lg">
            <Outlet />
          </main>
        </div>
      </div>
      </LookupsProvider>
    </ToastProvider>
  )
}
