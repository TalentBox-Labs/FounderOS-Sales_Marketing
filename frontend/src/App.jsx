import React from 'react'
import { HashRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import Contacts from './pages/Contacts.jsx'
import Deals from './pages/Deals.jsx'
import Analytics from './pages/Analytics.jsx'
import Goals from './pages/Goals.jsx'
import Activity from './pages/Activity.jsx'
import Approvals from './pages/Approvals.jsx'
import Login from './pages/Login.jsx'
import { isAuthed, logout } from './api.js'

function RequireAuth({ children }) {
  if (!isAuthed()) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <NavLink to="/" className="nav-logo">
              WorkCrew CRM
            </NavLink>
            {isAuthed() && (
              <ul className="nav-menu">
                <li><NavLink to="/" className="nav-link" end>Dashboard</NavLink></li>
                <li><NavLink to="/contacts" className="nav-link">Contacts</NavLink></li>
                <li><NavLink to="/deals" className="nav-link">Deals</NavLink></li>
                <li><NavLink to="/analytics" className="nav-link">Analytics</NavLink></li>
                <li><NavLink to="/goals" className="nav-link">Goals</NavLink></li>
                <li><NavLink to="/approvals" className="nav-link">Approvals</NavLink></li>
                <li><NavLink to="/activity" className="nav-link">Activity</NavLink></li>
                <li>
                  <button
                    onClick={logout}
                    className="nav-link"
                    style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit' }}
                  >
                    Logout
                  </button>
                </li>
              </ul>
            )}
          </div>
        </nav>

        <div className="main-content">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
            <Route path="/contacts" element={<RequireAuth><Contacts /></RequireAuth>} />
            <Route path="/deals" element={<RequireAuth><Deals /></RequireAuth>} />
            <Route path="/analytics" element={<RequireAuth><Analytics /></RequireAuth>} />
            <Route path="/goals" element={<RequireAuth><Goals /></RequireAuth>} />
            <Route path="/approvals" element={<RequireAuth><Approvals /></RequireAuth>} />
            <Route path="/activity" element={<RequireAuth><Activity /></RequireAuth>} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}
