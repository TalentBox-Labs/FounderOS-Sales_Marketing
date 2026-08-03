import React from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import Contacts from './pages/Contacts.jsx'
import Deals from './pages/Deals.jsx'
import Analytics from './pages/Analytics.jsx'
import Goals from './pages/Goals.jsx'
import Activity from './pages/Activity.jsx'

export default function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <NavLink to="/" className="nav-logo">
              WorkCrew CRM
            </NavLink>
            <ul className="nav-menu">
              <li><NavLink to="/" className="nav-link" end>Dashboard</NavLink></li>
              <li><NavLink to="/contacts" className="nav-link">Contacts</NavLink></li>
              <li><NavLink to="/deals" className="nav-link">Deals</NavLink></li>
              <li><NavLink to="/analytics" className="nav-link">Analytics</NavLink></li>
              <li><NavLink to="/goals" className="nav-link">Goals</NavLink></li>
              <li><NavLink to="/activity" className="nav-link">Activity</NavLink></li>
            </ul>
          </div>
        </nav>

        <div className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/contacts" element={<Contacts />} />
            <Route path="/deals" element={<Deals />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/goals" element={<Goals />} />
            <Route path="/activity" element={<Activity />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}
