import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { StammdatenCombobox } from './StammdatenCombobox'

describe('StammdatenCombobox Escape', () => {
  it('verhindert Escape nur solange die Vorschlagsliste offen ist', () => {
    render(
      <StammdatenCombobox
        items={[{ id: 1, label: 'Firma Alpha' }]}
        selectedId={null}
        freitext=""
        onChange={vi.fn()}
      />,
    )
    const input = screen.getByPlaceholderText('Suchen oder frei eingeben…')
    fireEvent.change(input, { target: { value: 'Firma' } })
    expect(screen.getByRole('button', { name: 'Firma Alpha' })).toBeTruthy()

    expect(fireEvent.keyDown(input, { key: 'Escape' })).toBe(false)
    expect(screen.queryByRole('button', { name: 'Firma Alpha' })).toBeNull()
    expect(fireEvent.keyDown(input, { key: 'Escape' })).toBe(true)
  })
})
