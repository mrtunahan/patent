// ISO "YYYY-MM-DD" -> "GG.AA.YYYY" (Date nesnesi kullanılmaz); boş/geçersizse "-".
export function formatDate(iso: string | null | undefined): string {
  const match = iso ? /^(\d{4})-(\d{2})-(\d{2})/.exec(iso) : null
  return match ? `${match[3]}.${match[2]}.${match[1]}` : '-'
}

// Backend normalize_tr ile aynı mantık (İ->i, I->ı, küçük harf, boşluk tekilleştirme); yalnızca ortak tekrarı uyarısı için.
export function normalizeKey(value: string): string {
  return value
    .trim()
    .normalize('NFC')
    .replace(/İ/g, 'i')
    .replace(/I/g, 'ı')
    .toLowerCase()
    .replace(/\s+/g, ' ')
}

// FSMH türü hap renkleri (tam sınıf adları: Tailwind'in görebilmesi için sabit yazılır).
export function fsmhTypeStyle(name: string): { pill: string; dot: string } {
  switch (normalizeKey(name)) {
    case 'patent':
      return { pill: 'bg-primary-fixed text-on-primary-fixed', dot: 'bg-primary' }
    case 'faydalı model':
      return { pill: 'bg-secondary-fixed text-on-secondary-fixed', dot: 'bg-secondary' }
    case 'tasarım tescili':
      return { pill: 'bg-tertiary-fixed text-on-tertiary-fixed', dot: 'bg-tertiary' }
    case 'telif hakkı':
      return { pill: 'bg-primary-container text-on-primary-container', dot: 'bg-primary' }
    default:
      return { pill: 'bg-surface-container-highest text-on-surface', dot: 'bg-outline' }
  }
}

// Patent durumu hap renkleri.
export function statusStyle(status: string): string {
  switch (status) {
    case 'Tescillendi':
      return 'bg-primary-fixed text-on-primary-fixed'
    case 'Süreç Devam Ediyor':
      return 'bg-secondary-fixed text-on-secondary-fixed'
    case 'Reddedildi':
      return 'bg-error-container text-on-error-container'
    default:
      return 'bg-surface-container-highest text-on-surface'
  }
}
