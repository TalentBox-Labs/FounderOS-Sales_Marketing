import React, { useState } from 'react'

const SAMPLE_DEALS = [
  { id: 1, name: 'Enterprise Platform Deal', contact: 'Sarah Johnson', value: 150000, stage: 'proposal', probability: 75 },
  { id: 2, name: 'Mid-Market Implementation', contact: 'Michael Chen', value: 80000, stage: 'negotiation', probability: 60 },
  { id: 3, name: 'SMB Pilot Program', contact: 'Emma Rodriguez', value: 25000, stage: 'qualification', probability: 40 },
  { id: 4, name: 'Annual Renewal', contact: 'John Smith', value: 45000, stage: 'closed_won', probability: 100 },
]

const STAGES = ['qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']

const STAGE_COLORS = {
  qualification: '#FFB800',
  proposal: '#00B4D8',
  negotiation: '#00D4FF',
  closed_won: '#06A77D',
  closed_lost: '#D62828',
}

export default function Deals() {
  const [deals] = useState(SAMPLE_DEALS)

  const openDeals = deals.filter(d => d.stage !== 'closed_won' && d.stage !== 'closed_lost')
  const totalPipeline = openDeals.reduce((sum, d) => sum + d.value, 0)
  const closedWon = deals.filter(d => d.stage === 'closed_won').reduce((sum, d) => sum + d.value, 0)
  const winRate = deals.length
    ? Math.round((deals.filter(d => d.stage === 'closed_won').length / deals.length) * 100)
    : 0

  return (
    <div>
      <h1>Sales Pipeline</h1>

      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className="stat-label">Total Pipeline</div>
          <div className="stat-number">${(totalPipeline / 1000).toFixed(0)}K</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Closed Won</div>
          <div className="stat-number">${(closedWon / 1000).toFixed(0)}K</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Deals</div>
          <div className="stat-number">{deals.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Win Rate</div>
          <div className="stat-number">{winRate}%</div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Pipeline by Stage</h2>
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {STAGES.map(stage => {
            const stageDeals = deals.filter(d => d.stage === stage)
            const stageValue = stageDeals.reduce((sum, d) => sum + d.value, 0)
            return (
              <div key={stage}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <strong style={{ textTransform: 'capitalize' }}>{stage.replace('_', ' ')}</strong>
                  <span style={{ float: 'right', color: '#999' }}>
                    {stageDeals.length} deals • ${(stageValue / 1000).toFixed(0)}K
                  </span>
                </div>
                <div style={{ backgroundColor: '#f0f0f0', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                  <div style={{
                    backgroundColor: STAGE_COLORS[stage],
                    height: '100%',
                    width: `${Math.min((stageValue / 200000) * 100, 100)}%`,
                    transition: 'width 0.3s',
                  }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">All Deals</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Deal Name</th><th>Contact</th><th>Value</th><th>Stage</th><th>Probability</th>
            </tr>
          </thead>
          <tbody>
            {deals.map(deal => (
              <tr key={deal.id}>
                <td><strong>{deal.name}</strong></td>
                <td>{deal.contact}</td>
                <td>${deal.value.toLocaleString()}</td>
                <td>
                  <span style={{
                    backgroundColor: STAGE_COLORS[deal.stage],
                    color: 'white',
                    padding: '0.4rem 0.8rem',
                    borderRadius: '4px',
                    fontSize: '0.85rem',
                    textTransform: 'capitalize',
                  }}>
                    {deal.stage.replace('_', ' ')}
                  </span>
                </td>
                <td>{deal.probability}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
