import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

function timeAgo(iso) {
  if (!iso) return ''
  const hasTimezone = /Z$|[+-]\d{2}:\d{2}$/.test(iso)
  const seconds = Math.floor((Date.now() - new Date(hasTimezone ? iso : iso + 'Z')) / 1000)
  if (Number.isNaN(seconds)) return iso.slice(0, 19).replace('T', ' ')
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export default function Approvals() {
  const [pending, setPending] = useState([])
  const [history, setHistory] = useState([])
  const [busy, setBusy] = useState(null) // request id being decided
  const [offline, setOffline] = useState(false)

  const load = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/approvals', { params: { limit: 100 } })
      const all = res.data.requests || []
      setPending(all.filter(r => r.status === 'pending'))
      setHistory(all.filter(r => r.status !== 'pending').slice(0, 20))
      setOffline(false)
    } catch {
      setOffline(true)
    }
  }, [])

  useEffect(() => {
    load()
    const timer = setInterval(load, 15000)
    return () => clearInterval(timer)
  }, [load])

  const decideRequest = async (id, action) => {
    setBusy(id)
    try {
      await api.post(`/api/v1/approvals/${id}/${action}`, { decided_by: 'user' })
      await load()
    } finally {
      setBusy(null)
    }
  }

  return (
    <div>
      <h1>Approvals Inbox</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Risky autonomous actions wait here for your sign-off. Approving executes
        the action; rejecting archives it. Nothing runs without a decision.
      </p>

      {offline && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>
          Backend offline — start the API on port 8000
        </div>
      )}

      <div className="card">
        <h2 className="card-title">
          Pending {pending.length > 0 && <span className="badge badge-warning">{pending.length}</span>}
        </h2>
        {pending.length === 0 ? (
          <div className="empty-state">
            <h3>Inbox zero</h3>
            <p>When Hermes proposes something risky (like sending an email), it appears here.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {pending.map(r => (
              <div key={r.id} style={{
                padding: '1.25rem', backgroundColor: '#fffdf5',
                border: '1px solid #f0e6c8', borderRadius: '8px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                  <div style={{ flex: 1, minWidth: '250px' }}>
                    <div style={{ marginBottom: '0.4rem' }}>
                      <strong style={{ fontSize: '1.05rem' }}>{r.title}</strong>
                    </div>
                    <div style={{ color: '#666', fontSize: '0.9rem', marginBottom: '0.4rem' }}>
                      {r.description}
                    </div>
                    <div style={{ color: '#999', fontSize: '0.85rem' }}>
                      requested by <strong>{r.requested_by}</strong> · {r.action_type} · {timeAgo(r.created_at)}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <button
                      className="btn"
                      style={{ backgroundColor: '#06A77D', color: 'white' }}
                      disabled={busy === r.id}
                      onClick={() => decideRequest(r.id, 'approve')}
                    >
                      {busy === r.id ? '…' : '✓ Approve'}
                    </button>
                    <button
                      className="btn"
                      style={{ backgroundColor: '#D62828', color: 'white' }}
                      disabled={busy === r.id}
                      onClick={() => decideRequest(r.id, 'reject')}
                    >
                      ✕ Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="card-title">Recent Decisions</h2>
        {history.length === 0 ? (
          <p style={{ color: '#999' }}>No decisions yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Request</th><th>Decision</th><th>By</th><th>Outcome</th><th>When</th></tr>
            </thead>
            <tbody>
              {history.map(r => (
                <tr key={r.id}>
                  <td><strong>{r.title}</strong></td>
                  <td>
                    <span className={`badge ${r.status === 'approved' ? 'badge-success' : 'badge-danger'}`}>
                      {r.status}
                    </span>
                  </td>
                  <td>{r.decided_by || '—'}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.execution_result ? JSON.stringify(r.execution_result) : '—'}
                  </td>
                  <td style={{ whiteSpace: 'nowrap' }}>{timeAgo(r.decided_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
