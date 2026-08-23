import React, { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import api from '../api.js'
import { LineChart, ColumnChart, DataTable } from '../components/Charts.jsx'

function currentPeriod() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

const SPEND_CHANNELS = ['manual', 'import', 'web_form', 'linkedin', 'referral', 'outreach', 'api', 'n8n']

const TREND_METRICS = [
  { id: 'pipeline_total_value', label: 'Pipeline Value', unit: '$' },
  { id: 'pipeline_weighted_forecast', label: 'Weighted Forecast', unit: '$' },
  { id: 'pipeline_deal_count', label: 'Open Deal Count', unit: '' },
]

const STAGE_ORDER = ['discovery', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost']

export default function Analytics() {
  const [metricId, setMetricId] = useState(TREND_METRICS[0].id)
  const [trendPoints, setTrendPoints] = useState([])
  const [stageData, setStageData] = useState([])
  const [scoreData, setScoreData] = useState([])
  const [showTable, setShowTable] = useState(false)
  const [offline, setOffline] = useState(false)
  const [loading, setLoading] = useState(true)

  const [attribution, setAttribution] = useState([])
  const [ltv, setLtv] = useState(null)
  const [cac, setCac] = useState([])
  const [agentProductivity, setAgentProductivity] = useState([])
  const [spendForm, setSpendForm] = useState({ channel: 'manual', period: currentPeriod(), amount: '', notes: '' })
  const [spendBusy, setSpendBusy] = useState(false)

  const loadTrend = useCallback(async (id) => {
    try {
      const res = await api.get(`/analytics/metric-data/${id}`)
      const pts = (res.data.data_points || [])
        .map(p => ({ t: new Date(p.timestamp), v: p.value }))
        .sort((a, b) => a.t - b.t)
      setTrendPoints(pts)
      setOffline(false)
    } catch (err) {
      if (err.response?.status === 404) setTrendPoints([])
      else setOffline(true)
    }
  }, [])

  const loadBreakdowns = useCallback(async () => {
    try {
      const [dealsRes, contactsRes] = await Promise.all([
        api.get('/api/v1/crm/deals', { params: { limit: 500 } }),
        api.get('/api/v1/crm/contacts', { params: { limit: 500 } }),
      ])
      const deals = dealsRes.data.deals || []
      setStageData(
        STAGE_ORDER
          .map(stage => ({
            label: stage.replace('_', ' '),
            value: deals.filter(d => d.stage === stage).reduce((s, d) => s + (d.value || 0), 0),
          }))
          .filter(d => d.value > 0 || true),
      )
      const contacts = contactsRes.data.contacts || []
      const buckets = [
        { label: '0–24', lo: 0, hi: 24 },
        { label: '25–49', lo: 25, hi: 49 },
        { label: '50–69', lo: 50, hi: 69 },
        { label: '70+', lo: 70, hi: 1000 },
      ]
      setScoreData(buckets.map(b => ({
        label: b.label,
        value: contacts.filter(c => (c.lead_score || 0) >= b.lo && (c.lead_score || 0) <= b.hi).length,
      })))
    } catch {
      setOffline(true)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadDepth = useCallback(async () => {
    try {
      const [attrRes, ltvRes, cacRes, agentsRes] = await Promise.all([
        api.get('/api/v1/analytics-depth/attribution'),
        api.get('/api/v1/analytics-depth/ltv'),
        api.get('/api/v1/analytics-depth/cac'),
        api.get('/api/v1/analytics-depth/agent-productivity'),
      ])
      setAttribution(attrRes.data.attribution || [])
      setLtv(ltvRes.data)
      setCac(cacRes.data.cac || [])
      setAgentProductivity(agentsRes.data.agents || [])
    } catch {
      // depth sections are additive — leave charts above working even if this fails
    }
  }, [])

  const logSpend = async (e) => {
    e.preventDefault()
    setSpendBusy(true)
    try {
      await api.post('/api/v1/analytics-depth/spend', {
        ...spendForm,
        amount: parseFloat(spendForm.amount || '0'),
      })
      setSpendForm({ channel: 'manual', period: currentPeriod(), amount: '', notes: '' })
      await loadDepth()
    } finally {
      setSpendBusy(false)
    }
  }

  useEffect(() => { loadTrend(metricId) }, [metricId, loadTrend])
  useEffect(() => { loadBreakdowns() }, [loadBreakdowns])
  useEffect(() => { loadDepth() }, [loadDepth])

  const activeMetric = TREND_METRICS.find(m => m.id === metricId)

  if (loading) return <div className="loading">Loading analytics…</div>

  return (
    <div>
      <h1>Analytics</h1>

      {offline && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>
          Backend offline — start the API on port 8000
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>
            {activeMetric.label} over time
          </h2>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {TREND_METRICS.map(m => (
              <button key={m.id}
                className={`btn ${metricId === m.id ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                onClick={() => setMetricId(m.id)}>
                {m.label}
              </button>
            ))}
          </div>
        </div>
        <p style={{ color: '#666', margin: '0.5rem 0 1rem' }}>
          Recorded automatically by the heartbeat's hourly pipeline snapshot.
        </p>
        {showTable ? (
          <DataTable
            columns={['Time', activeMetric.label]}
            rows={trendPoints.map(p => [p.t.toLocaleString(), `${activeMetric.unit}${p.v.toLocaleString()}`])}
          />
        ) : (
          <LineChart points={trendPoints} unit={activeMetric.unit === '$' ? '' : activeMetric.unit}
            ariaLabel={`${activeMetric.label} trend`} />
        )}
        <button className="btn btn-secondary" style={{ marginTop: '0.75rem', padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
          onClick={() => setShowTable(!showTable)}>
          {showTable ? 'Chart view' : 'Table view'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title">Pipeline value by stage</h2>
          <ColumnChart data={stageData} ariaLabel="pipeline value by stage" />
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title">Contacts by lead score</h2>
          <ColumnChart data={scoreData} ariaLabel="contacts by lead score band" />
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Attribution — revenue by source</h2>
        <p style={{ color: '#666', margin: '0.25rem 0 1rem' }}>
          Where closed-won revenue actually came from, by how the contact entered the CRM.
        </p>
        {attribution.length === 0 ? (
          <p style={{ color: '#999' }}>No contacts yet.</p>
        ) : (
          <>
            <ColumnChart
              data={attribution.map(a => ({ label: a.source, value: a.won_value }))}
              ariaLabel="closed-won revenue by source"
            />
            <div style={{ marginTop: '1rem' }}>
              <DataTable
                columns={['Source', 'Contacts', 'Qualify Rate', 'Won Deals', 'Won Value']}
                rows={attribution.map(a => [
                  a.source, a.contacts, `${Math.round(a.qualify_rate * 100)}%`,
                  a.won_deals, `$${a.won_value.toLocaleString()}`,
                ])}
              />
            </div>
          </>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title">Customer Lifetime Value</h2>
          {!ltv || ltv.avg_ltv === null ? (
            <p style={{ color: '#999' }}>No closed-won deals linked to a contact yet.</p>
          ) : (
            <>
              <div className="grid" style={{ marginBottom: '1rem' }}>
                <div className="stat-card">
                  <div className="stat-label">Avg LTV</div>
                  <div className="stat-number">${ltv.avg_ltv.toLocaleString()}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Customers w/ Revenue</div>
                  <div className="stat-number">{ltv.customers_with_revenue}</div>
                </div>
              </div>
              <div style={{ display: 'grid', gap: '0.4rem' }}>
                {ltv.top_customers.map(c => (
                  <Link key={c.contact_id} to={`/contacts/${c.contact_id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', padding: '0.3rem 0' }}>
                      <span>{c.name} <span style={{ color: '#999' }}>({c.deals} deal{c.deals === 1 ? '' : 's'})</span></span>
                      <strong>${c.total_value.toLocaleString()}</strong>
                    </div>
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <h2 className="card-title">Customer Acquisition Cost</h2>
          <p style={{ color: '#666', fontSize: '0.85rem', margin: '0 0 0.75rem' }}>
            CAC only shows for channels with logged spend — nothing here is estimated.
          </p>
          <form onSubmit={logSpend} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
            <select value={spendForm.channel} onChange={e => setSpendForm({ ...spendForm, channel: e.target.value })}
              style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}>
              {SPEND_CHANNELS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <input type="month" value={spendForm.period}
              onChange={e => setSpendForm({ ...spendForm, period: e.target.value })}
              style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
            <input type="number" min="0" step="any" placeholder="Spend ($)" value={spendForm.amount}
              onChange={e => setSpendForm({ ...spendForm, amount: e.target.value })}
              style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
            <button type="submit" className="btn btn-primary" disabled={spendBusy || !spendForm.amount}>
              Log Spend
            </button>
          </form>
          {cac.length === 0 ? (
            <p style={{ color: '#999' }}>No spend logged yet.</p>
          ) : (
            <DataTable
              columns={['Channel', 'Spend', 'Customers', 'CAC']}
              rows={cac.map(c => [
                c.channel, `$${c.spend.toLocaleString()}`, c.customers_acquired,
                c.cac === null ? '—' : `$${c.cac.toLocaleString()}`,
              ])}
            />
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Agent Productivity</h2>
        <p style={{ color: '#666', margin: '0.25rem 0 1rem' }}>
          Actions, goals, and approvals per registered agent — see the <Link to="/agents">Agents page</Link> for detail.
        </p>
        {agentProductivity.length === 0 ? (
          <p style={{ color: '#999' }}>No agents registered.</p>
        ) : (
          <DataTable
            columns={['Agent', 'Type', 'Actions', 'Goals', 'Approvals']}
            rows={agentProductivity.map(a => [
              <Link key={a.name} to="/agents" style={{ color: '#667eea' }}>{a.name}</Link>,
              a.type,
              `${a.actions_completed}/${a.actions_total}${a.actions_failed ? ` (${a.actions_failed} failed)` : ''}`,
              `${a.goals_achieved}/${a.goals_owned}`,
              `${a.approvals_approved}/${a.approvals_requested}`,
            ])}
          />
        )}
      </div>
    </div>
  )
}
