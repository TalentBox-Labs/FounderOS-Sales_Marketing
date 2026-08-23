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

const SALES_AGENTS = [
  { key: 'research', label: 'ICP Research Agent', endpoint: 'research', cta: 'Research',
    blurb: 'Buying signals — funding, recent job change, company fit — from real LinkedIn data.' },
  { key: 'coldEmail', label: 'Cold Email Agent', endpoint: 'cold-email', cta: 'Draft email',
    blurb: "First-touch email from this contact's real CRM context, not merge tags." },
  { key: 'linkedin', label: 'LinkedIn Opener Agent', endpoint: 'linkedin-opener', cta: 'Draft opener',
    blurb: "Connection note + follow-up DM that don't read like a pitch." },
  { key: 'sequence', label: 'Follow-Up Sequence Agent', endpoint: 'sequence', cta: 'Build sequence',
    blurb: '5-7 touch nurture flow across email + LinkedIn.' },
  { key: 'objection', label: 'Objection Handler Agent', endpoint: 'handle-reply', cta: 'Handle latest reply',
    blurb: 'Classifies the latest inbound reply and drafts a response, for your approval.' },
]

export default function ContactDetail() {
  const { id } = useParams()
  const [contact, setContact] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [linkedinInput, setLinkedinInput] = useState('')
  const [enriching, setEnriching] = useState(false)
  const [enrichResult, setEnrichResult] = useState(null)

  const [agentBusy, setAgentBusy] = useState({})
  const [agentResults, setAgentResults] = useState({})

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

  const runAgent = async (agent) => {
    setAgentBusy(prev => ({ ...prev, [agent.key]: true }))
    setAgentResults(prev => ({ ...prev, [agent.key]: null }))
    try {
      const res = await api.post(`/api/v1/agents/sales/${id}/${agent.endpoint}`)
      setAgentResults(prev => ({ ...prev, [agent.key]: res.data }))
      if (res.data.ok && (agent.key === 'research')) await load()
    } catch (err) {
      setAgentResults(prev => ({ ...prev, [agent.key]: { ok: false, reason: err.response?.data?.detail || 'Agent failed' } }))
    } finally {
      setAgentBusy(prev => ({ ...prev, [agent.key]: false }))
    }
  }

  if (loading) return <div className="loading">Loading contact…</div>
  if (error) return <div className="card" style={{ borderLeft: '4px solid #D62828' }}>{error}</div>
  if (!contact) return null

  const boxStyle = { padding: '0.9rem', backgroundColor: '#f8f9ff', borderRadius: '8px', fontSize: '0.9rem', marginTop: '0.6rem' }
  const failStyle = { padding: '0.9rem', backgroundColor: '#fff8e6', borderRadius: '8px', fontSize: '0.9rem', marginTop: '0.6rem' }

  const renderAgentResult = (agent, r) => {
    if (!r) return null
    if (!r.ok) return <div style={failStyle}>{r.reason || 'No result'}</div>
    if (agent.key === 'research') {
      const s = r.signals || {}
      return (
        <div style={boxStyle}>
          {r.icp_fit && (
            <span style={{
              backgroundColor: ICP_COLORS[r.icp_fit.fit], color: 'white', padding: '0.25rem 0.7rem',
              borderRadius: '4px', fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase',
            }}>{r.icp_fit.fit} ICP fit ({r.icp_fit.score}/100)</span>
          )}
          <ul style={{ margin: '0.6rem 0 0', paddingLeft: '1.2rem' }}>
            <li>{s.job_change ? `Job change: ${s.job_change.title} at ${s.job_change.company} (~${s.job_change.days_ago}d ago)` : 'No recent job change detected'}</li>
            <li>{s.funding_rounds?.length ? `Funding: ${s.funding_rounds[0].type} (${s.funding_rounds[0].announced})` : 'No funding rounds on file'}</li>
            <li style={{ color: '#999' }}>{s.tech_stack?.reason}</li>
          </ul>
        </div>
      )
    }
    if (agent.key === 'coldEmail') {
      return <div style={boxStyle}><pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'inherit' }}>{r.body}</pre>
        <p style={{ marginTop: '0.6rem', color: '#667eea' }}><Link to="/approvals" style={{ color: 'inherit' }}>Filed for approval →</Link></p></div>
    }
    if (agent.key === 'linkedin') {
      return <div style={boxStyle}>
        <p style={{ margin: '0 0 0.5rem' }}><strong>Connection note:</strong> {r.connection_note}</p>
        <p style={{ margin: 0 }}><strong>Follow-up DM:</strong> {r.follow_up_dm}</p>
        <p style={{ marginTop: '0.6rem', color: '#667eea' }}><Link to="/approvals" style={{ color: 'inherit' }}>Filed for approval →</Link></p>
      </div>
    }
    if (agent.key === 'sequence') {
      return <div style={boxStyle}>
        Built a {r.steps?.length}-step sequence.{' '}
        <Link to="/marketing" style={{ color: '#667eea' }}>Review under Marketing → Sequences →</Link>
      </div>
    }
    if (agent.key === 'objection') {
      return <div style={boxStyle}>
        <span className="badge badge-warning" style={{ textTransform: 'uppercase', fontSize: '0.75rem' }}>{r.category?.replace('_', ' ')}</span>
        <p style={{ margin: '0.6rem 0 0' }}>{r.draft_reply}</p>
        {r.approval_id && <p style={{ marginTop: '0.6rem', color: '#667eea' }}><Link to="/approvals" style={{ color: 'inherit' }}>Filed for approval →</Link></p>}
      </div>
    }
    return null
  }

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
        <h2 className="card-title">Sales Agent Crew</h2>
        <p style={{ color: '#666', fontSize: '0.85rem', marginTop: '-0.5rem', marginBottom: '1rem' }}>
          Five specialized agents that draft real, context-aware outreach. Nothing sends on its own — every draft is filed to Approvals for you to review.
        </p>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {SALES_AGENTS.map(agent => (
            <div key={agent.key} style={{ border: '1px solid #eee', borderRadius: '8px', padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
                <div>
                  <strong>{agent.label}</strong>
                  <p style={{ margin: '0.2rem 0 0', color: '#666', fontSize: '0.85rem' }}>{agent.blurb}</p>
                </div>
                <button className="btn btn-secondary" style={{ whiteSpace: 'nowrap' }}
                  disabled={agentBusy[agent.key]} onClick={() => runAgent(agent)}>
                  {agentBusy[agent.key] ? 'Working…' : agent.cta}
                </button>
              </div>
              {renderAgentResult(agent, agentResults[agent.key])}
            </div>
          ))}
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
