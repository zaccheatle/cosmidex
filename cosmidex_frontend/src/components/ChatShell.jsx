import { useState } from 'react'
import './ChatShell.css'

// Placeholder chat UI — not wired to a backend yet. Prep for the M7 MCP/RAG chat layer.
function ChatShell() {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')

  return (
    <div className="chat-shell">
      <button
        className="chat-toggle"
        onClick={() => setOpen(o => !o)}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? '✕' : '💬'}
      </button>

      {open && (
        <div className="chat-panel">
          <div className="chat-header">Ask CosmiDex</div>
          <div className="chat-messages">
            <div className="chat-message chat-message-assistant">
              Chat is coming soon — ask me about any exoplanet once this is wired up.
            </div>
          </div>
          <form
            className="chat-input-row"
            onSubmit={e => {
              e.preventDefault()
              setDraft('')
            }}
          >
            <input
              type="text"
              placeholder="Coming soon..."
              value={draft}
              onChange={e => setDraft(e.target.value)}
              disabled
            />
            <button type="submit" disabled>
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default ChatShell
