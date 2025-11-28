import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface AuthState {
  token: string | null
  admin: {
    id: number
    username: string
    email?: string
    role?: string
  } | null
  isAuthenticated: boolean
  setAuth: (token: string, admin: any) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      admin: null,
      isAuthenticated: false,
      setAuth: (token, admin) => {
        set({ token, admin, isAuthenticated: true })
      },
      clearAuth: () => {
        set({ token: null, admin: null, isAuthenticated: false })
      },
    }),
    {
      name: 'admin-auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

