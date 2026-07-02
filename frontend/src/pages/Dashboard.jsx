import React, { useState, useEffect } from 'react'
import api from '../api.js'

export default function Dashboard() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [analyticsHealth, setAnalyticsHealth] = useState(null)

  useEffect(() => {
    api.get('/health')
      .then(() => setApiStatus('connected'))
      .catch(() => setApiStatus('offline'))

    api.get('/analytics/health')
      .then(res => setAnalyticsHealth(res.data))
      .catch(() => setAnalyticsHealth(null))
  }, [])

  const stats = {
    totalContacts: 12,
    totalDeals: 8,
    pipelineValue: 250000,
    closedDeals: 5,
  }

  return (
    <div>
      <h1>Dashboard</h1>

      <div className="grid">
        <div className="stat-card">
          <div className="stat-label">Total Contacts</div>
          <div className="stat-number">{stats.totalContacts}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active Deals</div>
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

      <div className="card" style={{ marginTop: '2rem' }}>
        <h2 className="card-title">System Status</h2>
        <p>
          Backend API:{' '}
          {apiStatus === 'connected' && <span className="badge badge-success">Connected</span>}
          {apiStatus === 'offline' && <span className="badge badge-danger">Offline — start the backend on port 8000</span>}
          {apiStatus === 'checking' && <span className="badge badge-warning">Checking…</span>}
        </p>
        {analyticsHealth && (
          <p style={{ marginTop: '0.75rem' }}>
            Analytics engine: <span className="badge badge-success">{analyticsHealth.status}</span>
            {' '}• {analyticsHealth.metrics_registered} metrics • {analyticsHealth.dashboards_created} dashboards
          </p>
        )}
      </div>

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
