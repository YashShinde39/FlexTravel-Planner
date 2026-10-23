import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { setMediaQueries } from './media'

// jsdom lacks pointer capture, which the bottom sheet (vaul) uses when a drag starts.
Element.prototype.setPointerCapture ??= () => {}
Element.prototype.releasePointerCapture ??= () => {}
Element.prototype.hasPointerCapture ??= () => false

afterEach(() => {
  cleanup()
  vi.restoreAllMocks() // e.g. the fetch spy from mockApi
  setMediaQueries({})
  document.documentElement.className = ''
})
