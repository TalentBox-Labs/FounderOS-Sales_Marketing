import React, { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api.js'
import Timeline from '../components/Timeline.jsx'

const badgeClass = (status) =>
  status === 'qualified' || status === 'customer' ? 'badge-success' :
  status === 'churned' ? 'badge-danger' : 'badge-warning'

const STAGE_COLORS = {
  discovery: '#FFB800', qualified: '#9B5DE5', proposal: '#00B4D8',
  negotiation: '#00D4FF', closed_won: '#06A77D', closed_lost: '#D62828',
}

const ICP_COLORS = { high: '#06A77D', medium: '#FFB800', low: '#999' }

export default function ContactDetail() {
  const { id } = useParams()
  const [contact, setContact] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [linkedinInput, setLinkedinInput] = useState('')
  const [enriching, setEnriching] = useState(false)
  const [enrichResult, setEnrichResult] = useState(null)

  const load = useCallback(async () => {
    try {
      const res = await api.get(`/api/v1/crm/contacts/${id}`)
      setContact(res.data.contact)
      setLinkedinInput(res.data.contact.linkedin_url || '')
      setError(null)
    } catch (err) {
      setError(err.response?.status === 404 ? 'Contact not found' : 'Backend offline — start the API on port 8000')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  const runEnrich = async () => {
    if (!linkedinInput.trim()) return
    setEnriching(true)
    setEnrichResult(null)
    try {
      const res = await api.post(`/api/v1/crm/contacts/${id}/enrich`, { linkedin_url: linkedinInput.trim() })
      setEnrichResult(res.data)
      if (res.data.ok) await load()
    } catch (err) {
      setEnrichResult({ ok: false, configured: true, reason: err.response?.data?.detail || 'Enrichment failed' })
    } finally {
      setEnriching(false)
    }
  }

  if (loading) return <div className="loading">Loading contact…</div>
  if (error) return <div className="card" style={{ borderLeft: '4px solid #D62828' }}>{error}</div>
  if (!contact) return null

  return (
    <div>
      <Link to="/contacts" style={{ color: '#667eea', textDecoration: 'none' }}>&larr; All Contacts</Link>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '1rem 0 2rem' }}>
        <h1 style={{ marginBottom: 0 }}>{contact.name}</h1>
        <span className={`badge ${badgeClass(contact.status)}`}>{contact.status}</span>
      </div>

      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className="stat-label">Email</div>
          <div className="stat-number" style={{ fontSize: '1.1rem' }}>{contact.email}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Lead Score</div>
          <div className="stat-number">{contact.lead_score}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Phone</div>
          <div className="stat-number" style={{ fontSize: '1.1rem' }}>{contact.phone || '—'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Title</div>
          <div className="stat-number" style={{ fontSize: '1.1rem' }}>{contact.title || '—'}</div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">LinkedIn Enrichment</h2>
        <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1rem' }}>
          <input type="text" value={linkedinInput} onChange={e => setLinkedinInput(e.target.value)}
            placeholder="https://linkedin.com/in/..."
            style={{ flex: 1, padding: '0.6rem', border: '1px solid #ddd', borderRadius: '4px' }} />
          <button className="btn btn-primary" disabled={enriching || !linkedinInput.trim()} onClick={runEnrich}>
            {enriching ? 'Enriching…' : 'Enrich'}
          </button>
        </div>

        {enrichResult && !enrichResult.ok && !enrichResult.configured && (
          <div style={{ padding: '0.9rem', backgroundColor: '#fff8e6', borderRadius: '8px', fontSize: '0.9rem' }}>
            {enrichResult.reason} <Link to="/integrations" style={{ color: '#667eea' }}>Configure it →</Link>
          </div>
        )}
        {enrichResult && !enrichResult.ok && enrichResult.configured && (
          <div style={{ padding: '0.9rem', backgroundColor: '#fff2f2', borderRadius: '8px', fontSize: '0.9rem', color: '#D62828' }}>
            {enrichResult.reason}
          </div>
        )}
        {enrichResult?.ok && (
          <div style={{ padding: '1rem', backgroundColor: '#f8f9ff', borderRadius: '8px' }}>
            {enrichResult.headline && <p style={{ margin: '0 0 0.5rem', fontWeight: 600 }}>{enrichResult.headline}</p>}
            {enrichResult.company && (
              <p style={{ margin: '0 0 0.5rem', color: '#444' }}>
                {enrichResult.company.name} · {enrichResult.company.industry}
                {enrichResult.company.employee_count ? ` · ${enrichResult.company.employee_count} employees` : ''}
              </p>
            )}
            {enrichResult.icp_fit && (
              <div>
                <span style={{
                  backgroundColor: ICP_COLORS[enrichResult.icp_fit.fit], color: 'white',
                  padding: '0.25rem 0.7rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 600,
                  textTransform: 'uppercase',
                }}>
                  {enrichResult.icp_fit.fit} ICP fit ({enrichResult.icp_fit.score}/100)
                </span>
                <ul style={{ margin: '0.6rem 0 0', paddingLeft: '1.2rem', fontSize: '0.85rem', color: '#666' }}>
                  {enrichResult.icp_fit.reasons.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="card-title">Deals ({contact.deals?.length || 0})</h2>
        {!contact.deals?.length ? (
          <div className="empty-state"><p>No deals yet for this contact.</p></div>
        ) : (
          <table className="table">
            <thead><tr><th>Deal</th><th>Stage</th><th>Value</th></tr></thead>
            <tbody>
              {contact.deals.map(d => (
                <tr key={d.id}>
                  <td><Link to={`/deals/${d.id}`} style={{ color: '#667eea' }}>{d.name}</Link></td>
                  <td>
                    <span style={{
                      backgroundColor: STAGE_COLORS[d.stage] || '#999',
                      color: 'white', padding: '0.3rem 0.6rem', borderRadius: '4px',
                      fontSize: '0.8rem', textTransform: 'capitalize',
                    }}>
                      {(d.stage || '').replace('_', ' ')}
                    </span>
                  </td>
                  <td>${(d.value || 0).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Timeline contactId={id} />
    </div>
  )
}
