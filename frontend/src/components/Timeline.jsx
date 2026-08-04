import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const TYPE_OPTIONS = [
  { value: 'note', label: 'Note' },
  { value: 'task', label: 'Task' },
  { value: 'call', label: 'Call' },
  { value: 'meeting', label: 'Meeting' },
  { value: 'email', label: 'Email' },
]

const TYPE_ICON = {
  note: '📝', task: '✅', call: '📞', meeting: '🗓️',
  email: '✉️', whatsapp: '💬', linkedin_message: '💼',
}

function fmt(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

/** Activity timeline (notes/tasks/calls) for a contact and/or a deal. */
export default function Timeline({ contactId, dealId }) {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({ activity_type: 'note', subject: '', body: '', due_date: '' })

  const load = useCallback(async () => {
    const params = {}
    if (contactId) params.contact_id = contactId
    if (dealId) params.deal_id = dealId
    try {
      const res = await api.get('/api/v1/crm/activities', { params })
      setActivities(res.data.activities || [])
    } catch {
      // leave prior state — page-level error banners cover offline API
    } finally {
      setLoading(false)
    }
  }, [contactId, dealId])

  useEffect(() => { load() }, [load])

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/api/v1/crm/activities', {
        contact_id: contactId || null,
        deal_id: dealId || null,
        activity_type: form.activity_type,
        subject: form.subject,
        body: form.body || null,
        due_date: form.activity_type === 'task' && form.due_date
          ? new Date(form.due_date).toISOString() : null,
      })
      setForm({ activity_type: 'note', subject: '', body: '', due_date: '' })
      setShowForm(false)
      await load()
    } finally {
      setBusy(false)
    }
  }

  const complete = async (id) => {
    await api.post(`/api/v1/crm/activities/${id}/complete`)
    await load()
  }

  const now = Date.now()

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="card-title" style={{ marginBottom: 0 }}>Timeline</h2>
        <button className="btn btn-secondary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Note / Task'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={submit} style={{ margin: '1rem 0', display: 'grid', gap: '0.75rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: form.activity_type === 'task' ? '1fr 1fr' : '1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>Type</label>
              <select value={form.activity_type}
                onChange={e => setForm({ ...form, activity_type: e.target.value })}>
                {TYPE_OPTIONS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            {form.activity_type === 'task' && (
              <div className="form-group">
                <label>Due date</label>
                <input type="datetime-local" value={form.due_date}
                  onChange={e => setForm({ ...form, due_date: e.target.value })} />
              </div>
            )}
          </div>
          <div className="form-group">
            <label>Subject</label>
            <input type="text" required value={form.subject}
              placeholder={form.activity_type === 'task' ? 'e.g. Send proposal' : 'e.g. Called, left voicemail'}
              onChange={e => setForm({ ...form, subject: e.target.value })} />
          </div>
          <div className="form-group">
            <label>Details (optional)</label>
            <textarea rows={2} value={form.body}
              onChange={e => setForm({ ...form, body: e.target.value })}
              style={{ width: '100%', padding: '0.6rem', border: '1px solid #ddd', borderRadius: '4px', fontFamily: 'inherit' }} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={busy || !form.subject.trim()}>
            {busy ? 'Saving…' : 'Save'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="loading">Loading timeline…</div>
      ) : activities.length === 0 ? (
        <div className="empty-state">
          <h3>No activity yet</h3>
          <p>Log a note or task to start the timeline.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem', marginTop: '1rem' }}>
          {activities.map(a => {
            const overdue = a.activity_type === 'task' && !a.is_completed
              && a.due_date && new Date(a.due_date).getTime() < now
            return (
              <div key={a.id} style={{
                display: 'flex', gap: '0.75rem', padding: '0.75rem',
                border: '1px solid #eee', borderRadius: '8px',
                backgroundColor: a.is_completed ? '#fafafa' : 'white',
              }}>
                <div style={{ fontSize: '1.1rem' }}>{TYPE_ICON[a.activity_type] || '•'}</div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontWeight: 600,
                    textDecoration: a.is_completed ? 'line-through' : 'none',
                    color: a.is_completed ? '#999' : '#222',
                  }}>
                    {a.subject || a.activity_type}
                  </div>
                  {a.body && <div style={{ color: '#666', fontSize: '0.9rem', marginTop: '0.2rem' }}>{a.body}</div>}
                  <div style={{ fontSize: '0.8rem', color: '#999', marginTop: '0.3rem' }}>
                    {fmt(a.created_at)}
                    {a.due_date && !a.is_completed && (
                      <span style={{ marginLeft: '0.5rem', color: overdue ? '#D62828' : '#999' }}>
                        · due {fmt(a.due_date)}{overdue ? ' (overdue)' : ''}
                      </span>
                    )}
                    {a.is_completed && a.completed_at && (
                      <span style={{ marginLeft: '0.5rem' }}>· completed {fmt(a.completed_at)}</span>
                    )}
                  </div>
                </div>
                {a.activity_type === 'task' && !a.is_completed && (
                  <button className="btn btn-secondary" style={{ alignSelf: 'start', padding: '0.35rem 0.7rem', fontSize: '0.8rem' }}
                    onClick={() => complete(a.id)}>
                    Mark done
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
