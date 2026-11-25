import React, { useState, useEffect } from 'react';
import SegmentedPillChart from '../components/SegmentedPillChart';
import { fetchOverview } from '../api';
import '../styles/Overview.css';

export default function Overview({ selectedBranch, setSelectedBranch, branches = [], onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activePeriod, setActivePeriod] = useState('WEEK');

  useEffect(() => {
    loadData();
  }, [selectedBranch]);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchOverview({ branch_id: selectedBranch });
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportRankingCsv = () => {
    if (!data?.branch_rankings) return;
    const headers = ["Branch ID", "Branch Name", "Sales ($)", "Purchases ($)", "Waste ($)", "Waste %", "Variance ($)", "Variance %", "Food Cost %", "Flags"];
    const rows = data.branch_rankings.map(b => [
      b.branch_id,
      `"${b.branch_name}"`,
      b.sales,
      b.purchases,
      b.waste_cost,
      b.waste_pct,
      b.variance_cost,
      b.variance_pct,
      b.food_cost_pct,
      b.items_flagged
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `branch_rankings_${selectedBranch}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading && !data) {
    return <div className="overview-page"><p style={{ fontWeight: 800 }}>Loading overview metrics...</p></div>;
  }

  const kpis = data?.kpis || {
    total_purchases: 4567,
    total_waste: 40234,
    unexplained_variance: 2845,
    total_sales: 44346,
    waste_pct: 3.2,
    variance_pct: 4.8,
    food_cost_pct: 28.5,
    active_branches: 6
  };

  return (
    <div className="overview-page">
      {/* Page Headline matching reference: "ACTIVE RESTAURANT (6)" */}
      <div className="page-headline-wrap">
        <div>
          <h1 className="page-headline">
            ACTIVE RESTAURANT <span className="headline-badge">({kpis.active_branches || 6})</span>
          </h1>
          <p style={{ fontWeight: 600, color: 'var(--color-gray-600)', marginTop: 4 }}>
            Multi-branch waste tracking, food cost variance & automated replenishment
          </p>
        </div>

        {/* Global Filter Bar */}
        <div className="overview-filter-bar">
          <div className="filter-group">
            <span>Branch:</span>
            <select
              className="filter-select"
              value={selectedBranch}
              onChange={(e) => setSelectedBranch(e.target.value)}
            >
              <option value="All">All 6 Branches</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
          <button className="btn-neo btn-neo-yellow" onClick={exportRankingCsv}>
            📥 Export CSV
          </button>
        </div>
      </div>

      {/* Top 3 Metric Cards matching Reference Image */}
      <div className="kpi-cards-grid">
        {/* Card 1: Pastel Yellow Card (Purchases / Revenue) */}
        <div className="kpi-card-yellow">
          <div className="card-header-row">
            <div className="card-icon-circle">📊</div>
            <div className="card-menu-dot">•••</div>
          </div>
          <div className="card-metric-section">
            <div className="card-metric-label">Total Purchases</div>
            <div className="card-metric-value">${kpis.total_purchases?.toLocaleString()}</div>
            <div className="card-metric-sub">
              <span className="pill-badge pill-badge-white">Food Cost {kpis.food_cost_pct}%</span>
            </div>
          </div>
        </div>

        {/* Card 2: Pastel Lavender Card (Waste / Expenses) */}
        <div className="kpi-card-purple">
          <div className="card-header-row">
            <div className="card-icon-circle">👛</div>
            <div className="card-menu-dot">•••</div>
          </div>
          <div className="card-metric-section">
            <div className="card-metric-label">Logged Waste Cost</div>
            <div className="card-metric-value">${kpis.total_waste?.toLocaleString()}</div>
            <div className="card-metric-sub">
              <span className="pill-badge pill-badge-white">Waste {kpis.waste_pct}% of Purchases</span>
            </div>
          </div>
        </div>

        {/* Card 3: Crisp White Card (Sales & Sparkline) */}
        <div className="kpi-card-white">
          <div className="card-header-row">
            <div>
              <div className="card-metric-label" style={{ color: 'var(--color-gray-600)' }}>Sales Revenue</div>
              <div className="card-metric-value">${kpis.total_sales?.toLocaleString()}</div>
            </div>
            <span className="pill-badge pill-badge-lime">Active 90D</span>
          </div>

          {/* Neo sparkline wavy line matching reference */}
          <div style={{ marginTop: 8 }}>
            <svg className="sparkline-svg" viewBox="0 0 300 50">
              <path d="M 0 38 Q 20 10, 40 32 T 80 15 T 120 40 T 160 12 T 200 35 T 240 8 T 280 28 L 300 20" />
            </svg>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-gray-600)' }}>Unexplained Variance:</span>
            <span className={`pill-badge ${kpis.variance_pct > 10 ? 'pill-badge-red' : 'pill-badge-yellow'}`}>
              ${kpis.unexplained_variance?.toLocaleString()} ({kpis.variance_pct}%)
            </span>
          </div>
        </div>
      </div>

      {/* Analytics 2-Column: Segmented Bar Chart + Recent Order Items */}
      <div className="overview-analytics-grid">
        {/* Left: Segmented Stacked Pill Bar Chart */}
        <div className="chart-panel-card">
          <div className="chart-header-row">
            <div className="chart-title-group">
              <h3>Sales & Consumption Rhythm</h3>
              <p>Day of week demand pattern with peak weekend volume</p>
            </div>
            <span className="pill-badge pill-badge-yellow">Live Rhythm</span>
          </div>

          <SegmentedPillChart
            data={data?.trend_bars || []}
            activePeriod={activePeriod}
            onPeriodChange={setActivePeriod}
          />
        </div>

        {/* Right: Top Food Items list matching reference image */}
        <div className="recent-orders-card">
          <div className="recent-orders-header">
            <h3>Recent High-Volume Items</h3>
            <span className="view-all-link" onClick={() => onNavigate('menu-items')}>View All</span>
          </div>

          <div className="orders-items-list">
            {(data?.top_items || []).map((item, idx) => (
              <div key={idx} className="order-pill-row">
                <div className="order-item-left">
                  <div className="order-avatar-icon" style={{ backgroundColor: item.color }}>
                    {item.icon}
                  </div>
                  <div>
                    <div className="order-item-name">{item.name}</div>
                    <div className="order-item-sub">{item.category} • {item.orders} orders</div>
                  </div>
                </div>

                <div className="order-item-right">
                  <div className="order-item-price">${item.sales?.toLocaleString()}</div>
                  <div className="order-item-count">{Math.round(item.sales / item.orders * 10) / 10} avg</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Branch Rankings Table */}
      <div className="branch-ranking-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.5rem' }}>Branch Performance Ranking</h2>
          <button className="btn-neo btn-neo-lime" onClick={() => onNavigate('procurement')}>
            📦 Plan Group Orders
          </button>
        </div>

        <div className="neo-table-container">
          <table className="neo-table">
            <thead>
              <tr>
                <th>Branch</th>
                <th>Gross Sales</th>
                <th>Purchases</th>
                <th>Food Cost %</th>
                <th>Waste Cost</th>
                <th>Waste %</th>
                <th>Unexplained Var ($)</th>
                <th>Var %</th>
                <th>Audit Flags</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {(data?.branch_rankings || []).map((b) => (
                <tr key={b.branch_id}>
                  <td>
                    <span className="branch-name-pill">{b.branch_name}</span>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)' }}>ID: {b.branch_id}</div>
                  </td>
                  <td style={{ fontWeight: 700 }}>${b.sales?.toLocaleString()}</td>
                  <td>${b.purchases?.toLocaleString()}</td>
                  <td>
                    <span className={`pill-badge ${b.food_cost_pct > 32 ? 'pill-badge-red' : 'pill-badge-white'}`}>
                      {b.food_cost_pct}%
                    </span>
                  </td>
                  <td style={{ color: '#DC2626', fontWeight: 700 }}>${b.waste_cost?.toLocaleString()}</td>
                  <td>
                    <span className={`pill-badge ${b.waste_pct > 8 ? 'pill-badge-red' : 'pill-badge-yellow'}`}>
                      {b.waste_pct}%
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>${b.variance_cost?.toLocaleString()}</td>
                  <td>
                    <span className={`pill-badge ${b.variance_pct > 15 ? 'pill-badge-red' : (b.variance_pct > 6 ? 'pill-badge-yellow' : 'pill-badge-white')}`}>
                      {b.variance_pct > 0 ? `+${b.variance_pct}%` : `${b.variance_pct}%`}
                    </span>
                  </td>
                  <td>
                    {b.items_flagged > 0 ? (
                      <span className="pill-badge pill-badge-red">{b.items_flagged} Alerts</span>
                    ) : (
                      <span className="pill-badge pill-badge-lime">Healthy</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="btn-neo btn-neo-yellow"
                      style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                      onClick={() => {
                        setSelectedBranch(b.branch_id);
                        onNavigate('branch-view');
                      }}
                    >
                      Inspect →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
