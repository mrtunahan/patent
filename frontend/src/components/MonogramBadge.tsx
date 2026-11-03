// Liste satırı monogram kutusu: en çok patentli satırda koyu mor dolu, diğerlerinde açık mor.
export default function MonogramBadge({ text, strong }: { text: string; strong: boolean }) {
  return (
    <span aria-hidden className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg font-label-md text-label-md font-bold ${strong ? 'bg-primary text-on-primary' : 'bg-primary-fixed text-on-primary-fixed'}`}>
      {text}
    </span>
  )
}
