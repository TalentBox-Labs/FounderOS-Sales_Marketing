import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const SALES_STAGES = ['discovery', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost']

const STAGE_COLORS = {
  discovery: '#FFB800',
  qualified: '#9B5DE5',
  proposal: '#00B4D8',
  negotiation: '#00D4FF',
  closed_won: '#06A77D',
  closed_lost: '#D62828',
}

const EMPTY_FORM = { name: '', value: '', stage: 'discovery', contact_id: '' }

export default function Deals() {
  const [deals, setDeals] = useState([])
  const [contacts, setContacts] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const [dealsRes, contactsRes] = await Promise.all([
        api.get('/api/v1/crm/deals', { params: { limit: 200 } }),
        api.get('/api/v1/crm/contacts', { params: { limit: 200 } }),
      ])
      setDeals(dealsRes.data.deals || [])
      setContacts(contactsRes.data.contacts || [])
      setError(null)
    } catch {
      setError('Backend offline — start the API on port 8000')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/api/v1/crm/deals', {
        name: formData.name,
        value: parseFloat(formData.value || '0'),
        stage: formData.stage,
        contact_id: formData.contact_id || null,
      })
      setFormData(EMPTY_FORM)
      setShowForm(false)
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create deal')
    } finally {
      setBusy(false)
    }
  }

  const openDeals = deals.filter(d => d.stage !== 'closed_won' && d.stage !== 'closed_lost')
  const totalPipeline = openDeals.reduce((sum, d) => sum + (d.value || 0), 0)
  const closedWon = deals.filter(d => d.stage === 'closed_won').reduce((sum, d) => sum + (d.value || 0), 0)
  const decided = deals.filter(d => d.stage === 'closed_won' || d.stage === 'closed_lost')
  const winRate = decided.length
    ? Math.round((deals.filter(d => d.stage === 'closed_won').length / decided.length) * 100)
    : 0
  const maxStageValue = Math.max(
    1,
    ...SALES_STAGES.map(s => deals.filter(d => d.stage === s).reduce((sum, d) => sum + (d.value || 0), 0)),
  )

  if (loading) return <div className="loading">Loading deals…</div>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: 0 }}>Sales Pipeline</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Deal'}
        </button>
      </div>

      {error && <div className="card" style={{ borderLeft: '4px solid #D62828' }}>{String(error)}</div>}

      {showForm && (
        <div className="card">
          <h2 className="card-title">New Deal</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 2fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Deal Name</label>
                <input type="text" required value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Value ($)</label>
                <input type="number" min="0" step="any" value={formData.value}
                  onChange={e => setFormData({ ...formData, value: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Stage</label>
                <select value={formData.stage}
                  onChange={e => setFormData({ ...formData, stage: e.target.value })}>
                  {SALES_STAGES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Contact (optional)</label>
                <select value={formData.contact_id}
                  onChange={e => setFormData({ ...formData, contact_id: e.target.value })}>
                  <option value="">— none —</option>
                  {contacts.map(c => <option key={c.id} value={c.id}>{c.name} ({c.email})</option>)}
                </select>
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? 'Saving…' : 'Create Deal'}
            </button>
          </form>
        </div>
      )}

      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className="stat-label">Open Pipeline</div>
          <div className="stat-number">${(totalPipeline / 1000).toFixed(0)}K</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Closed Won</div>
          <div className="stat-number">${(closedWon / 1000).toFixed(0)}K</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Deals</div>
          <div className="stat-number">{deals.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Win Rate</div>
          <div className="stat-number">{winRate}%</div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Pipeline by Stage</h2>
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {SALES_STAGES.map(stage => {
            const stageDeals = deals.filter(d => d.stage === stage)
            const stageValue = stageDeals.reduce((sum, d) => sum + (d.value || 0), 0)
            return (
              <div key={stage}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <strong style={{ textTransform: 'capitalize' }}>{stage.replace('_', ' ')}</strong>
                  <span style={{ float: 'right', color: '#999' }}>
                    {stageDeals.length} deals · ${(stageValue / 1000).toFixed(0)}K
                  </span>
                </div>
                <div style={{ backgroundColor: '#f0f0f0', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                  <div style={{
                    backgroundColor: STAGE_COLORS[stage],
                    height: '100%',
                    width: `${Math.round((stageValue / maxStageValue) * 100)}%`,
                    transition: 'width 0.3s',
                  }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">All Deals ({deals.length})</h2>
        {deals.length === 0 ? (
          <div className="empty-state">
            <h3>No deals yet</h3>
            <p>Create a deal, or let Hermes open deals for qualified contacts via a pipeline goal.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Deal</th><th>Contact</th><th>Value</th><th>Stage</th><th>Probability</th></tr>
            </thead>
            <tbody>
              {deals.map(deal => (
                <tr key={deal.id}>
                  <td><strong>{deal.name}</strong></td>
                  <td>{deal.contact_name || '—'}</td>
                  <td>${(deal.value || 0).toLocaleString()}</td>
                  <td>
                    <span style={{
                      backgroundColor: STAGE_COLORS[deal.stage] || '#999',
                      color: 'white', padding: '0.4rem 0.8rem', borderRadius: '4px',
                      fontSize: '0.85rem', textTransform: 'capitalize',
                    }}>
                      {(deal.stage || '').replace('_', ' ')}
                    </span>
                  </td>
                  <td>{deal.probability}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
