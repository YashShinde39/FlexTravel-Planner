import { renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { setMediaQueries } from '@/test/media'
import { useColorScheme } from './use-color-scheme'

describe('useColorScheme', () => {
  it('uses the dark theme when the device prefers dark', () => {
    setMediaQueries({ '(prefers-color-scheme: dark)': true })

    const { result } = renderHook(() => useColorScheme())

    expect(result.current).toBe('dark')
    expect(document.documentElement).toHaveClass('dark')
  })

  it('uses the light theme otherwise', () => {
    document.documentElement.classList.add('dark')

    const { result } = renderHook(() => useColorScheme())

    expect(result.current).toBe('light')
    expect(document.documentElement).not.toHaveClass('dark')
  })
})
