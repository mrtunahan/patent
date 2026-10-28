import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section>
      <h2 className="text-lg font-semibold">Sayfa bulunamadı</h2>
      <p className="mt-2 text-muted">
        Aradığınız sayfa yok. <Link to="/" className="text-brand-600 underline">Patent Listesi</Link>'ne dönün.
      </p>
    </section>
  )
}
