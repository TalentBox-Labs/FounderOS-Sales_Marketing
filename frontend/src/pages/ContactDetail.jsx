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

export default function ContactDetail() {
  const { id } = useParams()
  const [contact, setContact] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const res = await api.get(`/api/v1/crm/contacts/${id}`)
      setContact(res.data.contact)
      setError(null)
    } catch (err) {
      setError(err.response?.status === 404 ? 'Contact not found' : 'Backend offline — start the API on port 8000')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

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
