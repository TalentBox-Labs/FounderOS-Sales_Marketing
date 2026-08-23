import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const ACTOR_COLORS = {
  heartbeat: '#00B4D8',
  hermes: '#667eea',
  n8n: '#F77F00',
  platform: '#06A77D',
}

const ACTOR_FILTERS = ['all', 'heartbeat', 'hermes', 'n8n', 'platform']

function timeAgo(iso) {
  if (!iso) return ''
  const hasTimezone = /Z$|[+-]\d{2}:\d{2}$/.test(iso)
  const seconds = Math.floor((Date.now() - new Date(hasTimezone ? iso : iso + 'Z')) / 1000)
  if (Number.isNaN(seconds)) return iso.slice(0, 19).replace('T', ' ')
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export default function Activity() {
  const [status, setStatus] = useState(null)
  const [actions, setActions] = useState([])
  const [actorFilter, setActorFilter] = useState('all')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [busy, setBusy] = useState(false)
  const [offline, setOffline] = useState(false)

  const load = useCallback(async () => {
    try {
      const params = actorFilter === 'all' ? { limit: 50 } : { limit: 50, actor: actorFilter }
      const [statusRes, activityRes] = await Promise.all([
        api.get('/api/v1/heartbeat/status'),
        api.get('/api/v1/heartbeat/activity', { params }),
      ])
      setStatus(statusRes.data)
      setActions(activityRes.data.actions || [])
      setOffline(false)
    } catch {
      setOffline(true)
    }
  }, [actorFilter])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!autoRefresh) return undefined
    const timer = setInterval(load, 10000)
    return () => clearInterval(timer)
  }, [autoRefresh, load])

  const runJob = async (jobName) => {
    setBusy(true)
    try {
      await api.post(`/api/v1/heartbeat/run/${jobName}`)
      await load()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: 0 }}>Activity — Command Center</h1>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#666' }}>
          <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
          Auto-refresh (10s)
        </label>
      </div>

      {offline && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>
          Backend offline — start the API on port 8000
        </div>
      )}

      <div className="card">
        <h2 className="card-title">Heartbeat</h2>
        {status ? (
          <>
            <p style={{ marginBottom: '1rem' }}>
              Scheduler:{' '}
              <span className={`badge ${status.running ? 'badge-success' : 'badge-danger'}`}>
                {status.running ? 'running' : 'stopped'}
              </span>
            </p>
            <table className="table">
              <thead>
                <tr><th>Job</th><th>Interval</th><th>Last Run</th><th>Status</th><th>Runs</th><th></th></tr>
              </thead>
              <tbody>
                {status.jobs.map(job => (
                  <tr key={job.name}>
                    <td><strong>{job.name}</strong></td>
                    <td>{Math.round(job.interval_seconds / 60)} min</td>
                    <td>{job.last_run_at ? timeAgo(job.last_run_at) : 'never'}</td>
                    <td>
                      {job.last_status ? (
                        <span className={`badge ${job.last_status === 'completed' ? 'badge-success' : 'badge-danger'}`}>
                          {job.last_status}
                        </span>
                      ) : '—'}
                    </td>
                    <td>{job.runs}</td>
                    <td>
                      <button className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                        disabled={busy} onClick={() => runJob(job.name)}>
                        Run Now
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <div className="loading">Loading heartbeat status…</div>
        )}
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>Audit Trail ({actions.length})</h2>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {ACTOR_FILTERS.map(actor => (
              <button
                key={actor}
                className={`btn ${actorFilter === actor ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                onClick={() => setActorFilter(actor)}
              >
                {actor}
              </button>
            ))}
          </div>
        </div>

        {actions.length === 0 ? (
          <div className="empty-state">
            <h3>No activity yet</h3>
            <p>Autonomous actions (scoring, qualification, n8n calls) will appear here.</p>
          </div>
        ) : (
          <div style={{ marginTop: '1rem', display: 'grid', gap: '0.5rem' }}>
            {actions.map(a => (
              <div key={a.id} style={{
                display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                padding: '0.75rem', backgroundColor: '#f9f9f9', borderRadius: '6px',
                borderLeft: `4px solid ${a.status === 'failed' ? '#D62828' : (ACTOR_COLORS[a.actor] || '#999')}`,
              }}>
                <span style={{
                  backgroundColor: ACTOR_COLORS[a.actor] || '#999', color: 'white',
                  padding: '0.2rem 0.6rem', borderRadius: '4px',
                  fontSize: '0.8rem', fontWeight: 600, whiteSpace: 'nowrap',
                }}>
                  {a.actor}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div>
                    <strong>{a.action_type}</strong>
                    {a.target_type && <span style={{ color: '#999' }}> · {a.target_type} {a.target_id ? String(a.target_id).slice(0, 8) : ''}</span>}
                    {a.status === 'failed' && <span className="badge badge-danger" style={{ marginLeft: '0.5rem' }}>failed</span>}
                  </div>
                  {a.detail && (
                    <div style={{
                      fontFamily: 'monospace', fontSize: '0.8rem', color: '#666',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {JSON.stringify(a.detail)}
                    </div>
                  )}
                </div>
                <span style={{ color: '#999', fontSize: '0.85rem', whiteSpace: 'nowrap' }}>
                  {timeAgo(a.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
