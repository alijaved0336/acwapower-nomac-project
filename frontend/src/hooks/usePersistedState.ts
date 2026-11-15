import { useState, useEffect, useCallback } from "react";

/**
 * Custom hook for managing state that persists to localStorage
 * @param key - The localStorage key to use
 * @param defaultValue - The default value if nothing is stored
 * @returns A tuple of [value, setValue, clearValue]
 */
export function usePersistedState<T>(
  key: string,
  defaultValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  // Initialize state from localStorage or use default
  const [value, setValue] = useState<T>(() => {
    if (typeof window === "undefined") return defaultValue;

    try {
      const stored = localStorage.getItem(key);
      return stored ? (JSON.parse(stored) as T) : defaultValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return defaultValue;
    }
  });

  // Persist to localStorage whenever value changes
  useEffect(() => {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error writing to localStorage key "${key}":`, error);
    }
  }, [key, value]);

  // Clear function to remove the item from localStorage
  const clearValue = useCallback(() => {
    if (typeof window === "undefined") return;

    try {
      localStorage.removeItem(key);
      setValue(defaultValue);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, defaultValue]);

  return [value, setValue, clearValue];
}

/**
 * Custom hook for managing session storage state
 * @param key - The sessionStorage key to use
 * @param defaultValue - The default value if nothing is stored
 * @returns A tuple of [value, setValue, clearValue]
 */
export function useSessionState<T>(
  key: string,
  defaultValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === "undefined") return defaultValue;

    try {
      const stored = sessionStorage.getItem(key);
      return stored ? (JSON.parse(stored) as T) : defaultValue;
    } catch (error) {
      console.error(`Error reading sessionStorage key "${key}":`, error);
      return defaultValue;
    }
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error writing to sessionStorage key "${key}":`, error);
    }
  }, [key, value]);

  const clearValue = useCallback(() => {
    if (typeof window === "undefined") return;

    try {
      sessionStorage.removeItem(key);
      setValue(defaultValue);
    } catch (error) {
      console.error(`Error removing sessionStorage key "${key}":`, error);
    }
  }, [key, defaultValue]);

  return [value, setValue, clearValue];
}
