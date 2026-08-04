import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const EMPTY_BROADCAST = { name: '', message: '', tag: '' }
const EMPTY_CONTACT = { phone: '', name: '', tags: '' }

export default function Marketing() {
  const [contacts, setContacts] = useState([])
  const [broadcasts, setBroadcasts] = useState([])
  const [broadcastForm, setBroadcastForm] = useState(EMPTY_BROADCAST)
  const [contactForm, setContactForm] = useState(EMPTY_CONTACT)
  const [showBroadcastForm, setShowBroadcastForm] = useState(false)
  const [showContactForm, setShowContactForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState(null)
  const [offline, setOffline] = useState(false)

  const load = useCallback(async () => {
    try {
      const [contactsRes, broadcastsRes] = await Promise.all([
        api.get('/api/v1/whatsapp/contacts'),
        api.get('/api/v1/whatsapp/broadcasts'),
      ])
      setContacts(contactsRes.data.contacts || contactsRes.data.data || [])
      setBroadcasts(broadcastsRes.data.broadcasts || broadcastsRes.data.data || [])
      setOffline(false)
    } catch {
      setOffline(true)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const addContact = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/api/v1/whatsapp/contacts', {
        phone: contactForm.phone,
        name: contactForm.name,
        tags: contactForm.tags ? contactForm.tags.split(',').map(t => t.trim()) : [],
      })
      setContactForm(EMPTY_CONTACT)
      setShowContactForm(false)
      setNotice('Contact added')
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Failed to add contact')
    } finally {
      setBusy(false)
    }
  }

  const createBroadcast = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/api/v1/whatsapp/broadcasts', {
        name: broadcastForm.name,
        message: broadcastForm.message,
        target_tag: broadcastForm.tag || null,
      })
      setBroadcastForm(EMPTY_BROADCAST)
      setShowBroadcastForm(false)
      setNotice('Broadcast created (draft)')
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Failed to create broadcast')
    } finally {
      setBusy(false)
    }
  }

  const sendBroadcast = async (id) => {
    setBusy(true)
    try {
      await api.post(`/api/v1/whatsapp/broadcasts/${id}/send`)
      setNotice('Broadcast sent')
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Send failed — is the WhatsApp API configured?')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1>Marketing — WhatsApp</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Broadcast campaigns and audience management. Email sequences run through
        n8n via the automation loop; outreach emails appear in Approvals.
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
          <div className="stat-label">WhatsApp Contacts</div>
          <div className="stat-number">{contacts.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Broadcast Campaigns</div>
          <div className="stat-number">{broadcasts.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Sent</div>
          <div className="stat-number">
            {broadcasts.filter(b => (b.status || '').includes('sent') || (b.status || '').includes('completed')).length}
          </div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>Broadcasts</h2>
          <button className="btn btn-primary" onClick={() => setShowBroadcastForm(!showBroadcastForm)}>
            {showBroadcastForm ? 'Cancel' : '+ New Broadcast'}
          </button>
        </div>

        {showBroadcastForm && (
          <form onSubmit={createBroadcast} style={{ marginTop: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Campaign Name</label>
                <input type="text" required value={broadcastForm.name}
                  onChange={e => setBroadcastForm({ ...broadcastForm, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Target Tag (optional)</label>
                <input type="text" placeholder="e.g. customers" value={broadcastForm.tag}
                  onChange={e => setBroadcastForm({ ...broadcastForm, tag: e.target.value })} />
              </div>
            </div>
            <div className="form-group">
              <label>Message</label>
              <textarea rows="3" required value={broadcastForm.message}
                onChange={e => setBroadcastForm({ ...broadcastForm, message: e.target.value })} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>Create Draft</button>
          </form>
        )}

        {broadcasts.length === 0 ? (
          <div className="empty-state">
            <h3>No broadcasts yet</h3>
            <p>Create a campaign draft, then send it to your tagged audience.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Campaign</th><th>Status</th><th>Recipients</th><th></th></tr>
            </thead>
            <tbody>
              {broadcasts.map(b => (
                <tr key={b.id || b.broadcast_id}>
                  <td><strong>{b.name}</strong></td>
                  <td><span className="badge badge-warning">{b.status || 'draft'}</span></td>
                  <td>{b.recipient_count ?? b.recipients?.length ?? '—'}</td>
                  <td>
                    {(b.status || 'draft') === 'draft' && (
                      <button className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                        disabled={busy} onClick={() => sendBroadcast(b.id || b.broadcast_id)}>
                        Send
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>Audience ({contacts.length})</h2>
          <button className="btn btn-primary" onClick={() => setShowContactForm(!showContactForm)}>
            {showContactForm ? 'Cancel' : '+ Add Contact'}
          </button>
        </div>

        {showContactForm && (
          <form onSubmit={addContact} style={{ marginTop: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Phone (with country code)</label>
                <input type="tel" required placeholder="+15550101" value={contactForm.phone}
                  onChange={e => setContactForm({ ...contactForm, phone: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Name</label>
                <input type="text" required value={contactForm.name}
                  onChange={e => setContactForm({ ...contactForm, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Tags (comma-separated)</label>
                <input type="text" placeholder="customers, beta" value={contactForm.tags}
                  onChange={e => setContactForm({ ...contactForm, tags: e.target.value })} />
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>Add Contact</button>
          </form>
        )}

        {contacts.length === 0 ? (
          <p style={{ color: '#999', marginTop: '1rem' }}>
            No WhatsApp contacts yet. Add contacts here or sync them via the API.
          </p>
        ) : (
          <table className="table">
            <thead><tr><th>Name</th><th>Phone</th><th>Tags</th></tr></thead>
            <tbody>
              {contacts.map((c, i) => (
                <tr key={c.phone || i}>
                  <td><strong>{c.name}</strong></td>
                  <td>{c.phone}</td>
                  <td>{Array.isArray(c.tags) ? c.tags.join(', ') : (c.tags || '—')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
