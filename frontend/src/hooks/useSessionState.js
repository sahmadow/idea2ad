import { useState, useEffect, useCallback } from 'react'

const SESSION_KEY_PREFIX = 'launchad_'

/**
 * Hook that persists state to sessionStorage
 * @param {string} key - Storage key
 * @param {any} initialValue - Default value if none stored
 * @returns {[any, Function, Function]} - [value, setValue, clearValue]
 */
export function useSessionState(key, initialValue) {
  const storageKey = SESSION_KEY_PREFIX + key

  // Initialize from sessionStorage or use default
  const [value, setValue] = useState(() => {
    try {
      const stored = sessionStorage.getItem(storageKey)
      if (stored !== null) {
        return JSON.parse(stored)
      }
    } catch (e) {
      console.warn(`[useSessionState] Failed to parse ${key}:`, e)
    }
    return initialValue
  })

  // Persist to sessionStorage on change
  useEffect(() => {
    try {
      if (value === null || value === undefined) {
        sessionStorage.removeItem(storageKey)
      } else {
        sessionStorage.setItem(storageKey, JSON.stringify(value))
      }
    } catch (e) {
      console.warn(`[useSessionState] Failed to save ${key}:`, e)
    }
  }, [storageKey, value])

  // Clear function
  const clearValue = useCallback(() => {
    sessionStorage.removeItem(storageKey)
    setValue(initialValue)
  }, [storageKey, initialValue])

  return [value, setValue, clearValue]
}

/**
 * Clear all LaunchAd session state
 */
export function clearAllSessionState() {
  const keysToRemove = []
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i)
    if (key?.startsWith(SESSION_KEY_PREFIX)) {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach(key => sessionStorage.removeItem(key))
  // Also clear fb_session from localStorage on full clear
  localStorage.removeItem('fb_session')
}

export default useSessionState
