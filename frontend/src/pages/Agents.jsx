import React, { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import api from '../api.js'

const TYPE_COLORS = {
  operations: '#00B4D8', sales_manager: '#9B5DE5', custom: '#667eea',
  sdr: '#06A77D', csm: '#FFB800', finance: '#D62828', product: '#00D4FF',
}

function fmt(iso) {
  if (!iso) return 'never'
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function Agents() {
  const [agents, setAgents] = useState([])
  const [approvals, setApprovals] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)
  const [busy, setBusy] = useState(false)
  const [messageForm, setMessageForm] = useState({ to_agent: '', message: '' })

  const load = useCallback(async () => {
    try {
      const [agentsRes, approvalsRes] = await Promise.all([
        api.get('/api/v1/agents/registry'),
        api.get('/api/v1/approvals'),
      ])
      setAgents(agentsRes.data.agents || [])
      setApprovals(approvalsRes.data.requests || approvalsRes.data.approvals || [])
      setOffline(false)
    } catch {
      setOffline(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const openAgent = async (agent) => {
    setSelected(agent.name)
    setMessageForm({ to_agent: '', message: '' })
    try {
      const [detailRes, goalsRes] = await Promise.all([
        api.get(`/api/v1/agents/registry/${agent.name}/messages`),
        api.get('/api/v1/hermes/goals', { params: { agent_name: agent.name } }),
      ])
      setDetail(detailRes.data.messages || [])
      setGoals(goalsRes.data.goals || [])
    } catch {
      setDetail([])
      setGoals([])
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!selected || !messageForm.to_agent || !messageForm.message.trim()) return
    setBusy(true)
    try {
      await api.post(`/api/v1/agents/registry/${selected}/messages`, {
        to_agent: messageForm.to_agent,
        message: messageForm.message,
      })
      setMessageForm({ to_agent: '', message: '' })
      const agent = agents.find(a => a.name === selected)
      if (agent) await openAgent(agent)
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <div className="loading">Loading agents…</div>

  const selectedAgent = agents.find(a => a.name === selected)
  const selectedApprovals = selected ? approvals.filter(r => r.requested_by === selected) : []

  return (
    <div>
      <h1>Agents</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Every autonomous subsystem the platform runs, registered with its
        capabilities. Messages below are real inter-agent handoffs — e.g.
        Hermes tells Copilot when it proposes an outreach approval.
      </p>

      {offline && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>
          Backend offline — start the API on port 8000
        </div>
      )}

      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className="stat-label">Registered Agents</div>
          <div className="stat-number">{agents.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active</div>
          <div className="stat-number">{agents.filter(a => a.status === 'active').length}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
        <div className="card">
          <h2 className="card-title">Registry ({agents.length})</h2>
          {agents.length === 0 ? (
            <div className="empty-state">
              <h3>No agents registered</h3>
              <p>Platform subsystems register themselves on startup.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {agents.map(a => (
                <div key={a.name}
                  onClick={() => openAgent(a)}
                  style={{
                    border: selected === a.name ? '2px solid #667eea' : '1px solid #eee',
                    borderRadius: '8px', padding: '1rem', cursor: 'pointer',
                    backgroundColor: selected === a.name ? '#f5f6ff' : 'white',
                  }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ textTransform: 'capitalize' }}>{a.name.replace(/_/g, ' ')}</strong>
                    <span style={{
                      backgroundColor: TYPE_COLORS[a.type] || '#999', color: 'white',
                      padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem',
                    }}>
                      {a.type}
                    </span>
                  </div>
                  {a.description && <p style={{ color: '#666', fontSize: '0.85rem', margin: '0.4rem 0' }}>{a.description}</p>}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', margin: '0.5rem 0' }}>
                    {(a.capabilities || []).map(c => (
                      <span key={c} style={{
                        fontSize: '0.75rem', color: '#667eea', backgroundColor: '#eef0ff',
                        padding: '0.15rem 0.5rem', borderRadius: '10px',
                      }}>
                        {c}
                      </span>
                    ))}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#999' }}>
                    <span className={`badge ${a.status === 'active' ? 'badge-success' : 'badge-warning'}`}>{a.status}</span>
                    {' '}· last active {fmt(a.last_active_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selected && selectedAgent && (
          <div className="card">
            <h2 className="card-title" style={{ textTransform: 'capitalize' }}>{selected.replace(/_/g, ' ')} — Detail</h2>

            <h3 style={{ fontSize: '0.95rem', marginTop: '1rem' }}>Inbox ({detail?.length || 0})</h3>
            {!detail || detail.length === 0 ? (
              <p style={{ color: '#999', fontSize: '0.9rem' }}>No messages yet.</p>
            ) : (
              <div style={{ display: 'grid', gap: '0.5rem', marginBottom: '1rem' }}>
                {detail.slice().reverse().map((m, i) => (
                  <div key={i} style={{ border: '1px solid #eee', borderRadius: '6px', padding: '0.6rem 0.8rem', fontSize: '0.85rem' }}>
                    <div><strong>from {m.from}</strong> <span style={{ color: '#999' }}>· {fmt(m.timestamp)}</span></div>
                    <div style={{ color: '#444', marginTop: '0.2rem' }}>{m.message}</div>
                  </div>
                ))}
              </div>
            )}

            <form onSubmit={sendMessage} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
              <select value={messageForm.to_agent}
                onChange={e => setMessageForm({ ...messageForm, to_agent: e.target.value })}
                style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                <option value="">Send to…</option>
                {agents.filter(a => a.name !== selected).map(a => (
                  <option key={a.name} value={a.name}>{a.name}</option>
                ))}
              </select>
              <input type="text" placeholder="Message" value={messageForm.message}
                onChange={e => setMessageForm({ ...messageForm, message: e.target.value })}
                style={{ flex: 1, padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
              <button type="submit" className="btn btn-primary" disabled={busy || !messageForm.to_agent || !messageForm.message.trim()}>
                Send
              </button>
            </form>

            <h3 style={{ fontSize: '0.95rem' }}>Goals ({goals.length})</h3>
            {goals.length === 0 ? (
              <p style={{ color: '#999', fontSize: '0.9rem' }}>No goals assigned to this agent.</p>
            ) : (
              <div style={{ display: 'grid', gap: '0.5rem', marginBottom: '1.5rem' }}>
                {goals.map(g => (
                  <Link key={g.id} to="/goals" style={{ textDecoration: 'none', color: 'inherit' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.4rem 0' }}>
                      <span>{g.title}</span>
                      <span style={{ color: '#999' }}>{g.current_value} / {g.target_value}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}

            <h3 style={{ fontSize: '0.95rem' }}>Approvals Requested ({selectedApprovals.length})</h3>
            {selectedApprovals.length === 0 ? (
              <p style={{ color: '#999', fontSize: '0.9rem' }}>No approvals requested by this agent — this is the permission boundary: risky actions always route through Approvals.</p>
            ) : (
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {selectedApprovals.slice(0, 8).map(r => (
                  <Link key={r.id} to="/approvals" style={{ textDecoration: 'none', color: 'inherit' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.4rem 0' }}>
                      <span>{r.title}</span>
                      <span className={`badge ${r.status === 'pending' ? 'badge-warning' : r.status === 'approved' ? 'badge-success' : 'badge-danger'}`}>
                        {r.status}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
