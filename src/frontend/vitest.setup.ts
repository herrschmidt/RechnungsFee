import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Testing-Library räumt nach jedem Test das DOM auf.
afterEach(() => cleanup())
