import { request } from './client'
import type { ApplicantRead, AttorneyFirmRead, DepartmentRead, FsmhTypeRead } from './types'

export const listApplicants = (signal?: AbortSignal) => request<ApplicantRead[]>('GET', '/applicants', { signal })
export const listDepartments = (signal?: AbortSignal) => request<DepartmentRead[]>('GET', '/departments', { signal })
export const listFsmhTypes = (signal?: AbortSignal) => request<FsmhTypeRead[]>('GET', '/fsmh_types', { signal })
export const listAttorneyFirms = (signal?: AbortSignal) =>
  request<AttorneyFirmRead[]>('GET', '/attorney_firms', { signal })
