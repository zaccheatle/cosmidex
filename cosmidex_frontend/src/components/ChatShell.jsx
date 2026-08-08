import { useState } from 'react'
import { apiFetch } from '../api'
import './ChatShell.css'

/**
 * Placeholder chat UI (the "Cosmo" assistant) — not wired to a backend yet.
 * Prep for the M7 MCP/RAG chat layer; input and send are disabled until then.
 *
 * @returns The floating chat toggle button and its expandable panel.
 */
function ChatShell() {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  return (
    <div className="chat-shell">
      <button
        className="chat-toggle"
        onClick={() => setOpen(o => !o)}
        aria-label={open ? 'Close Cosmo chat' : 'Open Cosmo chat'}
      >
        {open ? '✕' : '💬'}
      </button>

      {open && (
        <div className="chat-panel">
          <div className="chat-header">🌌 Ask Cosmo</div>
          <div className="chat-messages">
              <div className="chat-message chat-message-assistant">
                  🌌 Hi, I'm Cosmo! Ask me about any exoplanet!
              </div>
              {messages.map((message, index) => (
                  <div key={index} className={`chat-message chat-message-${message.role}`}>
                      {message.text}
                  </div>
              ))}
              {loading && (
                <div className="chat-message chat-message-assistant">
                  Pondering...
                </div>
              )}
          </div>
          <form
              className="chat-input-row"
              onSubmit={e => {
                  e.preventDefault()
                  const userMessage = draft
                  setMessages(prevMessages => [...prevMessages, { role: 'user', text: userMessage }])
                  setDraft('')
                  setLoading(true)

                  apiFetch('/chat', { method: 'POST', body: { message: userMessage } })
                      .then(response => {
                          setMessages(prevMessages => [...prevMessages, { role: 'assistant', text: response }])
                      })
                      .catch(err => {
                          setMessages(prevMessages => [...prevMessages, { role: 'assistant', text: `Sorry, something went wrong: ${err.message}` }])
                      })
                      .finally(() => {
                          setLoading(false)
                      })
              }}
          >
            <input
              type="text"
              placeholder="Ask Cosmo..."
              value={draft}
              onChange={e => setDraft(e.target.value)}
            />
            <button type="submit">
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default ChatShell
