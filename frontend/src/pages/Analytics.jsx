import React, { useState, useEffect } from 'react'
import api from '../api.js'

const DASHBOARD_ICONS = {
  executive: '👔',
  sales: '💼',
  csm: '💝',
  marketing: '📢',
  operations: '⚙️',
}

const DASHBOARD_DESCRIPTIONS = {
  executive: 'High-level business metrics for the C-suite',
  sales: 'Pipeline and deal metrics for the sales team',
  csm: 'Customer health and retention metrics',
  marketing: 'Lead generation and campaign performance',
  operations: 'System health and automation metrics',
}

export default function Analytics() {
  const [dashboards, setDashboards] = useState([])
  const [selected, setSelected] = useState(null)
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/analytics/dashboards/templates')
      .then(res => {
        const list = Object.entries(res.data.templates || {}).map(([key, value]) => ({ id: key, ...value }))
        setDashboards(list)
        setConnected(true)
      })
      .catch(() => {
        // Backend offline — show the template names so the page still renders.
        setDashboards(Object.keys(DASHBOARD_ICONS).map(id => ({
          id,
          name: `${id.charAt(0).toUpperCase()}${id.slice(1)} Dashboard`,
          dashboard_type: id,
          widgets: [],
        })))
        setConnected(false)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading analytics…</div>

  return (
    <div>
      <h1>Analytics & Reports</h1>

      <div className="card">
        <h2 className="card-title">Backend Connection</h2>
        {connected ? (
          <span className="badge badge-success">✓ Live — dashboard templates loaded from the API</span>
        ) : (
          <span className="badge badge-danger">Offline — start the backend on port 8000 to load live data</span>
        )}
      </div>

      <div className="card">
        <h2 className="card-title">Available Dashboards</h2>
        <div className="grid" style={{ marginTop: '1rem' }}>
          {dashboards.map(d => (
            <div key={d.id} className="stat-card" style={{ cursor: 'pointer' }} onClick={() => setSelected(d)}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
                {DASHBOARD_ICONS[d.dashboard_type] || '📊'}
              </div>
              <h3 style={{ marginBottom: '0.5rem' }}>{d.name}</h3>
              <p style={{ color: '#999', fontSize: '0.9rem', marginBottom: '1rem' }}>
                {DASHBOARD_DESCRIPTIONS[d.dashboard_type] || 'View detailed metrics'}
              </p>
              <button className="btn btn-primary" style={{ width: '100%' }}>
                {selected?.id === d.id ? 'Selected' : 'View Widgets'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {selected && (
        <div className="card">
          <h2 className="card-title">{selected.name} — Widgets</h2>
          {selected.widgets?.length ? (
            <table className="table">
              <thead>
                <tr><th>Widget</th><th>Metric</th><th>Type</th></tr>
              </thead>
              <tbody>
                {selected.widgets.map((w, i) => (
                  <tr key={i}>
                    <td><strong>{w.name}</strong></td>
                    <td>{w.metric_id}</td>
                    <td><span className="badge badge-warning">{w.widget_type}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#999' }}>
              Widget definitions load from the backend. Start the API to see this dashboard's widgets.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
