import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const PRESETS = [
  { key: 'lead-qualified', label: 'Lead Qualified → notify + task' },
  { key: 'deal-at-risk', label: 'Deal At Risk → alert owner' },
  { key: 'deal-closed', label: 'Deal Closed → celebrate + handoff' },
  { key: 'crew-completed', label: 'Crew Completed → publish content' },
]

const OPERATORS = ['eq', 'gte', 'lte', 'gt', 'lt', 'contains', 'in', 'exists']

const ACTION_FIELD_SPECS = {
  send_slack: [
    { key: 'channel', label: 'Channel', type: 'text', placeholder: '#sales' },
    { key: 'message', label: 'Message', type: 'textarea', placeholder: 'Use {field_name} to interpolate event data' },
  ],
  send_email: [
    { key: 'to', label: 'To', type: 'text' },
    { key: 'subject', label: 'Subject', type: 'text' },
    { key: 'body', label: 'Body', type: 'textarea' },
  ],
  send_webhook: [
    { key: 'url', label: 'Webhook URL', type: 'text' },
  ],
  create_task: [
    { key: 'title', label: 'Title', type: 'text' },
    { key: 'description', label: 'Description', type: 'textarea', placeholder: 'Use {field_name} to interpolate event data' },
    { key: 'due_in_hours', label: 'Due in (hours)', type: 'number' },
  ],
  create_activity: [
    { key: 'activity_type', label: 'Activity Type', type: 'select', options: ['note', 'task', 'call', 'meeting', 'email', 'whatsapp', 'linkedin_message'] },
    { key: 'subject', label: 'Subject', type: 'text' },
    { key: 'body', label: 'Body', type: 'textarea' },
  ],
  trigger_crew: [
    { key: 'crew_name', label: 'Crew Name', type: 'text', placeholder: 'marketing, generation…' },
  ],
  trigger_sdr: [],
  update_field: [
    { key: 'entity_type', label: 'Entity Type', type: 'text', placeholder: 'contact, deal' },
    { key: 'field', label: 'Field', type: 'text' },
    { key: 'value', label: 'Value', type: 'text' },
  ],
  add_tag: [{ key: 'tag', label: 'Tag', type: 'text' }],
  remove_tag: [{ key: 'tag', label: 'Tag', type: 'text' }],
  log_event: [],
}

const EMPTY_WORKFLOW = { name: '', description: '', event_type: '', enabled: true }

function ActionConfigFields({ actionType, config, onChange }) {
  const spec = ACTION_FIELD_SPECS[actionType] || []
  if (spec.length === 0) {
    return <p style={{ color: '#999', fontSize: '0.85rem', margin: 0 }}>No configuration needed for this action.</p>
  }
  return (
    <div style={{ display: 'grid', gap: '0.5rem' }}>
      {spec.map(f => (
        <div key={f.key} className="form-group" style={{ marginBottom: 0 }}>
          <label style={{ fontSize: '0.8rem' }}>{f.label}</label>
          {f.type === 'textarea' ? (
            <textarea rows={2} placeholder={f.placeholder} value={config[f.key] || ''}
              onChange={e => onChange({ ...config, [f.key]: e.target.value })}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', fontFamily: 'inherit' }} />
          ) : f.type === 'select' ? (
            <select value={config[f.key] || f.options[0]}
              onChange={e => onChange({ ...config, [f.key]: e.target.value })}
              style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', width: '100%' }}>
              {f.options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          ) : (
            <input type={f.type} placeholder={f.placeholder} value={config[f.key] || ''}
              onChange={e => onChange({ ...config, [f.key]: f.type === 'number' ? Number(e.target.value) : e.target.value })}
              style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', width: '100%' }} />
          )}
        </div>
      ))}
    </div>
  )
}

export default function Automation() {
  const [workflows, setWorkflows] = useState([])
  const [events, setEvents] = useState([])
  const [eventTypes, setEventTypes] = useState([])
  const [actionTypes, setActionTypes] = useState([])
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState(null)
  const [offline, setOffline] = useState(false)
  const [loading, setLoading] = useState(true)

  const [showBuilder, setShowBuilder] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [workflowForm, setWorkflowForm] = useState(EMPTY_WORKFLOW)
  const [conditions, setConditions] = useState([])
  const [actions, setActions] = useState([])

  const [expandedId, setExpandedId] = useState(null)
  const [executions, setExecutions] = useState([])

  const load = useCallback(async () => {
    const results = await Promise.allSettled([
      api.get('/api/v1/automation/workflows'),
      api.get('/api/v1/automation/events/history', { params: { limit: 25 } }),
      api.get('/api/v1/automation/events/types'),
      api.get('/api/v1/automation/actions/types'),
    ])
    const [wfRes, evRes, evtRes, actRes] = results
    if (wfRes.status === 'fulfilled') {
      setWorkflows(wfRes.value.data.workflows || [])
      setOffline(false)
    } else {
      setOffline(true)
    }
    if (evRes.status === 'fulfilled') {
      setEvents(evRes.value.data.events || evRes.value.data.history || [])
    }
    if (evtRes.status === 'fulfilled') {
      setEventTypes((evtRes.value.data.event_types || []).map(t => t.name))
    }
    if (actRes.status === 'fulfilled') {
      setActionTypes((actRes.value.data.action_types || []).map(t => t.name))
    }
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  const toggleWorkflow = async (id) => {
    setBusy(true)
    try {
      await api.put(`/api/v1/automation/workflows/${id}/toggle`)
      await load()
    } finally {
      setBusy(false)
    }
  }

  const deleteWorkflow = async (id) => {
    setBusy(true)
    try {
      await api.delete(`/api/v1/automation/workflows/${id}`)
      setNotice('Workflow deleted')
      await load()
    } finally {
      setBusy(false)
    }
  }

  const installPreset = async (key) => {
    setBusy(true)
    try {
      await api.post(`/api/v1/automation/workflows/presets/${key}`)
      setNotice(`Preset installed: ${key}`)
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || `Failed to install ${key}`)
    } finally {
      setBusy(false)
    }
  }

  const resetBuilder = () => {
    setEditingId(null)
    setWorkflowForm(EMPTY_WORKFLOW)
    setConditions([])
    setActions([])
  }

  const openNewBuilder = () => {
    resetBuilder()
    setShowBuilder(true)
  }

  const openEditBuilder = (wf) => {
    setEditingId(wf.workflow_id)
    setWorkflowForm({
      name: wf.name, description: wf.description || '',
      event_type: wf.event_type || '', enabled: wf.enabled,
    })
    setConditions(wf.conditions || [])
    setActions((wf.actions || []).map(a => ({ action_type: a.action_type, config: a.config || {}, enabled: a.enabled !== false })))
    setShowBuilder(true)
    setExpandedId(null)
  }

  const addCondition = () => setConditions([...conditions, { field: '', operator: 'eq', value: '' }])
  const updateCondition = (i, patch) => setConditions(conditions.map((c, idx) => idx === i ? { ...c, ...patch } : c))
  const removeCondition = (i) => setConditions(conditions.filter((_, idx) => idx !== i))

  const addAction = () => setActions([...actions, { action_type: actionTypes[0] || 'send_slack', config: {}, enabled: true }])
  const updateActionType = (i, actionType) => setActions(actions.map((a, idx) => idx === i ? { action_type: actionType, config: {}, enabled: true } : a))
  const updateActionConfig = (i, config) => setActions(actions.map((a, idx) => idx === i ? { ...a, config } : a))
  const removeAction = (i) => setActions(actions.filter((_, idx) => idx !== i))

  const saveWorkflow = async (e) => {
    e.preventDefault()
    setBusy(true)
    const payload = {
      name: workflowForm.name,
      description: workflowForm.description,
      event_type: workflowForm.event_type,
      enabled: workflowForm.enabled,
      conditions: conditions.filter(c => c.field),
      actions: actions.map(a => ({ action_type: a.action_type, config: a.config, enabled: a.enabled })),
    }
    try {
      if (editingId) {
        await api.put(`/api/v1/automation/workflows/${editingId}`, payload)
        setNotice('Workflow updated')
      } else {
        await api.post('/api/v1/automation/workflows', payload)
        setNotice('Workflow created')
      }
      resetBuilder()
      setShowBuilder(false)
      await load()
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Failed to save workflow')
    } finally {
      setBusy(false)
    }
  }

  const toggleExecutions = async (wf) => {
    if (expandedId === wf.workflow_id) {
      setExpandedId(null)
      return
    }
    setExpandedId(wf.workflow_id)
    try {
      const res = await api.get(`/api/v1/automation/workflows/${wf.workflow_id}/executions`)
      setExecutions(res.data.executions || [])
    } catch {
      setExecutions([])
    }
  }

  if (loading) return <div className="loading">Loading automation…</div>

  return (
    <div>
      <h1>Automation Rules</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Event-driven workflows: when something happens (lead qualified, deal at
        risk…), these rules decide what runs. The heartbeat and Hermes emit the
        events; n8n receives the bridged ones. Workflows are saved to the
        database, so they survive a restart.
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

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>Workflows ({workflows.length})</h2>
          <button className="btn btn-primary" onClick={() => showBuilder ? setShowBuilder(false) : openNewBuilder()}>
            {showBuilder ? 'Cancel' : '+ Build Workflow'}
          </button>
        </div>

        {showBuilder && (
          <form onSubmit={saveWorkflow} style={{ marginTop: '1.5rem', border: '1px solid #eee', borderRadius: '8px', padding: '1.25rem' }}>
            <h3 style={{ marginTop: 0 }}>{editingId ? 'Edit Workflow' : 'New Workflow'}</h3>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 2fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Name</label>
                <input type="text" required value={workflowForm.name}
                  onChange={e => setWorkflowForm({ ...workflowForm, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Description</label>
                <input type="text" value={workflowForm.description}
                  onChange={e => setWorkflowForm({ ...workflowForm, description: e.target.value })} />
              </div>
              <div className="form-group">
                <label>When this event fires…</label>
                <select required value={workflowForm.event_type}
                  onChange={e => setWorkflowForm({ ...workflowForm, event_type: e.target.value })}>
                  <option value="">Select event…</option>
                  {eventTypes.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>

            <div style={{ marginTop: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '0.9rem' }}>…and these conditions hold (optional)</strong>
                <button type="button" className="btn btn-secondary" style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem' }}
                  onClick={addCondition}>+ Condition</button>
              </div>
              {conditions.map((c, i) => (
                <div key={i} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 2fr auto', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <input type="text" placeholder="field (e.g. risk_score)" value={c.field}
                    onChange={e => updateCondition(i, { field: e.target.value })}
                    style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                  <select value={c.operator} onChange={e => updateCondition(i, { operator: e.target.value })}
                    style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                    {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
                  </select>
                  <input type="text" placeholder="value" value={c.value ?? ''}
                    onChange={e => updateCondition(i, { value: e.target.value })}
                    style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                  <button type="button" className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem' }}
                    onClick={() => removeCondition(i)}>✕</button>
                </div>
              ))}
            </div>

            <div style={{ marginTop: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '0.9rem' }}>…then run these actions</strong>
                <button type="button" className="btn btn-secondary" style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem' }}
                  onClick={addAction}>+ Action</button>
              </div>
              {actions.length === 0 && <p style={{ color: '#999', fontSize: '0.85rem' }}>No actions yet — add at least one.</p>}
              {actions.map((a, i) => (
                <div key={i} style={{ border: '1px solid #eee', borderRadius: '6px', padding: '0.75rem', marginTop: '0.5rem' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <select value={a.action_type} onChange={e => updateActionType(i, e.target.value)}
                      style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', flex: 1 }}>
                      {actionTypes.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                    <button type="button" className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem' }}
                      onClick={() => removeAction(i)}>✕</button>
                  </div>
                  <ActionConfigFields actionType={a.action_type} config={a.config}
                    onChange={config => updateActionConfig(i, config)} />
                </div>
              ))}
            </div>

            <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <button type="submit" className="btn btn-primary" disabled={busy || actions.length === 0}>
                {editingId ? 'Save Changes' : 'Create Workflow'}
              </button>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem' }}>
                <input type="checkbox" checked={workflowForm.enabled}
                  onChange={e => setWorkflowForm({ ...workflowForm, enabled: e.target.checked })} />
                Enabled
              </label>
            </div>
          </form>
        )}

        {workflows.length === 0 ? (
          <div className="empty-state">
            <h3>No workflows installed</h3>
            <p>Install a preset below, or build a custom workflow.</p>
          </div>
        ) : (
          <table className="table" style={{ marginTop: '1rem' }}>
            <thead>
              <tr><th>Workflow</th><th>Trigger Event</th><th>Actions</th><th>Enabled</th><th></th></tr>
            </thead>
            <tbody>
              {workflows.map(wf => (
                <React.Fragment key={wf.workflow_id}>
                  <tr>
                    <td>
                      <strong>{wf.name}</strong>
                      {wf.description && <div style={{ color: '#999', fontSize: '0.85rem' }}>{wf.description}</div>}
                    </td>
                    <td><code style={{ backgroundColor: '#f5f5f5', padding: '0.2rem 0.5rem', borderRadius: '3px' }}>
                      {wf.event_type || wf.trigger || '—'}
                    </code></td>
                    <td>{Array.isArray(wf.actions) ? wf.actions.length : (wf.action_count ?? '—')}</td>
                    <td>
                      <span className={`badge ${wf.enabled ? 'badge-success' : 'badge-danger'}`}>
                        {wf.enabled ? 'on' : 'off'}
                      </span>
                    </td>
                    <td style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                      <button className="btn btn-secondary" style={{ padding: '0.4rem 0.7rem', fontSize: '0.8rem' }}
                        disabled={busy} onClick={() => toggleWorkflow(wf.workflow_id)}>
                        {wf.enabled ? 'Disable' : 'Enable'}
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '0.4rem 0.7rem', fontSize: '0.8rem' }}
                        disabled={busy} onClick={() => openEditBuilder(wf)}>
                        Edit
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '0.4rem 0.7rem', fontSize: '0.8rem' }}
                        disabled={busy} onClick={() => toggleExecutions(wf)}>
                        {expandedId === wf.workflow_id ? 'Hide runs' : `Runs (${wf.execution_count ?? 0})`}
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '0.4rem 0.7rem', fontSize: '0.8rem', color: '#D62828' }}
                        disabled={busy} onClick={() => deleteWorkflow(wf.workflow_id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                  {expandedId === wf.workflow_id && (
                    <tr>
                      <td colSpan={5} style={{ backgroundColor: '#fafafa' }}>
                        {executions.length === 0 ? (
                          <p style={{ color: '#999', margin: '0.5rem 0' }}>No executions yet.</p>
                        ) : (
                          <div style={{ display: 'grid', gap: '0.4rem', padding: '0.5rem 0' }}>
                            {executions.slice().reverse().map(ex => (
                              <div key={ex.execution_id} style={{ fontSize: '0.85rem' }}>
                                <span className={`badge ${ex.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                                  {ex.status}
                                </span>
                                <span style={{ marginLeft: '0.5rem', color: '#666' }}>
                                  {new Date(ex.triggered_at).toLocaleString()} · {ex.actions_executed?.length || 0} action(s)
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h2 className="card-title">Install Preset Workflows</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          {PRESETS.map(p => (
            <button key={p.key} className="btn btn-secondary" disabled={busy}
              style={{ textAlign: 'left', padding: '1rem' }}
              onClick={() => installPreset(p.key)}>
              + {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Recent Events ({events.length})</h2>
        {events.length === 0 ? (
          <p style={{ color: '#999' }}>No events recorded yet this session.</p>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Event</th><th>Entity</th><th>Source</th><th>Priority</th></tr>
            </thead>
            <tbody>
              {events.map((ev, i) => (
                <tr key={ev.event_id || i}>
                  <td><strong>{ev.event_type}</strong></td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {ev.entity_type} {String(ev.entity_id || '').slice(0, 8)}
                  </td>
                  <td>{ev.source}</td>
                  <td><span className="badge badge-warning">{ev.priority}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
