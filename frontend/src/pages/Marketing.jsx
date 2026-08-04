import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const EMPTY_BROADCAST = { name: '', message: '', tag: '' }
const EMPTY_CONTACT = { phone: '', name: '', tags: '' }
const EMPTY_SEQUENCE = { name: '', channel: 'email' }
const EMPTY_STEP = { delay_days: '1', subject: '', template: '', action_type: 'send_email' }
const EMPTY_KEYWORD = { keyword: '', target_url: '', geo: '', target_rank: '' }
const EMPTY_CHECK = { rank: '', ai_visible: false, notes: '' }

function trendBadge(trend) {
  if (trend === null || trend === undefined) return <span style={{ color: '#999' }}>—</span>
  if (trend > 0) return <span style={{ color: '#06A77D' }}>▲ {trend}</span>
  if (trend < 0) return <span style={{ color: '#D62828' }}>▼ {Math.abs(trend)}</span>
  return <span style={{ color: '#999' }}>= 0</span>
}

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

  // Email sequences
  const [sequences, setSequences] = useState([])
  const [crmContacts, setCrmContacts] = useState([])
  const [showSequenceForm, setShowSequenceForm] = useState(false)
  const [sequenceForm, setSequenceForm] = useState(EMPTY_SEQUENCE)
  const [expandedSeq, setExpandedSeq] = useState(null)
  const [sequenceDetail, setSequenceDetail] = useState(null)
  const [stepForm, setStepForm] = useState(EMPTY_STEP)
  const [enrollContactId, setEnrollContactId] = useState('')

  // SEO / GEO tracking
  const [keywords, setKeywords] = useState([])
  const [showKeywordForm, setShowKeywordForm] = useState(false)
  const [keywordForm, setKeywordForm] = useState(EMPTY_KEYWORD)
  const [checkFormFor, setCheckFormFor] = useState(null)
  const [checkForm, setCheckForm] = useState(EMPTY_CHECK)

  const load = useCallback(async () => {
    try {
      const [contactsRes, broadcastsRes, sequencesRes, crmContactsRes, keywordsRes] = await Promise.all([
        api.get('/api/v1/whatsapp/contacts'),
        api.get('/api/v1/whatsapp/broadcasts'),
        api.get('/api/v1/outreach/sequences'),
        api.get('/api/v1/crm/contacts', { params: { limit: 200 } }),
        api.get('/api/v1/seo/keywords'),
      ])
      setContacts(contactsRes.data.contacts || contactsRes.data.data || [])
      setBroadcasts(broadcastsRes.data.broadcasts || broadcastsRes.data.data || [])
      setSequences(sequencesRes.data.sequences || [])
      setCrmContacts(crmContactsRes.data.contacts || [])
      setKeywords(keywordsRes.data.keywords || [])
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

  // --- Sequences ---

  const createSequence = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/api/v1/outreach/sequences', sequenceForm)
      setSequenceForm(EMPTY_SEQUENCE)
      setShowSequenceForm(false)
      setNotice('Sequence created — add steps, then enroll a contact')
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Failed to create sequence')
    } finally {
      setBusy(false)
    }
  }

  const toggleSequence = async (seq) => {
    if (expandedSeq === seq.id) {
      setExpandedSeq(null)
      setSequenceDetail(null)
      return
    }
    setExpandedSeq(seq.id)
    setEnrollContactId('')
    try {
      const res = await api.get(`/api/v1/outreach/sequences/${seq.id}`)
      setSequenceDetail(res.data.sequence)
    } catch {
      setSequenceDetail(null)
    }
  }

  const addStep = async (e, seqId) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post(`/api/v1/outreach/sequences/${seqId}/steps`, {
        ...stepForm,
        delay_days: parseInt(stepForm.delay_days || '0', 10),
      })
      setStepForm(EMPTY_STEP)
      const res = await api.get(`/api/v1/outreach/sequences/${seqId}`)
      setSequenceDetail(res.data.sequence)
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Failed to add step')
    } finally {
      setBusy(false)
    }
  }

  const enroll = async (seqId) => {
    if (!enrollContactId) return
    setBusy(true)
    try {
      const res = await api.post(`/api/v1/outreach/sequences/${seqId}/enroll`, { contact_id: enrollContactId })
      setNotice(`Enrolled ${res.data.contact} — ${res.data.tasks_created} touch(es) scheduled`)
      setEnrollContactId('')
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Enroll failed')
    } finally {
      setBusy(false)
    }
  }

  // --- SEO / GEO ---

  const addKeyword = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/api/v1/seo/keywords', {
        ...keywordForm,
        target_rank: keywordForm.target_rank ? parseInt(keywordForm.target_rank, 10) : null,
      })
      setKeywordForm(EMPTY_KEYWORD)
      setShowKeywordForm(false)
      setNotice('Keyword tracked')
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Failed to add keyword')
    } finally {
      setBusy(false)
    }
  }

  const logCheck = async (e, keywordId) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post(`/api/v1/seo/keywords/${keywordId}/checks`, {
        ...checkForm,
        rank: checkForm.rank ? parseInt(checkForm.rank, 10) : null,
      })
      setCheckForm(EMPTY_CHECK)
      setCheckFormFor(null)
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Failed to log rank check')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1>Marketing</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        WhatsApp broadcasts, email sequences, and SEO/GEO keyword tracking —
        one place to run outbound and watch visibility.
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
          <div className="stat-label">Email Sequences</div>
          <div className="stat-number">{sequences.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Keywords Tracked</div>
          <div className="stat-number">{keywords.length}</div>
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

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>Email Sequences</h2>
          <button className="btn btn-primary" onClick={() => setShowSequenceForm(!showSequenceForm)}>
            {showSequenceForm ? 'Cancel' : '+ New Sequence'}
          </button>
        </div>
        <p style={{ color: '#999', fontSize: '0.9rem', marginTop: '0.3rem' }}>
          Enrolling a contact schedules each step as an activity on their timeline — no separate send engine.
        </p>

        {showSequenceForm && (
          <form onSubmit={createSequence} style={{ marginTop: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Sequence Name</label>
                <input type="text" required value={sequenceForm.name}
                  onChange={e => setSequenceForm({ ...sequenceForm, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Channel</label>
                <select value={sequenceForm.channel}
                  onChange={e => setSequenceForm({ ...sequenceForm, channel: e.target.value })}>
                  <option value="email">Email</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="whatsapp">WhatsApp</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>Create Sequence</button>
          </form>
        )}

        {sequences.length === 0 ? (
          <div className="empty-state">
            <h3>No sequences yet</h3>
            <p>Create a sequence, add steps, then enroll a qualified contact.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '1rem' }}>
            {sequences.map(seq => (
              <div key={seq.id} style={{ border: '1px solid #eee', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                  onClick={() => toggleSequence(seq)}>
                  <div>
                    <strong>{seq.name}</strong>
                    <span style={{ color: '#999', marginLeft: '0.75rem', fontSize: '0.85rem' }}>
                      {seq.channel} · {seq.steps_count} step(s)
                    </span>
                  </div>
                  <span className={`badge ${seq.is_active ? 'badge-success' : 'badge-warning'}`}>
                    {seq.is_active ? 'active' : 'paused'}
                  </span>
                </div>

                {expandedSeq === seq.id && sequenceDetail && (
                  <div style={{ marginTop: '1rem', borderTop: '1px solid #eee', paddingTop: '1rem' }}>
                    {sequenceDetail.steps.length === 0 ? (
                      <p style={{ color: '#999' }}>No steps yet.</p>
                    ) : (
                      <ol style={{ paddingLeft: '1.2rem', margin: '0 0 1rem', color: '#444' }}>
                        {sequenceDetail.steps.map(st => (
                          <li key={st.id} style={{ marginBottom: '0.4rem' }}>
                            <strong>{st.subject || '(no subject)'}</strong>
                            <span style={{ color: '#999' }}> — day {st.delay_days} · {st.action_type}</span>
                          </li>
                        ))}
                      </ol>
                    )}

                    <form onSubmit={e => addStep(e, seq.id)} style={{ display: 'grid', gap: '0.6rem', marginBottom: '1rem' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '0.6rem' }}>
                        <input type="text" placeholder="Subject" value={stepForm.subject}
                          onChange={e => setStepForm({ ...stepForm, subject: e.target.value })}
                          style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                        <input type="number" min="0" placeholder="Delay (days)" value={stepForm.delay_days}
                          onChange={e => setStepForm({ ...stepForm, delay_days: e.target.value })}
                          style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                        <select value={stepForm.action_type}
                          onChange={e => setStepForm({ ...stepForm, action_type: e.target.value })}
                          style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                          <option value="send_email">Email</option>
                          <option value="linkedin_message">LinkedIn</option>
                          <option value="whatsapp">WhatsApp</option>
                          <option value="call">Call</option>
                        </select>
                      </div>
                      <textarea rows={2} placeholder="Template / talking points"
                        value={stepForm.template}
                        onChange={e => setStepForm({ ...stepForm, template: e.target.value })}
                        style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', fontFamily: 'inherit' }} />
                      <button type="submit" className="btn btn-secondary" disabled={busy || !stepForm.subject.trim()}
                        style={{ justifySelf: 'start' }}>
                        + Add Step
                      </button>
                    </form>

                    <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                      <select value={enrollContactId} onChange={e => setEnrollContactId(e.target.value)}
                        style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', flex: 1 }}>
                        <option value="">Select a contact to enroll…</option>
                        {crmContacts.map(c => (
                          <option key={c.id} value={c.id}>{c.name} ({c.email})</option>
                        ))}
                      </select>
                      <button className="btn btn-primary" disabled={busy || !enrollContactId}
                        onClick={() => enroll(seq.id)}>
                        Enroll
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>SEO & GEO Tracking</h2>
          <button className="btn btn-primary" onClick={() => setShowKeywordForm(!showKeywordForm)}>
            {showKeywordForm ? 'Cancel' : '+ Track Keyword'}
          </button>
        </div>
        <p style={{ color: '#999', fontSize: '0.9rem', marginTop: '0.3rem' }}>
          Log what you observe in search and AI answer engines (ChatGPT, Perplexity) — trend shows movement since the last check.
        </p>

        {showKeywordForm && (
          <form onSubmit={addKeyword} style={{ marginTop: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 2fr 1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Keyword</label>
                <input type="text" required value={keywordForm.keyword}
                  onChange={e => setKeywordForm({ ...keywordForm, keyword: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Target URL</label>
                <input type="text" value={keywordForm.target_url}
                  onChange={e => setKeywordForm({ ...keywordForm, target_url: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Geo</label>
                <input type="text" placeholder="e.g. United States" value={keywordForm.geo}
                  onChange={e => setKeywordForm({ ...keywordForm, geo: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Target Rank</label>
                <input type="number" min="1" value={keywordForm.target_rank}
                  onChange={e => setKeywordForm({ ...keywordForm, target_rank: e.target.value })} />
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>Track Keyword</button>
          </form>
        )}

        {keywords.length === 0 ? (
          <div className="empty-state">
            <h3>No keywords tracked yet</h3>
            <p>Add a keyword, then log rank checks over time to see the trend.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Keyword</th><th>Rank</th><th>Trend</th><th>Target</th><th>AI Visible</th><th>Last Checked</th><th></th></tr>
            </thead>
            <tbody>
              {keywords.map(k => (
                <React.Fragment key={k.id}>
                  <tr>
                    <td><strong>{k.keyword}</strong>{k.geo && <div style={{ color: '#999', fontSize: '0.8rem' }}>{k.geo}</div>}</td>
                    <td>{k.current_rank ?? '—'}</td>
                    <td>{trendBadge(k.trend)}</td>
                    <td>{k.target_rank ?? '—'}</td>
                    <td>{k.ai_visible ? <span className="badge badge-success">yes</span> : <span style={{ color: '#999' }}>no</span>}</td>
                    <td>{k.last_checked_at ? new Date(k.last_checked_at).toLocaleDateString() : 'never'}</td>
                    <td>
                      <button className="btn btn-secondary" style={{ padding: '0.35rem 0.7rem', fontSize: '0.8rem' }}
                        onClick={() => { setCheckFormFor(checkFormFor === k.id ? null : k.id); setCheckForm(EMPTY_CHECK) }}>
                        Log check
                      </button>
                    </td>
                  </tr>
                  {checkFormFor === k.id && (
                    <tr>
                      <td colSpan={7}>
                        <form onSubmit={e => logCheck(e, k.id)}
                          style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.75rem', backgroundColor: '#fafafa', borderRadius: '6px' }}>
                          <input type="number" min="1" placeholder="Rank (blank = not found)" value={checkForm.rank}
                            onChange={e => setCheckForm({ ...checkForm, rank: e.target.value })}
                            style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', width: '200px' }} />
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem' }}>
                            <input type="checkbox" checked={checkForm.ai_visible}
                              onChange={e => setCheckForm({ ...checkForm, ai_visible: e.target.checked })} />
                            Visible in AI answer engine
                          </label>
                          <input type="text" placeholder="Notes (optional)" value={checkForm.notes}
                            onChange={e => setCheckForm({ ...checkForm, notes: e.target.value })}
                            style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', flex: 1 }} />
                          <button type="submit" className="btn btn-primary" disabled={busy}>Save</button>
                        </form>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
