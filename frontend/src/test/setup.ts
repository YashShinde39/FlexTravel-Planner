import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import { setMediaQueries } from './media'

// jsdom lacks pointer capture, which the bottom sheet (vaul) uses when a drag starts.
Element.prototype.setPointerCapture ??= () => {}
Element.prototype.releasePointerCapture ??= () => {}
Element.prototype.hasPointerCapture ??= () => false

afterEach(() => {
  cleanup()
  setMediaQueries({})
  document.documentElement.className = ''
})
