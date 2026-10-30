export default function PagePlaceholder({ title }: { title: string }) {
  return (
    <section className="flex flex-col gap-space-xs">
      <h1 className="font-headline-lg text-headline-lg tracking-tight text-on-surface">{title}</h1>
      <p className="font-body-md text-body-md text-on-surface-variant">Bu sayfa henüz geliştirilmedi.</p>
    </section>
  )
}
