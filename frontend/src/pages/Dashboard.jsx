import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api.js'

export default function Dashboard() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [analyticsHealth, setAnalyticsHealth] = useState(null)
  const [goals, setGoals] = useState([])
  const [heartbeat, setHeartbeat] = useState(null)
  const [stats, setStats] = useState({ totalContacts: 0, totalDeals: 0, pipelineValue: 0, closedDeals: 0 })
  const [followups, setFollowups] = useState(null)

  useEffect(() => {
    api.get('/health')
      .then(() => setApiStatus('connected'))
      .catch(() => setApiStatus('offline'))

    api.get('/analytics/health')
      .then(res => setAnalyticsHealth(res.data))
      .catch(() => setAnalyticsHealth(null))

    api.get('/api/v1/hermes/goals')
      .then(res => setGoals(res.data.goals || []))
      .catch(() => setGoals([]))

    api.get('/api/v1/heartbeat/status')
      .then(res => setHeartbeat(res.data))
      .catch(() => setHeartbeat(null))

    Promise.all([
      api.get('/api/v1/crm/contacts', { params: { limit: 500 } }),
      api.get('/api/v1/crm/deals', { params: { limit: 500 } }),
    ]).then(([contactsRes, dealsRes]) => {
      const deals = dealsRes.data.deals || []
      const open = deals.filter(d => d.stage !== 'closed_won' && d.stage !== 'closed_lost')
      setStats({
        totalContacts: contactsRes.data.count || 0,
        totalDeals: open.length,
        pipelineValue: open.reduce((sum, d) => sum + (d.value || 0), 0),
        closedDeals: deals.filter(d => d.stage === 'closed_won').length,
      })
    }).catch(() => {})

    api.get('/api/v1/crm/followups')
      .then(res => setFollowups(res.data))
      .catch(() => setFollowups(null))
  }, [])

  return (
    <div>
      <h1>Dashboard</h1>

      <div className="grid">
        <div className="stat-card">
          <div className="stat-label">Total Contacts</div>
          <div className="stat-number">{stats.totalContacts}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Open Deals</div>
          <div className="stat-number">{stats.totalDeals}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pipeline Value</div>
          <div className="stat-number">${(stats.pipelineValue / 1000).toFixed(0)}K</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Closed Deals</div>
          <div className="stat-number">{stats.closedDeals}</div>
        </div>
      </div>

      {followups && followups.total > 0 && (
        <div className="card">
          <h2 className="card-title">Needs Your Attention ({followups.total})</h2>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {followups.overdue_tasks.slice(0, 3).map(t => (
              <div key={t.id} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>⚠️ Overdue: {t.subject}</span>
                <Link to={t.deal_id ? `/deals/${t.deal_id}` : `/contacts/${t.contact_id}`} style={{ color: '#667eea' }}>View</Link>
              </div>
            ))}
            {followups.at_risk_deals.slice(0, 3).map(d => (
              <div key={d.deal_id} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>📉 At risk: {d.name}</span>
                <Link to={`/deals/${d.deal_id}`} style={{ color: '#667eea' }}>View</Link>
              </div>
            ))}
            {followups.stalled_contacts.slice(0, 3).map(c => (
              <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>💤 Stalled: {c.name} ({c.days_stale}d quiet)</span>
                <Link to={`/contacts/${c.id}`} style={{ color: '#667eea' }}>View</Link>
              </div>
            ))}
            {followups.pending_approvals.slice(0, 3).map(r => (
              <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>✅ Approval: {r.title}</span>
                <Link to="/approvals" style={{ color: '#667eea' }}>View</Link>
              </div>
            ))}
          </div>
          <Link to="/copilot" style={{ display: 'inline-block', marginTop: '1rem', color: '#667eea' }}>
            Ask Copilot for the full brief →
          </Link>
        </div>
      )}

      <div className="card" style={{ marginTop: '2rem' }}>
        <h2 className="card-title">System Status</h2>
        <p>
          Backend API:{' '}
          {apiStatus === 'connected' && <span className="badge badge-success">Connected</span>}
          {apiStatus === 'offline' && <span className="badge badge-danger">Offline — start the backend on port 8000</span>}
          {apiStatus === 'checking' && <span className="badge badge-warning">Checking…</span>}
        </p>
        {heartbeat && (
          <p style={{ marginTop: '0.75rem' }}>
            Heartbeat: <span className={`badge ${heartbeat.running ? 'badge-success' : 'badge-danger'}`}>
              {heartbeat.running ? 'running' : 'stopped'}
            </span>
            {' '}• {heartbeat.jobs?.length || 0} autonomous jobs
          </p>
        )}
        {analyticsHealth && (
          <p style={{ marginTop: '0.75rem' }}>
            Analytics engine: <span className="badge badge-success">{analyticsHealth.status}</span>
            {' '}• {analyticsHealth.metrics_registered} metrics • {analyticsHealth.dashboards_created} dashboards
          </p>
        )}
      </div>

      {goals.length > 0 && (
        <div className="card">
          <h2 className="card-title">Hermes Goals</h2>
          {goals.slice(0, 5).map(g => (
            <div key={g.id} style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <strong>{g.title}</strong>
                <span style={{ color: '#999' }}>
                  {g.current_value} / {g.target_value} · {g.status}
                </span>
              </div>
              <div style={{ backgroundColor: '#f0f0f0', borderRadius: '6px', height: '10px', overflow: 'hidden' }}>
                <div style={{
                  backgroundColor: g.progress >= 1 ? '#06A77D' : '#667eea',
                  height: '100%',
                  width: `${Math.min(Math.round((g.progress || 0) * 100), 100)}%`,
                }} />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h2 className="card-title">Quick Start</h2>
        <ul style={{ paddingLeft: '1.5rem', lineHeight: 2 }}>
          <li>📇 Manage contacts on the <strong>Contacts</strong> page</li>
          <li>💼 Track your pipeline on the <strong>Deals</strong> page</li>
          <li>📊 Explore dashboards on the <strong>Analytics</strong> page</li>
        </ul>
      </div>
    </div>
  )
}
