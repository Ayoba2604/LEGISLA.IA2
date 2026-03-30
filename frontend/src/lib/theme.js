import { useCallback, useEffect, useState } from 'react'

const THEME_KEY = 'theme'
const THEME_EVENT = 'legisla-theme-change'

export function readTheme() {
  if (typeof window === 'undefined') return 'light'
  return window.localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light'
}

export function applyTheme(nextTheme) {
  const resolvedTheme = nextTheme === 'dark' ? 'dark' : 'light'

  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', resolvedTheme)
  }

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(THEME_KEY, resolvedTheme)
    window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: resolvedTheme }))
  }

  return resolvedTheme
}

export function useThemePreference() {
  const [theme, setThemeState] = useState(() => applyTheme(readTheme()))

  useEffect(() => {
    if (typeof window === 'undefined') return undefined

    const syncTheme = (event) => {
      setThemeState(event?.detail || readTheme())
    }

    const syncStorage = (event) => {
      if (!event.key || event.key === THEME_KEY) {
        setThemeState(readTheme())
      }
    }

    window.addEventListener(THEME_EVENT, syncTheme)
    window.addEventListener('storage', syncStorage)

    return () => {
      window.removeEventListener(THEME_EVENT, syncTheme)
      window.removeEventListener('storage', syncStorage)
    }
  }, [])

  const setTheme = useCallback((nextTheme) => {
    setThemeState(applyTheme(typeof nextTheme === 'function' ? nextTheme(readTheme()) : nextTheme))
  }, [])

  return [theme, setTheme]
}
