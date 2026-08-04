import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const CATEGORY_LABELS = {
  email: 'Email', notifications: 'Notifications', messaging: 'Messaging',
  calendar: 'Calendar', automation: 'Automation', ai: 'AI', content: 'Content Publishing',
}

function fmt(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function Integrations() {
  const [connectors, setConnectors] = useState([])
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState(null)
  const [openForm, setOpenForm] = useState(null)
  const [formValues, setFormValues] = useState({})

  const load = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/integrations/connectors')
      setConnectors(res.data.connectors || [])
      setOffline(false)
    } catch {
      setOffline(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const openConfigure = (connector) => {
    setOpenForm(connector.name)
    setFormValues({})
  }

  const submitConfigure = async (e, connector) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post(`/api/v1/integrations/connectors/${connector.name}/configure`, formValues)
      setNotice(`${connector.label} configured`)
      setOpenForm(null)
      setFormValues({})
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || `Failed to configure ${connector.label}`)
    } finally {
      setBusy(false)
    }
  }

  const removeConnector = async (connector) => {
    setBusy(true)
    try {
      await api.delete(`/api/v1/integrations/connectors/${connector.name}`)
      setNotice(`${connector.label} credentials removed`)
      await load()
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <div className="loading">Loading integrations…</div>

  const byCategory = {}
  for (const c of connectors) {
    byCategory[c.category] = byCategory[c.category] || []
    byCategory[c.category].push(c)
  }
  const configuredCount = connectors.filter(c => c.configured).length

  return (
    <div>
      <h1>Integrations</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Every connector this platform knows about, in one place. Credentials
        you enter here are encrypted at rest and survive a restart — no
        re-entering an SMTP password after every deploy.
      </p>

      {offline && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>
          Backend offline — start the API on port 8000
        </div>
      )}
      {notice && (
        <div className="card" style={{ borderLeft: '4px solid #667eea', padding: '1rem 2rem' }}>
          {String(notice)}
          <button className="btn btn-secondary" style={{ marginLeft: '1rem', padding: '0.2rem 0.6rem' }}
            onClick={() => setNotice(null)}>dismiss</button>
        </div>
      )}

      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className="stat-label">Connectors</div>
          <div className="stat-number">{connectors.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Configured</div>
          <div className="stat-number">{configuredCount}</div>
        </div>
      </div>

      {Object.entries(byCategory).map(([category, items]) => (
        <div className="card" key={category}>
          <h2 className="card-title">{CATEGORY_LABELS[category] || category}</h2>
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {items.map(c => (
              <div key={c.name} style={{ border: '1px solid #eee', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{c.label}</strong>
                    {c.source === 'env' && (
                      <span style={{ color: '#999', fontSize: '0.8rem', marginLeft: '0.6rem' }}>
                        via env: {c.env_vars.join(', ')}
                      </span>
                    )}
                    {c.configured && c.updated_at && (
                      <span style={{ color: '#999', fontSize: '0.8rem', marginLeft: '0.6rem' }}>
                        · configured {fmt(c.updated_at)}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className={`badge ${c.configured ? 'badge-success' : 'badge-warning'}`}>
                      {c.configured ? 'configured' : 'not configured'}
                    </span>
                    {c.source === 'vault' && (
                      <>
                        <button className="btn btn-secondary" style={{ padding: '0.35rem 0.7rem', fontSize: '0.8rem' }}
                          onClick={() => openForm === c.name ? setOpenForm(null) : openConfigure(c)}>
                          {openForm === c.name ? 'Cancel' : c.configured ? 'Reconfigure' : 'Configure'}
                        </button>
                        {c.configured && (
                          <button className="btn btn-secondary" style={{ padding: '0.35rem 0.7rem', fontSize: '0.8rem', color: '#D62828' }}
                            disabled={busy} onClick={() => removeConnector(c)}>
                            Remove
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {openForm === c.name && (
                  <form onSubmit={e => submitConfigure(e, c)} style={{ marginTop: '1rem', display: 'grid', gap: '0.6rem' }}>
                    {c.fields.map(f => (
                      <div key={f.key} className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.85rem' }}>{f.label}</label>
                        <input
                          type={f.type === 'password' ? 'password' : f.type === 'number' ? 'number' : 'text'}
                          value={formValues[f.key] || ''}
                          onChange={e => setFormValues({ ...formValues, [f.key]: e.target.value })}
                          style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', width: '100%' }}
                        />
                      </div>
                    ))}
                    <button type="submit" className="btn btn-primary" disabled={busy} style={{ justifySelf: 'start' }}>
                      Save
                    </button>
                  </form>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
