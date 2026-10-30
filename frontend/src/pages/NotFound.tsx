import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="flex flex-col gap-space-xs">
      <h1 className="font-headline-lg text-headline-lg tracking-tight text-on-surface">Sayfa bulunamadı</h1>
      <p className="font-body-md text-body-md text-on-surface-variant">
        Aradığınız sayfa yok. <Link to="/" className="font-semibold text-primary underline">Patent Listesi</Link>'ne dönün.
      </p>
    </section>
  )
}
