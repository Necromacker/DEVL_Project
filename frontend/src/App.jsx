import React, { useState, useEffect } from 'react';
import { fetchBranches, fetchReviewQueue } from './api';
import Overview from './pages/Overview';
import BranchView from './pages/BranchView';
import MenuItemReview from './pages/MenuItemReview';
import ProcurementPlanner from './pages/ProcurementPlanner';
import ReviewQueue from './pages/ReviewQueue';
import DataQuality from './pages/DataQuality';
import DataUploadSettings from './pages/DataUploadSettings';
import './styles/App.css';

export default function App() {
  const [currentPage, setCurrentPage] = useState('overview');
  const [selectedBranch, setSelectedBranch] = useState('All');
  const [branches, setBranches] = useState([]);
  const [openAlertsCount, setOpenAlertsCount] = useState(3);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    loadAppMeta();
  }, []);

  const loadAppMeta = async () => {
    try {
      const bList = await fetchBranches();
      setBranches(bList);
      const queue = await fetchReviewQueue({ status: 'open' });
      setOpenAlertsCount(queue.length);
    } catch (e) {
      console.error(e);
    }
  };

  const navItems = [
    { id: 'overview', label: 'Overview', icon: '📊', colorClass: 'nav-yellow' },
    { id: 'branch-view', label: 'Branch Balance', icon: '🏪', colorClass: 'nav-purple' },
    { id: 'menu-items', label: 'Menu Item BOM', icon: '🍽️', colorClass: 'nav-lime' },
    { id: 'procurement', label: 'Procurement Planner', icon: '📦', colorClass: 'nav-yellow' },
    { id: 'review-queue', label: 'Review Queue', icon: '🚨', badge: openAlertsCount, colorClass: 'nav-purple' },
    { id: 'data-quality', label: 'Data Quality', icon: '🔍', colorClass: 'nav-lime' },
    { id: 'settings', label: 'Upload & Settings', icon: '⚙️', colorClass: 'nav-yellow' },
  ];

  const handleNav = (id) => {
    setCurrentPage(id);
    setMobileMenuOpen(false);
  };

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <aside className={`app-sidebar ${mobileMenuOpen ? 'open' : ''}`}>
        <div>
          {/* Brand section matching Neo-Brutalist look */}
          <div className="brand-section">
            <div className="brand-icon-box">🥗</div>
            <div className="brand-title-wrap">
              <h2>BRANCH PLANNER</h2>
              <div className="brand-subtitle">Waste & Procurement</div>
            </div>
          </div>

          {/* Navigation Links */}
          <ul className="nav-links">
            {navItems.map((item) => {
              const isActive = currentPage === item.id;
              return (
                <li key={item.id}>
                  <button
                    className={`nav-item-btn ${isActive ? `active ${item.colorClass}` : ''}`}
                    onClick={() => handleNav(item.id)}
                  >
                    <div className="nav-item-left">
                      <span style={{ fontSize: '1.2rem' }}>{item.icon}</span>
                      <span>{item.label}</span>
                    </div>
                    {item.badge !== undefined && item.badge > 0 && (
                      <span className="nav-badge">{item.badge}</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Sidebar Footer with Branch Switcher */}
        <div className="sidebar-footer">
          <div className="branch-select-box">
            <span className="branch-label">Active Branch Scope</span>
            <select
              className="filter-select"
              value={selectedBranch}
              onChange={(e) => setSelectedBranch(e.target.value)}
            >
              <option value="All">All 6 Branches (Group)</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--color-gray-600)', textAlign: 'center', fontWeight: 600 }}>
            v2.0 • 90-Day Live Audit
          </div>
        </div>
      </aside>

      {/* Main Viewport */}
      <div className="main-viewport">
        {/* Top Header matching reference image: "Hi, Charlotte / Your restaurant overview" */}
        <header className="top-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <button
              className="btn-icon-circle mobile-nav-toggle"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              ☰
            </button>

            <div className="header-user-greeting">
              <div className="header-avatar-circle">
                👩🏻‍🍳
              </div>
              <div className="user-text-meta">
                <div className="greeting-sub">Hi, Charlotte</div>
                <div className="greeting-title">Your restaurant overview</div>
              </div>
            </div>
          </div>

          <div className="header-actions">
            {/* Circular buttons matching reference image */}
            <button
              className="btn-icon-circle"
              title="Audit Alerts"
              onClick={() => handleNav('review-queue')}
            >
              🔔
            </button>

            {/* Neon lime circle button matching the reference image top right */}
            <button
              className="btn-icon-circle btn-icon-lime"
              title="Quick Procurement"
              onClick={() => handleNav('procurement')}
            >
              📊
            </button>
          </div>
        </header>

        {/* Page Container */}
        <main className="page-container">
          {currentPage === 'overview' && (
            <Overview
              selectedBranch={selectedBranch}
              setSelectedBranch={setSelectedBranch}
              branches={branches}
              onNavigate={handleNav}
            />
          )}
          {currentPage === 'branch-view' && (
            <BranchView
              selectedBranch={selectedBranch}
              setSelectedBranch={setSelectedBranch}
              branches={branches}
            />
          )}
          {currentPage === 'menu-items' && (
            <MenuItemReview />
          )}
          {currentPage === 'procurement' && (
            <ProcurementPlanner
              selectedBranch={selectedBranch}
              setSelectedBranch={setSelectedBranch}
              branches={branches}
            />
          )}
          {currentPage === 'review-queue' && (
            <ReviewQueue />
          )}
          {currentPage === 'data-quality' && (
            <DataQuality />
          )}
          {currentPage === 'settings' && (
            <DataUploadSettings />
          )}
        </main>
      </div>
    </div>
  );
}
