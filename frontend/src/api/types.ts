// Backend şemalarıyla (backend/app/schemas) birebir tipler.

export interface IdName {
  id: number
  name: string
}

export interface ApplicantRef {
  id: number
  full_name: string
}

export interface PatentRead {
  id: number
  title: string
  applicant: ApplicantRef
  department: IdName | null
  fsmh_type: IdName
  attorney_firm: IdName | null
  partners: string[]
  application_date: string | null // ISO YYYY-MM-DD
  notes: string | null
  created_at: string
  updated_at: string
}

export interface PatentIn {
  title: string
  applicant_id: number
  fsmh_type_id: number
  department_id: number | null
  attorney_firm_id: number | null
  application_date: string | null
  notes: string | null
  partners: string[]
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ApplicantRead {
  id: number
  full_name: string
  department_id: number | null
  email: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DepartmentRead {
  id: number
  name: string
  created_at: string
  updated_at: string
}

export interface FsmhTypeRead {
  id: number
  name: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface AttorneyFirmRead {
  id: number
  name: string
  contact_info: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export type SortField =
  | 'id'
  | 'title'
  | 'applicant'
  | 'department'
  | 'fsmh_type'
  | 'attorney_firm'
  | 'application_date'
  | 'created_at'
export type SortDir = 'asc' | 'desc'

export type PatentListParams = {
  q?: string
  applicant_id?: number
  department_id?: number
  fsmh_type_id?: number
  attorney_firm_id?: number
  date_from?: string
  date_to?: string
  has_attorney?: boolean
  sort_by?: SortField
  sort_dir?: SortDir
  page?: number
  page_size?: number
}

export interface Lookups {
  applicants: ApplicantRead[]
  departments: DepartmentRead[]
  fsmhTypes: FsmhTypeRead[]
  attorneyFirms: AttorneyFirmRead[]
}
