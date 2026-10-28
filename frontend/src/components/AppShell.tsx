import { NavLink, Outlet, useLocation } from 'react-router-dom'

// Patent Formu sekme değildir; formdayken "Patent Listesi" sekmesi vurgulu kalır.
const tabs = [
  { to: '/', label: 'Patent Listesi', end: true },
  { to: '/applicants', label: 'Başvuru Sahipleri' },
  { to: '/departments', label: 'Bölümler' },
  { to: '/attorney-firms', label: 'Vekil Firmalar' },
  { to: '/settings', label: 'Ayarlar' },
]

export default function AppShell() {
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto max-w-6xl px-4 pt-4">
          <h1 className="text-xl font-semibold text-brand-900">Patent Takip</h1>
          <nav aria-label="Ana gezinme" className="mt-3 flex flex-wrap gap-x-1 gap-y-1">
            {tabs.map((tab) => (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
                className={({ isActive }) => {
                  const active = isActive || (tab.to === '/' && pathname.startsWith('/patents'))
                  return [
                    'rounded-t-ui border-b-2 px-3 py-2 text-sm font-medium',
                    active
                      ? 'border-brand-600 bg-brand-50 text-brand-700'
                      : 'border-transparent text-muted hover:text-ink',
                  ].join(' ')
                }}
              >
                {tab.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl min-w-0 break-words px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
