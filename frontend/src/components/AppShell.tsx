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

export default function AppShell() {
  const { pathname } = useLocation()

  return (
    <ToastProvider>
      <LookupsProvider>
      <div className="min-h-screen bg-surface-container-low text-on-surface">
        <aside className="flex items-center gap-space-md bg-surface-container-low px-margin-mobile py-space-sm lg:fixed lg:left-0 lg:top-0 lg:z-40 lg:h-full lg:w-64 lg:flex-col lg:items-stretch lg:justify-start lg:gap-space-md lg:px-0 lg:py-space-lg">
          <div className="flex shrink-0 items-center gap-space-sm lg:px-space-lg">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Icon name="account_balance" className="text-[22px] text-on-primary" />
            </div>
            <div className="flex flex-col">
              <span className="font-title-sm text-title-sm leading-none tracking-tight text-on-surface">TTO PORTAL</span>
              <span className="font-label-sm text-label-sm text-on-surface-variant">Patent &amp; FSMH Takibi</span>
            </div>
          </div>
          <div className="min-w-0 flex-1 lg:flex-none lg:px-space-md lg:pt-space-sm">
            <div className="hidden px-space-sm pb-space-xs font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant lg:block">
              Menü
            </div>
            <nav aria-label="Ana gezinme" className="flex gap-space-xs overflow-x-auto lg:flex-col lg:overflow-visible">
              {menu.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => {
                    const active = isActive || (item.to === '/' && pathname.startsWith('/patents'))
                    return `flex shrink-0 items-center gap-space-sm whitespace-nowrap rounded-lg px-space-md py-space-sm font-label-lg text-label-lg transition-colors ${
                      active
                        ? 'bg-primary-container text-on-primary-container'
                        : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                    }`
                  }}
                >
                  <Icon name={item.icon} className="text-[20px]" />
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </aside>
        <div className="min-w-0 lg:pl-64">
          <main className="min-w-0 px-margin-mobile pb-space-xl pt-space-lg sm:px-margin lg:pt-space-lg">
            <Outlet />
          </main>
        </div>
      </div>
      </LookupsProvider>
    </ToastProvider>
  )
}
