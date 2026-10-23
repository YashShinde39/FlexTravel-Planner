import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { setMediaQueries } from './media'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks() // e.g. the fetch spy from mockApi
  setMediaQueries({})
  document.documentElement.className = ''
})
