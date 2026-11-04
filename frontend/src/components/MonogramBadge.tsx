// Liste satırı monogram kutusu (gömük): en çok patentli satırda mor, diğerlerinde indigo yazı.
export default function MonogramBadge({ text, strong }: { text: string; strong: boolean }) {
  return (
    <span aria-hidden className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg font-label-md text-label-md font-bold bg-surface shadow-inset-sm ${strong ? 'text-tertiary' : 'text-primary'}`}>
      {text}
    </span>
  )
}
