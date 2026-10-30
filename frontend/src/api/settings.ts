import { request } from './client'
import type { Settings } from './types'

export const getSettings = (signal?: AbortSignal) => request<Settings>('GET', '/settings', { signal })
export const saveSettings = (values: Settings) => request<Settings>('PUT', '/settings', { body: values })
