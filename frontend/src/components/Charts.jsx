import React, { useMemo, useRef, useState } from 'react'

// Chart tokens (validated reference palette, light mode)
const SERIES = '#2a78d6'      // categorical slot 1 — single-series charts use only this
const GRID = '#e8e8e6'        // hairline gridlines, one step off surface
const TEXT_SECONDARY = '#52514e'
const SURFACE = '#ffffff'

function niceTicks(min, max, count = 4) {
  if (max <= min) max = min + 1
  const span = max - min
  const rawStep = span / count
  const mag = Math.pow(10, Math.floor(Math.log10(rawStep)))
  const step = [1, 2, 5, 10].map(m => m * mag).find(s => s >= rawStep) || 10 * mag
  const lo = Math.floor(min / step) * step
  const ticks = []
  for (let v = lo; v <= max + step * 0.5; v += step) ticks.push(v)
  return ticks
}

function fmtCompact(v) {
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  if (Math.abs(v) >= 1_000) return `${Math.round(v / 1_000)}K`
  return `${Math.round(v * 100) / 100}`
}

/**
 * Single-series line chart with area wash, crosshair hover, endpoint label.
 * points: [{ t: Date, v: number }] (sorted ascending by t)
 */
export function LineChart({ points, height = 240, unit = '', ariaLabel = 'line chart' }) {
  const [hover, setHover] = useState(null) // index
  const wrapRef = useRef(null)
  const width = 640
  const pad = { top: 16, right: 56, bottom: 28, left: 48 }

  const model = useMemo(() => {
    if (!points || points.length === 0) return null
    const vs = points.map(p => p.v)
    const vMin = Math.min(0, ...vs)
    const vMax = Math.max(...vs)
    const ticks = niceTicks(vMin, vMax)
    const yMin = ticks[0]
    const yMax = ticks[ticks.length - 1]
    const x = i => pad.left + (points.length === 1
      ? (width - pad.left - pad.right) / 2
      : (i / (points.length - 1)) * (width - pad.left - pad.right))
    const y = v => pad.top + (1 - (v - yMin) / (yMax - yMin || 1)) * (height - pad.top - pad.bottom)
    const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(p.v).toFixed(1)}`).join(' ')
    const area = `${path} L${x(points.length - 1).toFixed(1)},${y(yMin).toFixed(1)} L${x(0).toFixed(1)},${y(yMin).toFixed(1)} Z`
    return { ticks, yMin, yMax, x, y, path, area }
  }, [points, height])

  if (!model) {
    return <div style={{ color: '#999', padding: '2rem', textAlign: 'center' }}>
      No data yet — the heartbeat records a snapshot every hour.
    </div>
  }

  const onMove = (e) => {
    const rect = wrapRef.current.getBoundingClientRect()
    const px = ((e.clientX - rect.left) / rect.width) * width
    let best = 0, bestDist = Infinity
    points.forEach((_, i) => {
      const d = Math.abs(model.x(i) - px)
      if (d < bestDist) { bestDist = d; best = i }
    })
    setHover(best)
  }

  const last = points.length - 1
  const h = hover

  return (
    <div ref={wrapRef} style={{ position: 'relative' }}
      onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={ariaLabel}
        style={{ width: '100%', height: 'auto', display: 'block' }}>
        {model.ticks.map(t => (
          <g key={t}>
            <line x1={pad.left} x2={width - pad.right} y1={model.y(t)} y2={model.y(t)}
              stroke={GRID} strokeWidth="1" />
            <text x={pad.left - 8} y={model.y(t) + 4} textAnchor="end"
              fontSize="11" fill={TEXT_SECONDARY}>{fmtCompact(t)}</text>
          </g>
        ))}

        <path d={model.area} fill={SERIES} opacity="0.1" />
        <path d={model.path} fill="none" stroke={SERIES} strokeWidth="2"
          strokeLinejoin="round" strokeLinecap="round" />

        {/* endpoint marker: >=8px dot with 2px surface ring, value label at the end */}
        <circle cx={model.x(last)} cy={model.y(points[last].v)} r="6"
          fill={SERIES} stroke={SURFACE} strokeWidth="2" />
        <text x={model.x(last) + 10} y={model.y(points[last].v) + 4}
          fontSize="12" fontWeight="600" fill="#0b0b0b">
          {fmtCompact(points[last].v)}{unit}
        </text>

        {/* x labels: first and last timestamp */}
        <text x={model.x(0)} y={height - 8} fontSize="11" fill={TEXT_SECONDARY}>
          {points[0].t.toLocaleDateString()}
        </text>
        <text x={model.x(last)} y={height - 8} textAnchor="end" fontSize="11" fill={TEXT_SECONDARY}>
          {points[last].t.toLocaleDateString()}
        </text>

        {h !== null && (
          <g>
            <line x1={model.x(h)} x2={model.x(h)} y1={pad.top} y2={height - pad.bottom}
              stroke={TEXT_SECONDARY} strokeWidth="1" opacity="0.4" />
            <circle cx={model.x(h)} cy={model.y(points[h].v)} r="5"
              fill={SERIES} stroke={SURFACE} strokeWidth="2" />
          </g>
        )}
      </svg>

      {h !== null && (
        <div style={{
          position: 'absolute',
          left: `${(model.x(h) / width) * 100}%`,
          top: 0,
          transform: `translateX(${h > points.length / 2 ? '-105%' : '8px'})`,
          background: '#0b0b0b', color: 'white', padding: '0.4rem 0.6rem',
          borderRadius: '6px', fontSize: '0.8rem', pointerEvents: 'none',
          whiteSpace: 'nowrap',
        }}>
          <div style={{ opacity: 0.7 }}>{points[h].t.toLocaleString()}</div>
          <div style={{ fontWeight: 600 }}>{fmtCompact(points[h].v)}{unit}</div>
        </div>
      )}
    </div>
  )
}

/**
 * Single-hue column chart: <=24px columns, 4px rounded cap, square baseline,
 * value on every cap (few categories), hover tooltip.
 * data: [{ label, value }]
 */
export function ColumnChart({ data, height = 220, unit = '', ariaLabel = 'column chart' }) {
  const [hover, setHover] = useState(null)
  const width = 640
  const pad = { top: 24, right: 12, bottom: 40, left: 48 }

  if (!data || data.length === 0) {
    return <div style={{ color: '#999', padding: '2rem', textAlign: 'center' }}>No data yet.</div>
  }

  const vMax = Math.max(...data.map(d => d.value), 1)
  const ticks = niceTicks(0, vMax)
  const yMax = ticks[ticks.length - 1]
  const band = (width - pad.left - pad.right) / data.length
  const barW = Math.min(24, band * 0.55)
  const y = v => pad.top + (1 - v / yMax) * (height - pad.top - pad.bottom)
  const baseline = y(0)

  return (
    <div style={{ position: 'relative' }}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={ariaLabel}
        style={{ width: '100%', height: 'auto', display: 'block' }}>
        {ticks.map(t => (
          <g key={t}>
            <line x1={pad.left} x2={width - pad.right} y1={y(t)} y2={y(t)}
              stroke={GRID} strokeWidth="1" />
            <text x={pad.left - 8} y={y(t) + 4} textAnchor="end"
              fontSize="11" fill={TEXT_SECONDARY}>{fmtCompact(t)}</text>
          </g>
        ))}

        {data.map((d, i) => {
          const cx = pad.left + band * i + band / 2
          const x0 = cx - barW / 2
          const top = y(d.value)
          const hgt = Math.max(baseline - top, 0)
          const r = Math.min(4, hgt, barW / 2)
          // rounded top corners (data end), square baseline
          const path = hgt <= 0 ? '' : [
            `M${x0},${baseline}`,
            `L${x0},${top + r}`,
            `Q${x0},${top} ${x0 + r},${top}`,
            `L${x0 + barW - r},${top}`,
            `Q${x0 + barW},${top} ${x0 + barW},${top + r}`,
            `L${x0 + barW},${baseline}`,
            'Z',
          ].join(' ')
          return (
            <g key={d.label}
              onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              {/* oversized hit target */}
              <rect x={pad.left + band * i} y={pad.top} width={band}
                height={height - pad.top - pad.bottom} fill="transparent" />
              {path && <path d={path} fill={SERIES} opacity={hover === null || hover === i ? 1 : 0.45} />}
              <text x={cx} y={top - 6} textAnchor="middle" fontSize="11"
                fontWeight="600" fill="#0b0b0b">{fmtCompact(d.value)}{unit}</text>
              <text x={cx} y={height - 12} textAnchor="middle" fontSize="11"
                fill={TEXT_SECONDARY}>{d.label}</text>
            </g>
          )
        })}
        <line x1={pad.left} x2={width - pad.right} y1={baseline} y2={baseline}
          stroke={TEXT_SECONDARY} strokeWidth="1" opacity="0.5" />
      </svg>
    </div>
  )
}

/** Accessible fallback: the same data as a plain table. */
export function DataTable({ columns, rows }) {
  return (
    <table className="table">
      <thead><tr>{columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>{r.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
        ))}
      </tbody>
    </table>
  )
}
