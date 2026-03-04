import { useState, useCallback } from 'react'

interface UseCounterReturn {
  count: number
  increment: () => void
  decrement: () => void
  reset: () => void
  set: (value: number) => void
}

export function useCounter(initialValue = 0): UseCounterReturn {
  const [count, setCount] = useState(initialValue)

  const increment = useCallback(() => {
    setCount((prev) => prev + 1)
  }, [])

  const decrement = useCallback(() => {
    setCount((prev) => prev - 1)
  }, [])

  const reset = useCallback(() => {
    setCount(initialValue)
  }, [initialValue])

  const set = useCallback((value: number) => {
    setCount(value)
  }, [])

  return {
    count,
    increment,
    decrement,
    reset,
    set,
  }
}

