import type { SortDir, SortField } from '../api/types'
import { EMPTY_FILTERS, type Filters } from '../components/FilterBar'

// Patent Listesi görünüm durumu: çekmece rotaları sayfayı yeniden kullandığından filtre/sıralama/sayfa
// modül düzeyinde de tutulur. pageSizeChosen: kullanıcı sayfa boyutunu kendisi seçtiyse ayar varsayılanı ezmez.
export const view = {
  filters: EMPTY_FILTERS as Filters,
  sortBy: 'id' as SortField,
  sortDir: 'asc' as SortDir,
  page: 1,
  pageSize: 25,
  pageSizeChosen: false,
  defaultsLoaded: false,
}

// Ayarlar kaydedilince Patent Listesi bir sonraki açılışta varsayılan sayfa boyutunu yeniden okur.
export function resetListDefaults() {
  view.defaultsLoaded = false
}
