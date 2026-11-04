import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import Icon from './Icon'

type ShowToast = (message: string) => void
const ToastContext = createContext<ShowToast>(() => {})

export const useToast = () => useContext(ToastContext)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState<string | null>(null)
  const [visible, setVisible] = useState(false)
  const timer = useRef<number>(0)

  const show = useCallback<ShowToast>((text) => {
    window.clearTimeout(timer.current)
    setMessage(text)
    setVisible(true)
    timer.current = window.setTimeout(() => setVisible(false), 3200)
  }, [])

  useEffect(() => () => window.clearTimeout(timer.current), [])

  return (
    <ToastContext.Provider value={show}>
      {children}
      <div
        role="status"
        aria-live="polite"
        className={`pointer-events-none fixed bottom-6 right-6 z-[70] flex max-w-[calc(100vw-3rem)] items-center gap-space-sm rounded-xl border border-indigo-700 bg-indigo-900/90 px-4 py-3 text-sm text-indigo-200 shadow-xl backdrop-blur-md transition-all duration-300 ${
          visible ? 'translate-y-0 opacity-100' : 'translate-y-16 opacity-0'
        }`}
      >
        <Icon name="check_circle" className="text-[20px] text-indigo-200" />
        <span>{message}</span>
      </div>
    </ToastContext.Provider>
  )
}
