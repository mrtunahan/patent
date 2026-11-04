import { API_BASE } from './config'

type QueryValue = string | number | boolean | null | undefined
export type Query = Record<string, QueryValue>

export class ApiError extends Error {
  status: number
  detail: string
  duplicate: boolean
  existingIds: number[]
  fieldErrors: Record<string, string>

  constructor(
    status: number,
    detail: string,
    extra: { duplicate?: boolean; existingIds?: number[]; fieldErrors?: Record<string, string> } = {},
  ) {
    super(detail)
    this.status = status
    this.detail = detail
    this.duplicate = extra.duplicate ?? false
    this.existingIds = extra.existingIds ?? []
    this.fieldErrors = extra.fieldErrors ?? {}
  }
}

export function buildUrl(path: string, query?: Query): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  }
  const qs = params.toString()
  return `${API_BASE}${path}${qs ? `?${qs}` : ''}`
}

interface ValidationItem {
  type?: string
  loc?: (string | number)[]
  msg?: string
  ctx?: { max_length?: number }
}

function translateValidation(item: ValidationItem): string {
  switch (item.type) {
    case 'missing':
      return 'Bu alan zorunludur.'
    case 'string_too_short':
      return 'Bu alan boş olamaz.'
    case 'string_too_long':
      return `En fazla ${item.ctx?.max_length ?? ''} karakter olabilir.`.replace('  ', ' ')
    case 'extra_forbidden':
      return 'Tanınmayan alan.'
    case 'date_from_datetime_parsing':
    case 'date_parsing':
    case 'date_type':
      return 'Geçerli bir tarih girin.'
    default:
      return 'Geçersiz değer.'
  }
}

// Ana sisteme (Offline Asistan) gömülü çalışırken yetki kapısı ve proxy yanıtları JSON gövdesi taşımaz.
const GATEWAY_MESSAGES: Record<number, string> = {
  401: 'Oturum bulunamadı. Offline Asistan üzerinden yeniden giriş yapın.',
  403: 'Bu ekran için Patent & FSMH yöneticisi yetkisi gerekir.',
  502: 'Patent Takip sunucusuna ulaşılamadı.',
  503: 'Patent Takip sunucusu şu an hizmet veremiyor.',
  504: 'Patent Takip sunucusu zamanında yanıt vermedi.',
}

function toApiError(status: number, data: unknown): ApiError {
  const body = (data && typeof data === 'object' ? data : {}) as Record<string, unknown>
  const detail = body.detail
  if (body.duplicate === true) {
    const ids = Array.isArray(body.existing_ids) ? (body.existing_ids as number[]) : []
    return new ApiError(status, typeof detail === 'string' ? detail : 'Mükerrer kayıt.', {
      duplicate: true,
      existingIds: ids,
    })
  }
  if (typeof detail === 'string') return new ApiError(status, detail)
  if (Array.isArray(detail)) {
    const fieldErrors: Record<string, string> = {}
    for (const raw of detail as ValidationItem[]) {
      const loc = raw.loc ?? []
      const field = String(loc[0] === 'body' ? (loc[1] ?? '') : (loc[loc.length - 1] ?? ''))
      if (field && !fieldErrors[field]) fieldErrors[field] = translateValidation(raw)
    }
    return new ApiError(status, 'Girilen bilgilerde hata var. Lütfen alanları kontrol edin.', { fieldErrors })
  }
  if (GATEWAY_MESSAGES[status]) return new ApiError(status, GATEWAY_MESSAGES[status])
  return new ApiError(status, `Beklenmeyen bir hata oluştu (HTTP ${status}).`)
}

export async function request<T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  path: string,
  options: { query?: Query; body?: unknown; signal?: AbortSignal } = {},
): Promise<T> {
  const { query, body, signal } = options
  let response: Response
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'Sunucuya ulaşılamadı.')
  }
  if (response.status === 204) return undefined as T
  let data: unknown = null
  try {
    data = await response.json()
  } catch {
    data = null
  }
  if (!response.ok) throw toApiError(response.status, data)
  return data as T
}

export function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

// Dosya indirme (xlsx): hata yanıtları JSON olarak ApiError'a çevrilir. Dosya adı Content-Disposition'dan gelir.
export async function download(path: string, query?: Query): Promise<{ blob: Blob; filename: string | null }> {
  let response: Response
  try {
    response = await fetch(buildUrl(path, query))
  } catch {
    throw new ApiError(0, 'Sunucuya ulaşılamadı.')
  }
  if (!response.ok) {
    let data: unknown = null
    try {
      data = await response.json()
    } catch {
      data = null
    }
    throw toApiError(response.status, data)
  }
  const match = /filename="?([^";]+)"?/.exec(response.headers.get('Content-Disposition') ?? '')
  return { blob: await response.blob(), filename: match ? match[1] : null }
}
