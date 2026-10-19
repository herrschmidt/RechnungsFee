import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { DateInput } from './DateInput'

describe('DateInput Escape', () => {
  it('markiert Escape bei offenem Kalender, schließt ihn und lässt geschlossenes Escape unverändert', () => {
    render(<DateInput value="2026-10-18" onChange={vi.fn()} />)
    const input = screen.getByPlaceholderText('TT.MM.JJJJ')

    fireEvent.click(screen.getByTitle('Kalender öffnen'))
    expect(screen.getByText(/Oktober 2026/)).toBeTruthy()
    expect(fireEvent.keyDown(input, { key: 'Escape' })).toBe(false)
    expect(screen.queryByText(/Oktober 2026/)).toBeNull()

    expect(fireEvent.keyDown(input, { key: 'Escape' })).toBe(true)
  })
})
