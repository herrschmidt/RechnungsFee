import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'

// Wiederverwendbare Modal-Basis für alle Dialog-Overlays.
// Setzt die Barrierefreiheits-Pflichtpunkte der Roadmap zentral um:
// - role="dialog" + aria-modal="true" + aria-labelledby auf den Titel
// - Initial Focus beim Öffnen (erster fokussierbarer Inhalt; ein `autoFocus`
//   im Inhalt gewinnt, wenn vorhanden)
// - Focus-Trap: Tab/Shift+Tab bleiben innerhalb des offenen Modals
// - Esc ruft onClose
// - Fokus wird beim Schließen auf das vorher aktive Element zurückgesetzt

const FOKUSSIERBAR =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

function fokussierbareElemente(wurzel: HTMLElement): HTMLElement[] {
  return Array.from(wurzel.querySelectorAll<HTMLElement>(FOKUSSIERBAR)).filter(
    (el) => el.tabIndex >= 0 && !el.closest('[hidden], [aria-hidden="true"]'),
  )
}

interface ModalProps {
  /** Titel des Dialogs – wird über aria-labelledby mit dem Panel verknüpft. */
  title: ReactNode
  onClose: () => void
  children: ReactNode
  /** Klassen des Panel-Divs (Inhalt), z. B. Breite/Padding. */
  panelClassName?: string
  /** Klassen des Overlay-Divs (Hintergrund), z. B. Polsterung. */
  overlayClassName?: string
  /** Klick auf den Hintergrund schließen? (Standard: ja, wie bisher üblich) */
  klickZumSchliessen?: boolean
}

export function Modal({
  title,
  onClose,
  children,
  panelClassName = '',
  overlayClassName = '',
  klickZumSchliessen = true,
}: ModalProps) {
  const titelId = useId()
  const panelRef = useRef<HTMLDivElement>(null)
  const vorherigesElementRef = useRef(document.activeElement as HTMLElement | null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    const panel = panelRef.current

    // Initial Focus: ein autoFocus im Inhalt hat bereits gewonnen – sonst
    // erstes fokussierbares Element im Panel setzen.
    if (panel && !panel.contains(document.activeElement)) {
      fokussierbareElemente(panel)[0]?.focus()
    }

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        if (e.defaultPrevented) return
        e.stopPropagation()
        onCloseRef.current()
        return
      }
      if (e.key !== 'Tab' || !panel) return
      const elements = fokussierbareElemente(panel)
      if (elements.length === 0) return
      const erstes = elements[0]
      const letztes = elements[elements.length - 1]
      if (!panel.contains(document.activeElement)) {
        e.preventDefault()
        ;(e.shiftKey ? letztes : erstes).focus()
        return
      }
      const aktive = document.activeElement as HTMLElement
      if (e.shiftKey ? aktive === erstes : aktive === letztes) {
        e.preventDefault()
        ;(e.shiftKey ? letztes : erstes).focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      vorherigesElementRef.current?.focus?.()
    }
  }, [])

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 ${overlayClassName}`}
      onClick={klickZumSchliessen ? onClose : undefined}
    >
      <div
        ref={panelRef}
        data-testid="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titelId}
        className={panelClassName}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id={titelId} className="font-semibold text-slate-800 dark:text-slate-100 mb-4">
          {title}
        </h3>
        {children}
      </div>
    </div>
  )
}
