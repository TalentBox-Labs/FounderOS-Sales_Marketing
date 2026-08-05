import React, { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api.js'
import Timeline from '../components/Timeline.jsx'

const STAGE_COLORS = {
  discovery: '#FFB800', qualified: '#9B5DE5', proposal: '#00B4D8',
  negotiation: '#00D4FF', closed_won: '#06A77D', closed_lost: '#D62828',
}

export default function DealDetail() {
  const { id } = useParams()
  const [deal, setDeal] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const res = await api.get(`/api/v1/crm/deals/${id}`)
      setDeal(res.data.deal)
      setError(null)
    } catch (err) {
      setError(err.response?.status === 404 ? 'Deal not found' : 'Backend offline — start the API on port 8000')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="loading">Loading deal…</div>
  if (error) return <div className="card" style={{ borderLeft: '4px solid #D62828' }}>{error}</div>
  if (!deal) return null

  return (
    <div>
      <Link to="/deals" style={{ color: '#667eea', textDecoration: 'none' }}>&larr; All Deals</Link>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '1rem 0 2rem' }}>
        <h1 style={{ marginBottom: 0 }}>{deal.name}</h1>
        <span style={{
          backgroundColor: STAGE_COLORS[deal.stage] || '#999',
          color: 'white', padding: '0.4rem 0.9rem', borderRadius: '4px',
          fontSize: '0.9rem', textTransform: 'capitalize',
        }}>
          {(deal.stage || '').replace('_', ' ')}
        </span>
      </div>

      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className="stat-label">Value</div>
          <div className="stat-number">${(deal.value || 0).toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Probability</div>
          <div className="stat-number">{deal.probability}%</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Contact</div>
          <div className="stat-number" style={{ fontSize: '1.1rem' }}>
            {deal.contact_id
              ? <Link to={`/contacts/${deal.contact_id}`} style={{ color: '#667eea' }}>{deal.contact_name || 'View contact'}</Link>
              : '—'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Expected Close</div>
          <div className="stat-number" style={{ fontSize: '1.1rem' }}>
            {deal.expected_close_date ? new Date(deal.expected_close_date).toLocaleDateString() : '—'}
          </div>
        </div>
      </div>

      <Timeline dealId={id} />
    </div>
  )
}
