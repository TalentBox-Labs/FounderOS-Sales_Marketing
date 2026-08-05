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

const MARKETING_AGENT_GROUPS = [
  {
    title: 'Research & Monitoring', agents: [
      { key: 'market_research', label: 'Market Research', endpoint: 'market-research',
        blurb: 'Competitors, trends, and pain points from real Reddit + Hacker News signals.',
        fields: [{ key: 'query', label: 'Topic', placeholder: 'e.g. CRM software for staffing agencies' }] },
      { key: 'community', label: 'Community Engagement', endpoint: 'community-engagement',
        blurb: 'Finds relevant Reddit discussions and drafts thoughtful (non-pitchy) replies.',
        fields: [{ key: 'query', label: 'Topic', placeholder: 'e.g. staffing agency software' }] },
      { key: 'brand', label: 'Brand Monitoring', endpoint: 'brand-monitoring',
        blurb: 'Scans Reddit for brand mentions and flags negative sentiment.',
        fields: [{ key: 'brand_name', label: 'Brand name', placeholder: 'e.g. WorkCrew' }] },
      { key: 'partnership', label: 'Partnership & Influencer', endpoint: 'partnership/discover',
        blurb: 'Discovers potential partners/podcasts/communities via Reddit + HN.',
        fields: [{ key: 'query', label: 'Topic', placeholder: 'e.g. B2B SaaS podcasts' }] },
    ],
  },
  {
    title: 'Strategy & Planning', agents: [
      { key: 'persona', label: 'Customer Persona', endpoint: 'persona/update',
        blurb: 'Refreshes the buyer persona from real CRM data.', fields: [] },
      { key: 'content_strategy', label: 'Content Strategy', endpoint: 'content-strategy',
        blurb: 'A content calendar grounded in tracked SEO keywords and active goals.',
        fields: [{ key: 'business_context', label: 'Business context', placeholder: 'e.g. B2B CRM for staffing agencies' }] },
      { key: 'seo_strategy', label: 'SEO Strategy', endpoint: 'seo-strategy',
        blurb: 'Keyword gaps, topic clusters, and linking opportunities from tracked keywords.',
        fields: [{ key: 'business_context', label: 'Business context', placeholder: 'optional' }] },
      { key: 'geo', label: 'GEO (AI Search)', endpoint: 'geo',
        blurb: 'Evaluates content for ChatGPT/Claude/Gemini/Perplexity visibility.',
        fields: [{ key: 'title', label: 'Title' }, { key: 'content', label: 'Content excerpt' }] },
      { key: 'product_marketing', label: 'Product Marketing', endpoint: 'product-marketing',
        blurb: 'Launch announcement, one-pager, demo talking points for a feature.',
        fields: [{ key: 'feature', label: 'Feature / launch' }] },
    ],
  },
  {
    title: 'Content Creation', agents: [
      { key: 'content_writer', label: 'Content Writer', endpoint: 'content-writer',
        blurb: 'Writes a blog post and publishes it to the Knowledge Base.',
        fields: [{ key: 'topic', label: 'Topic' }], extraBody: { content_type: 'blog post', publish: true } },
      { key: 'linkedin_content', label: 'LinkedIn Content', endpoint: 'linkedin-content',
        blurb: 'Founder-voice post, filed for approval before posting.',
        fields: [{ key: 'topic', label: 'Topic' }], extraBody: { post_type: 'educational' } },
      { key: 'social_media', label: 'Social Media', endpoint: 'social-media',
        blurb: 'Platform-native variants for LinkedIn/X/Instagram, filed for approval.',
        fields: [{ key: 'topic', label: 'Topic' }], extraBody: { platforms: ['linkedin', 'x', 'instagram'] } },
      { key: 'video_strategy', label: 'Video Strategy', endpoint: 'video-strategy',
        blurb: 'Hook, talking points, B-roll, and caption for a short video.',
        fields: [{ key: 'topic', label: 'Topic' }] },
      { key: 'creative_design', label: 'Creative Design', endpoint: 'creative-design',
        blurb: 'A creative brief for a designer or image-gen tool.',
        fields: [{ key: 'topic', label: 'Topic' }], extraBody: { asset_type: 'social graphic' } },
    ],
  },
  {
    title: 'Campaigns & Automation', agents: [
      { key: 'email_campaign', label: 'Email Marketing', endpoint: 'email-campaign',
        blurb: 'Drafts a campaign email, filed for approval before sending.',
        fields: [{ key: 'context', label: 'Campaign context', placeholder: 'e.g. monthly product update' }], extraBody: { campaign_type: 'newsletter' } },
      { key: 'whatsapp_campaign', label: 'WhatsApp Marketing', endpoint: 'whatsapp-campaign',
        blurb: 'Drafts a WhatsApp campaign, filed for approval before sending.',
        fields: [{ key: 'context', label: 'Campaign context', placeholder: 'e.g. webinar reminder' }], extraBody: { campaign_type: 'promotional' } },
      { key: 'campaign_manager', label: 'Campaign Manager', endpoint: 'campaign/plan',
        blurb: 'Plans a multi-channel campaign with a timeline and KPIs.',
        fields: [{ key: 'name', label: 'Campaign name' }, { key: 'goal', label: 'Goal' }],
        extraBody: { channels: ['seo', 'email', 'linkedin', 'social'] } },
      { key: 'automation', label: 'Marketing Automation', endpoint: 'automation/trigger',
        blurb: 'Fires a named n8n workflow with real payload data.',
        fields: [{ key: 'workflow_name', label: 'n8n workflow name', placeholder: 'e.g. publish-content' }], extraBody: { payload: {} } },
    ],
  },
  {
    title: 'Analytics & Optimization', agents: [
      { key: 'analytics', label: 'Analytics & Attribution', endpoint: 'analytics-report',
        blurb: 'Real attribution, LTV, CAC, and an executive summary.', fields: [] },
      { key: 'cro', label: 'Conversion Rate Optimization', endpoint: 'cro',
        blurb: 'Recommendations from the real deal-stage funnel.', fields: [] },
    ],
  },
]

function resultLines(result) {
  if (!result) return []
  const skip = new Set(['ok', 'configured'])
  return Object.entries(result)
    .filter(([k]) => !skip.has(k))
    .map(([k, v]) => {
      const label = k.replace(/_/g, ' ')
      let val = v
      if (Array.isArray(val)) val = val.length ? val.map(x => (typeof x === 'object' ? JSON.stringify(x) : x)).join('; ') : '(none)'
      else if (val && typeof val === 'object') val = JSON.stringify(val)
      return { label, val: String(val ?? '') }
    })
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

  // Marketing Agent Crew
  const [orchestratorContext, setOrchestratorContext] = useState('')
  const [orchestratorBusy, setOrchestratorBusy] = useState(false)
  const [orchestratorResult, setOrchestratorResult] = useState(null)
  const [agentInputs, setAgentInputs] = useState({})
  const [agentBusy, setAgentBusy] = useState({})
  const [agentResults, setAgentResults] = useState({})

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

  const runOrchestrator = async () => {
    setOrchestratorBusy(true)
    setOrchestratorResult(null)
    try {
      const res = await api.post('/api/v1/marketing-agents/orchestrator/run', { business_context: orchestratorContext })
      setOrchestratorResult(res.data)
      await load()
    } catch (err) {
      setOrchestratorResult({ ok: false, error: err.response?.data?.detail || 'Orchestrator run failed' })
    } finally {
      setOrchestratorBusy(false)
    }
  }

  const runAgent = async (agent) => {
    const body = { ...(agent.extraBody || {}) }
    for (const f of agent.fields) body[f.key] = (agentInputs[`${agent.key}.${f.key}`] || '').trim()
    setAgentBusy(prev => ({ ...prev, [agent.key]: true }))
    setAgentResults(prev => ({ ...prev, [agent.key]: null }))
    try {
      const res = await api.post(`/api/v1/marketing-agents/${agent.endpoint}`, body)
      setAgentResults(prev => ({ ...prev, [agent.key]: res.data }))
      if (['content_writer', 'persona', 'campaign_manager'].includes(agent.key)) await load()
    } catch (err) {
      setAgentResults(prev => ({ ...prev, [agent.key]: { ok: false, reason: err.response?.data?.detail || 'Agent failed' } }))
    } finally {
      setAgentBusy(prev => ({ ...prev, [agent.key]: false }))
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

      <div className="card" style={{ borderLeft: '4px solid #667eea' }}>
        <h2 className="card-title">Marketing Orchestrator — the AI CMO</h2>
        <p style={{ color: '#666', fontSize: '0.85rem', marginTop: '-0.5rem', marginBottom: '1rem' }}>
          Runs the full pipeline: research → persona → content strategy → SEO/writer/video → creative/social →
          email/WhatsApp → campaign → automation → analytics. Also runs automatically once a day.
        </p>
        <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1rem' }}>
          <input type="text" value={orchestratorContext} onChange={e => setOrchestratorContext(e.target.value)}
            placeholder="Business context (optional) — e.g. B2B CRM for staffing agencies"
            style={{ flex: 1, padding: '0.6rem', border: '1px solid #ddd', borderRadius: '4px' }} />
          <button className="btn btn-primary" disabled={orchestratorBusy} onClick={runOrchestrator}>
            {orchestratorBusy ? 'Running full cycle…' : 'Run Marketing Cycle'}
          </button>
        </div>
        {orchestratorResult && (
          <div style={{ padding: '1rem', backgroundColor: '#f8f9ff', borderRadius: '8px', fontSize: '0.85rem' }}>
            {!orchestratorResult.ok && <p style={{ color: '#D62828' }}>{orchestratorResult.error}</p>}
            {orchestratorResult.ok && (
              <>
                <p style={{ fontWeight: 600, marginTop: 0 }}>{orchestratorResult.executive_summary}</p>
                <table className="table">
                  <thead><tr><th>Stage</th><th>Result</th></tr></thead>
                  <tbody>
                    {Object.entries(orchestratorResult.stages || {}).map(([stage, data]) => (
                      <tr key={stage}>
                        <td style={{ textTransform: 'capitalize', whiteSpace: 'nowrap' }}>{stage.replace(/_/g, ' ')}</td>
                        <td style={{ color: '#444' }}>
                          {resultLines(data).slice(0, 2).map(l => `${l.label}: ${l.val}`).join(' · ').slice(0, 200) || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
        )}
      </div>

      {MARKETING_AGENT_GROUPS.map(group => (
        <div className="card" key={group.title}>
          <h2 className="card-title">{group.title}</h2>
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {group.agents.map(agent => (
              <div key={agent.key} style={{ border: '1px solid #eee', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
                  <div style={{ flex: '1 1 260px' }}>
                    <strong>{agent.label}</strong>
                    <p style={{ margin: '0.2rem 0 0.6rem', color: '#666', fontSize: '0.85rem' }}>{agent.blurb}</p>
                    {agent.fields.length > 0 && (
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {agent.fields.map(f => (
                          <input key={f.key} type="text"
                            value={agentInputs[`${agent.key}.${f.key}`] || ''}
                            onChange={e => setAgentInputs(prev => ({ ...prev, [`${agent.key}.${f.key}`]: e.target.value }))}
                            placeholder={f.placeholder || f.label}
                            style={{ padding: '0.45rem', border: '1px solid #ddd', borderRadius: '4px', minWidth: '180px', flex: 1 }} />
                        ))}
                      </div>
                    )}
                  </div>
                  <button className="btn btn-secondary" style={{ whiteSpace: 'nowrap' }}
                    disabled={agentBusy[agent.key]} onClick={() => runAgent(agent)}>
                    {agentBusy[agent.key] ? 'Working…' : 'Run'}
                  </button>
                </div>
                {agentResults[agent.key] && (
                  <div style={{ marginTop: '0.75rem', padding: '0.8rem', backgroundColor: agentResults[agent.key].ok === false ? '#fff2f2' : '#f8f9ff', borderRadius: '6px', fontSize: '0.82rem' }}>
                    {agentResults[agent.key].ok === false ? (
                      <span style={{ color: '#D62828' }}>{agentResults[agent.key].reason || agentResults[agent.key].error || 'No result'}</span>
                    ) : (
                      <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
                        {resultLines(agentResults[agent.key]).map((l, i) => (
                          <li key={i}><strong style={{ textTransform: 'capitalize' }}>{l.label}:</strong> {l.val.slice(0, 300)}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

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
