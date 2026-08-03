import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const METRICS = [
  { value: 'qualified_leads', label: 'Qualified Leads', unit: 'contacts' },
  { value: 'pipeline_value', label: 'Pipeline Value', unit: '$' },
  { value: 'deals_closed', label: 'Deals Closed', unit: 'deals' },
]

const EMPTY_FORM = { title: '', metric: 'qualified_leads', target_value: '', description: '' }

const STATUS_BADGE = {
  active: 'badge-warning',
  achieved: 'badge-success',
  paused: 'badge-danger',
}

function ProgressBar({ value }) {
  const pct = Math.round((value || 0) * 100)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <div style={{ flex: 1, backgroundColor: '#f0f0f0', borderRadius: '6px', height: '12px', overflow: 'hidden' }}>
        <div style={{
          backgroundColor: pct >= 100 ? '#06A77D' : '#667eea',
          height: '100%',
          width: `${Math.min(pct, 100)}%`,
          transition: 'width 0.4s',
        }} />
      </div>
      <span style={{ minWidth: '3rem', fontWeight: 600 }}>{pct}%</span>
    </div>
  )
}

export default function Goals() {
  const [goals, setGoals] = useState([])
  const [selected, setSelected] = useState(null) // { goal, plan }
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const loadGoals = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/hermes/goals')
      setGoals(res.data.goals || [])
      setError(null)
    } catch {
      setError('Backend offline — start the API on port 8000')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadGoals() }, [loadGoals])

  const openDetail = async (goalId) => {
    try {
      const res = await api.get(`/api/v1/hermes/goals/${goalId}`)
      setSelected(res.data)
    } catch { /* list stays usable */ }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/api/v1/hermes/goals', {
        title: formData.title,
        metric: formData.metric,
        target_value: parseFloat(formData.target_value),
        description: formData.description,
      })
      setFormData(EMPTY_FORM)
      setShowForm(false)
      await loadGoals()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create goal')
    } finally {
      setBusy(false)
    }
  }

  const checkNow = async (goalId) => {
    setBusy(true)
    try {
      await api.post(`/api/v1/hermes/goals/${goalId}/check`)
      await loadGoals()
      await openDetail(goalId)
    } finally {
      setBusy(false)
    }
  }

  const setStatus = async (goalId, action) => {
    setBusy(true)
    try {
      await api.post(`/api/v1/hermes/goals/${goalId}/${action}`)
      await loadGoals()
      if (selected?.goal?.id === goalId) await openDetail(goalId)
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <div className="loading">Loading goals…</div>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: 0 }}>Goals — Hermes Planner</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Goal'}
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>{error}</div>
      )}

      {showForm && (
        <div className="card">
          <h2 className="card-title">New Goal</h2>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            Hermes snapshots the current value as a baseline, generates an execution
            plan, and works toward the target on every heartbeat.
          </p>
          <form onSubmit={handleCreate}>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text" required minLength={3}
                  placeholder="e.g. Reach 20 qualified leads"
                  value={formData.title}
                  onChange={e => setFormData({ ...formData, title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Metric</label>
                <select
                  value={formData.metric}
                  onChange={e => setFormData({ ...formData, metric: e.target.value })}
                >
                  {METRICS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Target ({METRICS.find(m => m.value === formData.metric)?.unit})</label>
                <input
                  type="number" required min="1" step="any"
                  value={formData.target_value}
                  onChange={e => setFormData({ ...formData, target_value: e.target.value })}
                />
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? 'Creating…' : 'Create Goal & Generate Plan'}
            </button>
          </form>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">All Goals ({goals.length})</h2>
        {goals.length === 0 ? (
          <div className="empty-state">
            <h3>No goals yet</h3>
            <p>Create a goal and Hermes will plan and execute toward it autonomously.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Goal</th><th>Metric</th><th style={{ width: '28%' }}>Progress</th>
                <th>Value</th><th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {goals.map(g => (
                <tr key={g.id}>
                  <td>
                    <strong style={{ cursor: 'pointer', color: '#667eea' }} onClick={() => openDetail(g.id)}>
                      {g.title}
                    </strong>
                  </td>
                  <td>{g.metric.replace('_', ' ')}</td>
                  <td><ProgressBar value={g.progress} /></td>
                  <td>{g.current_value} / {g.target_value}</td>
                  <td><span className={`badge ${STATUS_BADGE[g.status] || 'badge-warning'}`}>{g.status}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {g.status === 'active' && (
                        <>
                          <button className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                            disabled={busy} onClick={() => checkNow(g.id)}>Run Check</button>
                          <button className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                            disabled={busy} onClick={() => setStatus(g.id, 'pause')}>Pause</button>
                        </>
                      )}
                      {g.status === 'paused' && (
                        <button className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                          disabled={busy} onClick={() => setStatus(g.id, 'resume')}>Resume</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selected && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 className="card-title" style={{ marginBottom: 0 }}>
              Plan: {selected.goal.title}
            </h2>
            <button className="btn btn-secondary" onClick={() => setSelected(null)}>Close</button>
          </div>
          <p style={{ color: '#666', margin: '0.75rem 0' }}>
            Baseline {selected.goal.baseline_value} → current {selected.goal.current_value} →
            target {selected.goal.target_value} • checked {selected.goal.checks}×
            {selected.goal.last_checked_at && ` (last: ${selected.goal.last_checked_at.slice(0, 19).replace('T', ' ')})`}
          </p>
          <table className="table">
            <thead>
              <tr><th>#</th><th>Step</th><th>Status</th><th>Runs</th><th>Last Result</th></tr>
            </thead>
            <tbody>
              {selected.plan.map(step => (
                <tr key={step.id}>
                  <td>{step.order + 1}</td>
                  <td>
                    <strong>{step.title}</strong>
                    {step.repeat && <span style={{ color: '#999', fontSize: '0.8rem' }}> (repeats)</span>}
                  </td>
                  <td>
                    <span className={`badge ${step.status === 'completed' ? 'badge-success' : step.status === 'failed' ? 'badge-danger' : 'badge-warning'}`}>
                      {step.status}
                    </span>
                  </td>
                  <td>{step.runs}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {step.result ? JSON.stringify(step.result) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
