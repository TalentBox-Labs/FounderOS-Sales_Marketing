import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const PRESETS = [
  { key: 'lead-qualified', label: 'Lead Qualified → notify + task' },
  { key: 'deal-at-risk', label: 'Deal At Risk → alert owner' },
  { key: 'deal-closed', label: 'Deal Closed → celebrate + handoff' },
  { key: 'crew-completed', label: 'Crew Completed → publish content' },
]

export default function Automation() {
  const [workflows, setWorkflows] = useState([])
  const [events, setEvents] = useState([])
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState(null)
  const [offline, setOffline] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    const results = await Promise.allSettled([
      api.get('/api/v1/automation/workflows'),
      api.get('/api/v1/automation/events/history', { params: { limit: 25 } }),
    ])
    const [wfRes, evRes] = results
    if (wfRes.status === 'fulfilled') {
      setWorkflows(wfRes.value.data.workflows || [])
      setOffline(false)
    } else {
      setOffline(true)
    }
    if (evRes.status === 'fulfilled') {
      setEvents(evRes.value.data.events || evRes.value.data.history || [])
    }
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  const toggleWorkflow = async (id) => {
    setBusy(true)
    try {
      await api.put(`/api/v1/automation/workflows/${id}/toggle`)
      await load()
    } finally {
      setBusy(false)
    }
  }

  const installPreset = async (key) => {
    setBusy(true)
    try {
      await api.post(`/api/v1/automation/workflows/presets/${key}`)
      setNotice(`Preset installed: ${key}`)
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || `Failed to install ${key}`)
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <div className="loading">Loading automation…</div>

  return (
    <div>
      <h1>Automation Rules</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Event-driven workflows: when something happens (lead qualified, deal at
        risk…), these rules decide what runs. The heartbeat and Hermes emit the
        events; n8n receives the bridged ones.
      </p>

      {offline && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>
          Backend offline — start the API on port 8000
        </div>
      )}
      {notice && (
        <div className="card" style={{ borderLeft: '4px solid #667eea', padding: '1rem 2rem' }}>
          {String(notice)}
          <button className="btn btn-secondary" style={{ marginLeft: '1rem', padding: '0.2rem 0.6rem' }}
            onClick={() => setNotice(null)}>dismiss</button>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">Workflows ({workflows.length})</h2>
        {workflows.length === 0 ? (
          <div className="empty-state">
            <h3>No workflows installed</h3>
            <p>Install a preset below to get started.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Workflow</th><th>Trigger Event</th><th>Actions</th><th>Enabled</th><th></th></tr>
            </thead>
            <tbody>
              {workflows.map(wf => (
                <tr key={wf.id}>
                  <td>
                    <strong>{wf.name}</strong>
                    {wf.description && <div style={{ color: '#999', fontSize: '0.85rem' }}>{wf.description}</div>}
                  </td>
                  <td><code style={{ backgroundColor: '#f5f5f5', padding: '0.2rem 0.5rem', borderRadius: '3px' }}>
                    {wf.event_type || wf.trigger || '—'}
                  </code></td>
                  <td>{Array.isArray(wf.actions) ? wf.actions.length : (wf.action_count ?? '—')}</td>
                  <td>
                    <span className={`badge ${wf.enabled ? 'badge-success' : 'badge-danger'}`}>
                      {wf.enabled ? 'on' : 'off'}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                      disabled={busy} onClick={() => toggleWorkflow(wf.id)}>
                      {wf.enabled ? 'Disable' : 'Enable'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h2 className="card-title">Install Preset Workflows</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          {PRESETS.map(p => (
            <button key={p.key} className="btn btn-secondary" disabled={busy}
              style={{ textAlign: 'left', padding: '1rem' }}
              onClick={() => installPreset(p.key)}>
              + {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Recent Events ({events.length})</h2>
        {events.length === 0 ? (
          <p style={{ color: '#999' }}>No events recorded yet this session.</p>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Event</th><th>Entity</th><th>Source</th><th>Priority</th></tr>
            </thead>
            <tbody>
              {events.map((ev, i) => (
                <tr key={ev.event_id || i}>
                  <td><strong>{ev.event_type}</strong></td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {ev.entity_type} {String(ev.entity_id || '').slice(0, 8)}
                  </td>
                  <td>{ev.source}</td>
                  <td><span className="badge badge-warning">{ev.priority}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
