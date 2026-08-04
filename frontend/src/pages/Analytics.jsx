import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'
import { LineChart, ColumnChart, DataTable } from '../components/Charts.jsx'

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

  useEffect(() => { loadTrend(metricId) }, [metricId, loadTrend])
  useEffect(() => { loadBreakdowns() }, [loadBreakdowns])

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
    </div>
  )
}
