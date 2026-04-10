import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import './Tooltip.css'

function Tooltip({ text }) {
  const [visible, setVisible] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const iconRef = useRef(null)
  const tooltipRef = useRef(null)

  const handleMouseEnter = () => {
    const rect = iconRef.current.getBoundingClientRect()
    setPosition({
      top: rect.top,
      left: rect.right + 8
    })
    setVisible(true)
  }

  useEffect(() => {
    if (visible && tooltipRef.current) {
      const tooltipRect = tooltipRef.current.getBoundingClientRect()
      const viewportHeight = window.innerHeight
      const viewportWidth = window.innerWidth
      const iconRect = iconRef.current.getBoundingClientRect()

      let top = iconRect.top
      let left = iconRect.right + 8

      // flip left if going off right edge
      if (left + tooltipRect.width > viewportWidth) {
        left = iconRect.left - tooltipRect.width - 8
      }

      // clamp bottom
      if (top + tooltipRect.height > viewportHeight - 8) {
        top = viewportHeight - tooltipRect.height - 8
      }

      // clamp top
      if (top < 8) {
        top = 8
      }

      setPosition({ top, left })
    }
  }, [visible])

  return (
    <span className="tooltip-wrapper">
      <span
        ref={iconRef}
        className="tooltip-icon"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setVisible(false)}
      >
        i
      </span>
      {visible && createPortal(
        <span
          ref={tooltipRef}
          className="tooltip-box"
          style={{ top: position.top, left: position.left }}
        >
          {text}
        </span>,
        document.body
      )}
    </span>
  )
}

export default Tooltip