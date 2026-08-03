import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const EMPTY_FORM = { first_name: '', last_name: '', email: '', phone: '', title: '', status: 'prospect' }

const STATUS_OPTIONS = ['lead', 'prospect', 'qualified', 'customer', 'churned']

export default function Contacts() {
  const [contacts, setContacts] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const params = { limit: 200 }
      if (search.trim()) params.search = search.trim()
      const res = await api.get('/api/v1/crm/contacts', { params })
      setContacts(res.data.contacts || [])
      setError(null)
    } catch {
      setError('Backend offline — start the API on port 8000')
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => { load() }, [load])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/api/v1/crm/contacts', formData)
      setFormData(EMPTY_FORM)
      setShowForm(false)
      setError(null)
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create contact')
    } finally {
      setBusy(false)
    }
  }

  const badgeClass = (status) =>
    status === 'qualified' || status === 'customer' ? 'badge-success' :
    status === 'churned' ? 'badge-danger' : 'badge-warning'

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: 0 }}>Contacts</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Contact'}
        </button>
      </div>

      {error && <div className="card" style={{ borderLeft: '4px solid #D62828' }}>{String(error)}</div>}

      {showForm && (
        <div className="card">
          <h2 className="card-title">New Contact</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>First Name</label>
                <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input type="tel" name="phone" value={formData.phone} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>Title</label>
                <input type="text" name="title" value={formData.title} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select name="status" value={formData.status} onChange={handleChange}>
                  {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? 'Saving…' : 'Save Contact'}
            </button>
          </form>
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>All Contacts ({contacts.length})</h2>
          <input
            type="search"
            placeholder="Search name or email…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ padding: '0.6rem', border: '1px solid #ddd', borderRadius: '4px', minWidth: '220px' }}
          />
        </div>

        {loading ? (
          <div className="loading">Loading contacts…</div>
        ) : contacts.length === 0 ? (
          <div className="empty-state">
            <h3>No contacts found</h3>
            <p>Add a contact — the heartbeat scores new contacts automatically.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th><th>Email</th><th>Title</th><th>Lead Score</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map(c => (
                <tr key={c.id}>
                  <td><strong>{c.name}</strong></td>
                  <td>{c.email}</td>
                  <td>{c.title || '—'}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ backgroundColor: '#f0f0f0', borderRadius: '4px', height: '6px', width: '60px', overflow: 'hidden' }}>
                        <div style={{
                          backgroundColor: c.lead_score >= 70 ? '#06A77D' : '#667eea',
                          height: '100%',
                          width: `${Math.min(c.lead_score, 100)}%`,
                        }} />
                      </div>
                      {c.lead_score}
                    </div>
                  </td>
                  <td><span className={`badge ${badgeClass(c.status)}`}>{c.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
