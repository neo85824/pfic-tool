import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api' })

export default api

// ── Types ────────────────────────────────────────────────────────────────────

export interface Client {
  id: string
  client_code: string
  tax_year_start?: number
  notes?: string
}

export interface Holding {
  id: string
  pfic_name: string
  reference_id?: string
  share_class?: string
  currency: string
  method: string
  first_pfic_year?: number
}

export interface Transaction {
  id: string
  txn_date: string
  txn_type: string
  units?: number
  total_value_usd: number
  notes?: string
}

export interface CalculationSummary {
  id: string
  tax_year: number
  method: string
  status: string
  engine_version?: string
  total_excess_dist?: number
  additional_tax?: number
  total_interest?: number
  ordinary_income?: number
  grand_total?: number
  warnings: string[]
}

export interface CalculationDetail extends CalculationSummary {
  full_result: Record<string, unknown>
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, password: string) =>
    api.post<{ access_token: string }>('/auth/register', { email, password }),
  login: (email: string, password: string) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post<{ access_token: string }>('/auth/login', form)
  },
}

// ── Clients ──────────────────────────────────────────────────────────────────

export const clientsApi = {
  list: () => api.get<Client[]>('/clients/'),
  create: (data: Partial<Client>) => api.post<Client>('/clients/', data),
  get: (id: string) => api.get<Client>(`/clients/${id}`),
  update: (id: string, data: Partial<Client>) => api.patch<Client>(`/clients/${id}`, data),
  delete: (id: string) => api.delete(`/clients/${id}`),
}

// ── Holdings ─────────────────────────────────────────────────────────────────

export const holdingsApi = {
  list: (clientId: string) => api.get<Holding[]>(`/clients/${clientId}/holdings/`),
  create: (clientId: string, data: Partial<Holding>) =>
    api.post<Holding>(`/clients/${clientId}/holdings/`, data),
  update: (clientId: string, holdingId: string, data: Partial<Holding>) =>
    api.patch<Holding>(`/clients/${clientId}/holdings/${holdingId}`, data),
  delete: (clientId: string, holdingId: string) =>
    api.delete(`/clients/${clientId}/holdings/${holdingId}`),
}

// ── Transactions ─────────────────────────────────────────────────────────────

export const txnsApi = {
  list: (holdingId: string) => api.get<Transaction[]>(`/holdings/${holdingId}/transactions/`),
  create: (holdingId: string, data: Partial<Transaction>) =>
    api.post<Transaction>(`/holdings/${holdingId}/transactions/`, data),
  delete: (holdingId: string, txnId: string) =>
    api.delete(`/holdings/${holdingId}/transactions/${txnId}`),
  importCsv: (holdingId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/holdings/${holdingId}/transactions/csv-import`, form)
  },
  previewCsv: (holdingId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/holdings/${holdingId}/transactions/csv-preview`, form)
  },
}

// ── Holding context (name + client) ──────────────────────────────────────────

export interface HoldingContext {
  pfic_name: string
  client_code: string
}

export const holdingContextApi = {
  get: (holdingId: string) => api.get<HoldingContext>(`/holdings/${holdingId}/info`),
}

// ── Calculations ─────────────────────────────────────────────────────────────

export const calcApi = {
  run: (holdingId: string, taxYear: number, interestEndDate?: string) =>
    api.post<CalculationDetail>(`/holdings/${holdingId}/calculate`, {
      tax_year: taxYear,
      ...(interestEndDate ? { interest_end_date: interestEndDate } : {}),
    }),
  list: (holdingId: string) =>
    api.get<CalculationSummary[]>(`/holdings/${holdingId}/calculations`),
  get: (holdingId: string, taxYear: number) =>
    api.get<CalculationDetail>(`/holdings/${holdingId}/calculations/${taxYear}`),
}

// ── Exports ──────────────────────────────────────────────────────────────────

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export const exportUrl = (holdingId: string, taxYear: number, type: 'pdf' | 'line16a' | 'excel') =>
  `${API_BASE}/holdings/${holdingId}/calculations/${taxYear}/export/${type}`
