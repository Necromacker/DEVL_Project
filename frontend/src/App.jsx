import React, { useState, useEffect } from 'react';
import { fetchBranches, fetchReviewQueue } from './api';
import Overview from './pages/Overview';
import BranchView from './pages/BranchView';
import ProcurementPlanner from './pages/ProcurementPlanner';
import ReviewQueue from './pages/ReviewQueue';
import { IconDashboard, IconBranch, IconProcurement, IconAlert, IconBell, IconChart, IconLogo } from './components/Icons';
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

  // 4 Core Options in Middle of Navbar
  const navItems = [
    { id: 'overview', label: 'Overview', icon: <IconDashboard size={18} />, colorClass: 'nav-yellow' },
    { id: 'branch-view', label: 'Branch Balance', icon: <IconBranch size={18} />, colorClass: 'nav-purple' },
    { id: 'procurement', label: 'Procurement', icon: <IconProcurement size={18} />, colorClass: 'nav-yellow' },
    { id: 'review-queue', label: 'Audit Alerts', icon: <IconAlert size={18} />, badge: openAlertsCount, colorClass: 'nav-purple' },
  ];

  const handleNav = (id) => {
    setCurrentPage(id);
    setMobileMenuOpen(false);
  };

  return (
    <div className="app-layout-horizontal">
      {/* Main Top Navbar */}
      <header className="main-navbar">
        {/* Left: Logo & Brand */}
        <div className="navbar-left">
          <button
            className="btn-icon-circle mobile-nav-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#121212" strokeWidth="2.5">
              <line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          
          <div className="brand-box" onClick={() => handleNav('overview')} style={{ cursor: 'pointer' }}>
            <div className="brand-icon-box">
              <IconLogo size={22} color="#121212" />
            </div>
            <div className="brand-title-wrap">
              <h2>BRANCH PLANNER</h2>
              <div className="brand-subtitle">Waste & Procurement</div>
            </div>
          </div>
        </div>

        {/* Middle: 4 Essential Navigation Options */}
        <nav className={`navbar-middle ${mobileMenuOpen ? 'mobile-open' : ''}`}>
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                className={`nav-tab-btn ${isActive ? `active ${item.colorClass}` : ''}`}
                onClick={() => handleNav(item.id)}
              >
                <span className="nav-icon-wrap">{item.icon}</span>
                <span>{item.label}</span>
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="nav-badge">{item.badge}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Rightmost: Notifications, Quick Button, Profile */}
        <div className="navbar-right">
          <button
            className="btn-icon-circle"
            title="Audit Alerts"
            onClick={() => handleNav('review-queue')}
          >
            <IconBell size={18} color="#121212" />
          </button>

          <button
            className="btn-icon-circle btn-icon-lime"
            title="Procurement Forecast"
            onClick={() => handleNav('procurement')}
          >
            <IconChart size={18} color="#121212" />
          </button>

          <div className="header-avatar-circle" title="Hi, Charlotte">
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80"
              alt="Charlotte"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
        </div>
      </header>

      {/* Main Page Body */}
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
      </main>
    </div>
  );
}
