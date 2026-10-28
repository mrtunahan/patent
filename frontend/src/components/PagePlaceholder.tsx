export default function PagePlaceholder({ title }: { title: string }) {
  return (
    <section>
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mt-2 text-muted">Bu sayfa henüz geliştirilmedi.</p>
    </section>
  )
}
