import React, { useState } from 'react'

const SAMPLE_CONTACTS = [
  { id: 1, name: 'Sarah Johnson', email: 'sarah.johnson@acme.com', phone: '+1-555-0101', company: 'Acme Corp', title: 'VP Sales', status: 'qualified' },
  { id: 2, name: 'Michael Chen', email: 'm.chen@techflow.io', phone: '+1-555-0102', company: 'TechFlow', title: 'CRO', status: 'prospect' },
  { id: 3, name: 'Emma Rodriguez', email: 'emma.r@innovate.com', phone: '+1-555-0103', company: 'Innovate Ltd', title: 'Revenue Ops Director', status: 'qualified' },
]

const EMPTY_FORM = { name: '', email: '', phone: '', company: '', title: '', status: 'prospect' }

export default function Contacts() {
  const [contacts, setContacts] = useState(SAMPLE_CONTACTS)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState(EMPTY_FORM)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const nextId = contacts.length ? Math.max(...contacts.map(c => c.id)) + 1 : 1
    setContacts([...contacts, { id: nextId, ...formData }])
    setFormData(EMPTY_FORM)
    setShowForm(false)
  }

  const badgeClass = (status) =>
    status === 'qualified' ? 'badge-success' :
    status === 'prospect' ? 'badge-warning' : 'badge-danger'

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: 0 }}>Contacts</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Contact'}
        </button>
      </div>

      {showForm && (
        <div className="card">
          <h2 className="card-title">New Contact</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Name</label>
                <input type="text" name="name" value={formData.name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input type="tel" name="phone" value={formData.phone} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>Company</label>
                <input type="text" name="company" value={formData.company} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>Title</label>
                <input type="text" name="title" value={formData.title} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select name="status" value={formData.status} onChange={handleChange}>
                  <option value="prospect">Prospect</option>
                  <option value="qualified">Qualified</option>
                  <option value="customer">Customer</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn btn-primary">Save Contact</button>
          </form>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">All Contacts ({contacts.length})</h2>
        {contacts.length === 0 ? (
          <div className="empty-state">
            <h3>No contacts yet</h3>
            <p>Click "Add Contact" to create your first contact.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th><th>Email</th><th>Company</th><th>Title</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map(c => (
                <tr key={c.id}>
                  <td><strong>{c.name}</strong></td>
                  <td>{c.email}</td>
                  <td>{c.company}</td>
                  <td>{c.title}</td>
                  <td><span className={`badge ${badgeClass(c.status)}`}>{c.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
