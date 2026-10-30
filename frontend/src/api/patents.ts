import { request, type Query } from './client'
import type { Page, PatentIn, PatentListParams, PatentRead } from './types'

export function listPatents(params: PatentListParams, signal?: AbortSignal) {
  return request<Page<PatentRead>>('GET', '/patents', { query: params as Query, signal })
}

export function getPatent(id: number, signal?: AbortSignal) {
  return request<PatentRead>('GET', `/patents/${id}`, { signal })
}

export function createPatent(body: PatentIn, confirmDuplicate = false) {
  return request<PatentRead>('POST', '/patents', {
    body,
    query: { confirm_duplicate: confirmDuplicate ? true : undefined },
  })
}

export function updatePatent(id: number, body: PatentIn, confirmDuplicate = false) {
  return request<PatentRead>('PUT', `/patents/${id}`, {
    body,
    query: { confirm_duplicate: confirmDuplicate ? true : undefined },
  })
}

export function removePatent(id: number) {
  return request<void>('DELETE', `/patents/${id}`)
}
