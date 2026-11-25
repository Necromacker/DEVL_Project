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
  };

  return (
    <div className="app-layout-horizontal">
      {/* Main Top Navbar */}
      <header className="main-navbar">
        {/* Left: Logo & Brand */}
        <div className="navbar-left">
          <div className="brand-box" onClick={() => handleNav('overview')} style={{ cursor: 'pointer' }}>
            <div className="brand-icon-box">
              <IconLogo size={22} color="#121212" />
            </div>
            <div className="brand-title-wrap">
              <h2>BRANCH PLANNER</h2>
              <div className="brand-subtitle">Waste & Procurement • Pune</div>
            </div>
          </div>
        </div>

        {/* Middle: 4 Essential Navigation Options */}
        <nav className="navbar-middle">
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

        {/* Rightmost: Notifications & Quick Action Button */}
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
