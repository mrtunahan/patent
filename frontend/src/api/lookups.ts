import { request } from './client'
import type {
  ApplicantIn,
  ApplicantRead,
  AttorneyFirmIn,
  AttorneyFirmRead,
  DepartmentIn,
  DepartmentRead,
  FsmhTypeIn,
  FsmhTypeRead,
} from './types'

export const listApplicants = (signal?: AbortSignal) => request<ApplicantRead[]>('GET', '/applicants', { signal })
export const listDepartments = (signal?: AbortSignal) => request<DepartmentRead[]>('GET', '/departments', { signal })
export const listFsmhTypes = (signal?: AbortSignal) => request<FsmhTypeRead[]>('GET', '/fsmh_types', { signal })
export const listAttorneyFirms = (signal?: AbortSignal) =>
  request<AttorneyFirmRead[]>('GET', '/attorney_firms', { signal })

// --- yazma uçları (create / update tam değiştirme / remove) ---

export const createApplicant = (body: ApplicantIn) => request<ApplicantRead>('POST', '/applicants', { body })
export const updateApplicant = (id: number, body: ApplicantIn) => request<ApplicantRead>('PUT', `/applicants/${id}`, { body })
export const removeApplicant = (id: number) => request<void>('DELETE', `/applicants/${id}`)

export const createDepartment = (body: DepartmentIn) => request<DepartmentRead>('POST', '/departments', { body })
export const updateDepartment = (id: number, body: DepartmentIn) => request<DepartmentRead>('PUT', `/departments/${id}`, { body })
export const removeDepartment = (id: number) => request<void>('DELETE', `/departments/${id}`)

export const createAttorneyFirm = (body: AttorneyFirmIn) => request<AttorneyFirmRead>('POST', '/attorney_firms', { body })
export const updateAttorneyFirm = (id: number, body: AttorneyFirmIn) =>
  request<AttorneyFirmRead>('PUT', `/attorney_firms/${id}`, { body })
export const removeAttorneyFirm = (id: number) => request<void>('DELETE', `/attorney_firms/${id}`)

export const createFsmhType = (body: FsmhTypeIn) => request<FsmhTypeRead>('POST', '/fsmh_types', { body })
