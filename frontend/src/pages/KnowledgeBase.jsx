import React, { useState, useEffect, useCallback } from 'react'
import api from '../api.js'

const EMPTY_ARTICLE = { title: '', content: '', tags: '' }

const TYPE_COLORS = {
  kb_article: '#667eea', contact: '#06A77D', deal: '#00B4D8',
  activity: '#FFB800', project: '#9B5DE5',
}

export default function KnowledgeBase() {
  const [kbId, setKbId] = useState(null)
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)
  const [busy, setBusy] = useState(false)

  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(EMPTY_ARTICLE)

  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [asking, setAsking] = useState(false)

  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [searching, setSearching] = useState(false)

  const load = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/knowledge-base/bases')
      const bases = res.data.knowledge_bases || []
      const kb = bases.find(b => b.name === 'Playbooks & Notes') || bases[0]
      if (kb) {
        setKbId(kb.id)
        const detail = await api.get(`/api/v1/knowledge-base/bases/${kb.id}`)
        setArticles(detail.data.knowledge_base.articles || [])
      } else {
        setArticles([])
      }
      setOffline(false)
    } catch {
      setOffline(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const resetForm = () => {
    setEditingId(null)
    setForm(EMPTY_ARTICLE)
    setShowForm(false)
  }

  const openEdit = (article) => {
    setEditingId(article.id)
    setForm({ title: article.title, content: article.content || '', tags: article.tags || '' })
    setShowForm(true)
  }

  const saveArticle = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      if (editingId) {
        await api.put(`/api/v1/knowledge-base/articles/${editingId}`, form)
      } else {
        await api.post(`/api/v1/knowledge-base/bases/${kbId || 'default'}/articles`, form)
      }
      resetForm()
      await load()
    } finally {
      setBusy(false)
    }
  }

  const deleteArticle = async (id) => {
    setBusy(true)
    try {
      await api.delete(`/api/v1/knowledge-base/articles/${id}`)
      await load()
    } finally {
      setBusy(false)
    }
  }

  const ask = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    setAsking(true)
    setAnswer(null)
    try {
      const res = await api.post('/api/v1/knowledge-base/ask', { question })
      setAnswer(res.data)
    } catch {
      setAnswer({ answer: 'Could not reach the backend.', sources: [] })
    } finally {
      setAsking(false)
    }
  }

  const runSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setSearching(true)
    setResults(null)
    try {
      const res = await api.get('/api/v1/knowledge-base/search', { params: { q: query } })
      setResults(res.data.results || [])
    } catch {
      setResults([])
    } finally {
      setSearching(false)
    }
  }

  if (loading) return <div className="loading">Loading knowledge base…</div>

  return (
    <div>
      <h1>Knowledge Base</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Playbooks and notes, searchable by meaning (not just keywords) across
        the knowledge base and your CRM. Ask a question and get an answer
        grounded in what's actually here.
      </p>

      {offline && (
        <div className="card" style={{ borderLeft: '4px solid #D62828' }}>
          Backend offline — start the API on port 8000
        </div>
      )}

      <div className="card">
        <h2 className="card-title">Ask</h2>
        <form onSubmit={ask} style={{ display: 'flex', gap: '0.6rem' }}>
          <input type="text" value={question} onChange={e => setQuestion(e.target.value)}
            placeholder='e.g. "How should I handle a deal stuck in negotiation?"'
            style={{ flex: 1, padding: '0.7rem', border: '1px solid #ddd', borderRadius: '4px' }} />
          <button type="submit" className="btn btn-primary" disabled={asking || !question.trim()}>
            {asking ? 'Thinking…' : 'Ask'}
          </button>
        </form>
        {answer && (
          <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f8f9ff', borderRadius: '8px' }}>
            <p style={{ whiteSpace: 'pre-line', margin: 0 }}>{answer.answer}</p>
            {answer.sources?.length > 0 && (
              <div style={{ marginTop: '0.75rem', display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {answer.sources.map((s, i) => (
                  <span key={i} style={{
                    fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '10px',
                    backgroundColor: TYPE_COLORS[s.type] || '#999', color: 'white',
                  }}>
                    {s.title}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="card-title">Search</h2>
        <form onSubmit={runSearch} style={{ display: 'flex', gap: '0.6rem' }}>
          <input type="text" value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search notes, contacts, deals, activities…"
            style={{ flex: 1, padding: '0.7rem', border: '1px solid #ddd', borderRadius: '4px' }} />
          <button type="submit" className="btn btn-secondary" disabled={searching || !query.trim()}>
            {searching ? 'Searching…' : 'Search'}
          </button>
        </form>
        {results && (
          results.length === 0 ? (
            <p style={{ color: '#999', marginTop: '1rem' }}>No matches.</p>
          ) : (
            <div style={{ display: 'grid', gap: '0.5rem', marginTop: '1rem' }}>
              {results.map(r => (
                <div key={r.id} style={{ border: '1px solid #eee', borderRadius: '6px', padding: '0.6rem 0.9rem' }}>
                  <span style={{
                    fontSize: '0.7rem', padding: '0.15rem 0.5rem', borderRadius: '10px',
                    backgroundColor: TYPE_COLORS[r.metadata?.type] || '#999', color: 'white', marginRight: '0.5rem',
                  }}>
                    {r.metadata?.type}
                  </span>
                  <strong>{r.metadata?.title || r.metadata?.name || r.metadata?.subject || r.id}</strong>
                  <div style={{ color: '#666', fontSize: '0.85rem', marginTop: '0.2rem' }}>{r.snippet}</div>
                </div>
              ))}
            </div>
          )
        )}
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="card-title" style={{ marginBottom: 0 }}>Articles ({articles.length})</h2>
          <button className="btn btn-primary" onClick={() => showForm ? resetForm() : setShowForm(true)}>
            {showForm ? 'Cancel' : '+ New Article'}
          </button>
        </div>

        {showForm && (
          <form onSubmit={saveArticle} style={{ marginTop: '1rem', display: 'grid', gap: '0.75rem' }}>
            <div className="form-group">
              <label>Title</label>
              <input type="text" required value={form.title}
                onChange={e => setForm({ ...form, title: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Content</label>
              <textarea rows={5} value={form.content}
                onChange={e => setForm({ ...form, content: e.target.value })}
                style={{ width: '100%', padding: '0.6rem', border: '1px solid #ddd', borderRadius: '4px', fontFamily: 'inherit' }} />
            </div>
            <div className="form-group">
              <label>Tags (comma-separated)</label>
              <input type="text" placeholder="sales, onboarding" value={form.tags}
                onChange={e => setForm({ ...form, tags: e.target.value })} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy || !form.title.trim()} style={{ justifySelf: 'start' }}>
              {editingId ? 'Save Changes' : 'Create Article'}
            </button>
          </form>
        )}

        {articles.length === 0 ? (
          <div className="empty-state">
            <h3>No articles yet</h3>
            <p>Write your first playbook or note — it becomes searchable immediately.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '1rem' }}>
            {articles.map(a => (
              <div key={a.id} style={{ border: '1px solid #eee', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <strong>{a.title}</strong>
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <button className="btn btn-secondary" style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem' }}
                      onClick={() => openEdit(a)}>Edit</button>
                    <button className="btn btn-secondary" style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem', color: '#D62828' }}
                      onClick={() => deleteArticle(a.id)}>Delete</button>
                  </div>
                </div>
                {a.content && <p style={{ color: '#666', fontSize: '0.9rem', margin: '0.5rem 0' }}>{a.content}</p>}
                {a.tags && <div style={{ color: '#999', fontSize: '0.8rem' }}>tags: {a.tags}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
