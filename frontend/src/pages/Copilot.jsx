import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api.js'

const QUICK_ACTIONS = [
  'What needs follow-up?',
  "Show today's priorities",
  'Show the pipeline',
  'Run lead scoring',
  'Run a goal check',
  'Show approvals',
]

const WELCOME = {
  role: 'copilot',
  reply: "I'm your Founder Copilot. I read live data and run real actions — scoring, goals, Hermes cycles. Ask me something, or tap a suggestion below.",
  items: [],
}

export default function Copilot() {
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const message = (text || input).trim()
    if (!message || busy) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', reply: message }])
    setBusy(true)
    try {
      const res = await api.post('/api/v1/copilot/chat', { message })
      setMessages(prev => [...prev, { role: 'copilot', ...res.data }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'copilot',
        reply: 'I could not reach the backend. Is the API running on port 8000?',
        items: [],
      }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto' }}>
      <h1>Copilot</h1>

      <div className="card" style={{
        display: 'flex', flexDirection: 'column',
        height: '62vh', minHeight: '420px', padding: '1.25rem',
      }}>
        <div style={{ flex: 1, overflowY: 'auto', display: 'grid', gap: '0.9rem', alignContent: 'start' }}>
          {messages.map((m, i) => (
            <div key={i} style={{
              justifySelf: m.role === 'user' ? 'end' : 'start',
              maxWidth: '85%',
            }}>
              <div style={{
                backgroundColor: m.role === 'user' ? '#667eea' : '#f4f4f6',
                color: m.role === 'user' ? 'white' : '#222',
                padding: '0.7rem 1rem',
                borderRadius: m.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                lineHeight: 1.5,
              }}>
                {m.reply}
              </div>
              {m.items?.length > 0 && (
                <div style={{ display: 'grid', gap: '0.4rem', marginTop: '0.5rem' }}>
                  {m.items.map((item, j) => (
                    <Link key={j} to={item.link || '#'} style={{
                      textDecoration: 'none', color: 'inherit',
                      display: 'block', padding: '0.6rem 0.9rem',
                      backgroundColor: 'white', border: '1px solid #e4e4e8',
                      borderRadius: '8px',
                    }}>
                      <div style={{ fontWeight: 600, fontSize: '0.92rem' }}>{item.title}</div>
                      {item.subtitle && (
                        <div style={{ color: '#888', fontSize: '0.83rem', marginTop: '0.15rem' }}>
                          {item.subtitle}
                        </div>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
          {busy && (
            <div style={{
              justifySelf: 'start', backgroundColor: '#f4f4f6', color: '#999',
              padding: '0.7rem 1rem', borderRadius: '14px 14px 14px 4px',
            }}>
              thinking…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', margin: '0.9rem 0' }}>
          {QUICK_ACTIONS.map(qa => (
            <button key={qa} className="btn btn-secondary" disabled={busy}
              style={{ padding: '0.35rem 0.75rem', fontSize: '0.83rem' }}
              onClick={() => send(qa)}>
              {qa}
            </button>
          ))}
        </div>

        <form style={{ display: 'flex', gap: '0.6rem' }}
          onSubmit={e => { e.preventDefault(); send() }}>
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder='Ask anything — e.g. "create a goal: 20 qualified leads"'
            autoFocus
            style={{
              flex: 1, padding: '0.75rem 1rem',
              border: '1px solid #ddd', borderRadius: '8px', fontSize: '1rem',
            }}
          />
          <button type="submit" className="btn btn-primary" disabled={busy || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
