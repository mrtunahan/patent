import { avatarTone, initials } from '../lib/format'

// Yuvarlak monogram avatar: ad ve soyadın baş harfi, renk addan deterministik.
export default function Avatar({ name, size = 'sm' }: { name: string; size?: 'sm' | 'lg' }) {
  const dimension = size === 'lg' ? 'h-12 w-12 text-[18px]' : 'h-8 w-8 text-[12px]'
  return (
    <span aria-hidden className={`flex shrink-0 items-center justify-center rounded-full font-bold ${dimension} ${avatarTone(name)}`}>
      {initials(name)}
    </span>
  )
}
