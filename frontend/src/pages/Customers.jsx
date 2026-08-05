import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const HEALTH_BADGE = {
  healthy: 'badge-success',
  at_risk: 'badge-danger',
  needs_attention: 'badge-warning',
}

export default function Customers() {
  const [summary, setSummary] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [atRisk, setAtRisk] = useState([])
  const [expansion, setExpansion] = useState([])
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)

  const load = useCallback(async () => {
    const results = await Promise.allSettled([
      api.get('/api/v1/csm/accounts/health'),
      api.get('/api/v1/csm/accounts/at-risk'),
      api.get('/api/v1/csm/accounts/expansion-opportunities'),
      api.get('/api/v1/csm/actions-summary'),
    ])
    const [healthRes, riskRes, expRes, summaryRes] = results
    let anyOk = false

    if (healthRes.status === 'fulfilled') {
      anyOk = true
      const d = healthRes.value.data
      setAccounts(d.accounts || d.assessments || [])
    }
    if (riskRes.status === 'fulfilled') {
      anyOk = true
      setAtRisk(riskRes.value.data.accounts || riskRes.value.data.at_risk || [])
    }
    if (expRes.status === 'fulfilled') {
      anyOk = true
      setExpansion(expRes.value.data.accounts || expRes.value.data.opportunities || [])
    }
    if (summaryRes.status === 'fulfilled') {
      anyOk = true
      setSummary(summaryRes.value.data)
    }
    setOffline(!anyOk)
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="loading">Loading customer health…</div>

  const healthyCount = accounts.filter(a => (a.health_status || a.status) === 'healthy').length
  const riskCount = atRisk.length || accounts.filter(a => (a.health_status || a.status) === 'at_risk').length

  return (
    <div>
      <h1>Customers — Success & Health</h1>

      {offline && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>
          Backend offline — start the API on port 8000
        </div>
      )}

      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className="stat-label">Accounts Assessed</div>
          <div className="stat-number">{accounts.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Healthy</div>
          <div className="stat-number" style={{ color: '#06A77D' }}>{healthyCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">At Risk</div>
          <div className="stat-number" style={{ color: '#D62828' }}>{riskCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Expansion Opportunities</div>
          <div className="stat-number">{expansion.length}</div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Account Health</h2>
        {accounts.length === 0 ? (
          <div className="empty-state">
            <h3>No customer accounts yet</h3>
            <p>
              Health scoring activates once contacts become customers with deals.
              Mark a contact as <strong>customer</strong> on the Contacts page to start.
            </p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Account</th><th>Health Score</th><th>Status</th><th>Signals</th></tr>
            </thead>
            <tbody>
              {accounts.map((a, i) => (
                <tr key={a.account_id || i}>
                  <td><strong>{a.account_name || a.name || a.account_id}</strong></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ backgroundColor: '#f0f0f0', borderRadius: '4px', height: '8px', width: '80px', overflow: 'hidden' }}>
                        <div style={{
                          backgroundColor: (a.health_score || 0) >= 70 ? '#06A77D' : (a.health_score || 0) >= 40 ? '#eda100' : '#D62828',
                          height: '100%', width: `${Math.min(a.health_score || 0, 100)}%`,
                        }} />
                      </div>
                      {Math.round(a.health_score || 0)}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${HEALTH_BADGE[a.health_status || a.status] || 'badge-warning'}`}>
                      {(a.health_status || a.status || 'unknown').replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.85rem', color: '#666' }}>
                    {Array.isArray(a.risk_factors) && a.risk_factors.length > 0
                      ? a.risk_factors.slice(0, 2).join('; ')
                      : Array.isArray(a.signals) ? a.signals.slice(0, 2).join('; ') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {expansion.length > 0 && (
        <div className="card">
          <h2 className="card-title">Expansion Opportunities</h2>
          <table className="table">
            <thead><tr><th>Account</th><th>Potential</th><th>Reason</th></tr></thead>
            <tbody>
              {expansion.map((a, i) => (
                <tr key={i}>
                  <td><strong>{a.account_name || a.name || a.account_id}</strong></td>
                  <td>{a.expansion_potential || a.potential || '—'}</td>
                  <td style={{ color: '#666' }}>{a.reason || a.recommendation || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {summary && summary.actions && (
        <div className="card">
          <h2 className="card-title">Recommended Actions</h2>
          <ul style={{ paddingLeft: '1.5rem', lineHeight: 2 }}>
            {(Array.isArray(summary.actions) ? summary.actions : []).slice(0, 8).map((a, i) => (
              <li key={i}>{typeof a === 'string' ? a : a.description || a.action || JSON.stringify(a)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
