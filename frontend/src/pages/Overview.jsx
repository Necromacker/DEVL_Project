import React, { useState, useEffect } from 'react';
import SegmentedPillChart from '../components/SegmentedPillChart';
import { fetchOverview } from '../api';
import { IconRupee, IconWallet, IconChart } from '../components/Icons';
import { formatINR, formatPct } from '../utils/formatters';
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

  const kpis = data?.kpis || {
    total_purchases: 4567,
    total_waste: 40234,
    unexplained_variance: 2845,
    total_sales: 44346,
    waste_pct: 3,
    variance_pct: 5,
    food_cost_pct: 29,
    active_branches: 6
  };

  // Recent order items matching reference image layout with clean URLs
  const recentItems = [
    {
      name: "Burger",
      sub: "3",
      price: "₹3,900",
      count: "1300",
      bgColor: "#D7B7FD",
      imgUrl: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=80&auto=format&fit=crop&q=80"
    },
    {
      name: "Pizza",
      sub: "₹320",
      price: "₹680",
      count: "20",
      bgColor: "#FFE57F",
      imgUrl: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=80&auto=format&fit=crop&q=80"
    },
    {
      name: "Grilled Bowl",
      sub: "₹380",
      price: "₹44,346",
      count: "2680",
      bgColor: "#CCFF00",
      imgUrl: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=80&auto=format&fit=crop&q=80"
    },
    {
      name: "Pasta Alfredo",
      sub: "₹420",
      price: "₹26,100",
      count: "1450",
      bgColor: "#D7B7FD",
      imgUrl: "https://images.unsplash.com/photo-1621996346565-e3d5d6281084?w=80&auto=format&fit=crop&q=80"
    }
  ];

  return (
    <div className="overview-page">
      {/* 3 Metric Cards: Revenue, Expenses, Sales - all matching the reference card UI */}
      <div className="kpi-cards-grid">
        {/* Card 1: Pastel Yellow Card (Revenue) */}
        <div className="kpi-card-yellow">
          <div className="card-header-row">
            <div className="card-icon-circle">
              <IconChart size={18} color="#121212" />
            </div>
            <div className="card-menu-dot">•••</div>
          </div>
          <div className="card-metric-section">
            <div className="card-metric-label">Revenue</div>
            <div className="card-metric-value">{formatINR(kpis.total_purchases)}</div>
            <div className="card-metric-sub">
              <span className="pill-badge pill-badge-white">Food Cost {formatPct(kpis.food_cost_pct)}</span>
            </div>
          </div>
        </div>

        {/* Card 2: Pastel Lavender Card (Expenses) */}
        <div className="kpi-card-purple">
          <div className="card-header-row">
            <div className="card-icon-circle">
              <IconWallet size={18} color="#121212" />
            </div>
            <div className="card-menu-dot">•••</div>
          </div>
          <div className="card-metric-section">
            <div className="card-metric-label">Expenses</div>
            <div className="card-metric-value">{formatINR(kpis.total_waste)}</div>
            <div className="card-metric-sub">
              <span className="pill-badge pill-badge-white">Waste {formatPct(kpis.waste_pct)}</span>
            </div>
          </div>
        </div>

        {/* Card 3: Crisp White Card (Sales - exact same card UI, whole number, no decimals) */}
        <div className="kpi-card-white">
          <div className="card-header-row">
            <div className="card-icon-circle">
              <IconRupee size={18} color="#121212" />
            </div>
            <div className="card-menu-dot">•••</div>
          </div>
          <div className="card-metric-section">
            <div className="card-metric-label">Sales</div>
            <div className="card-metric-value">{formatINR(kpis.total_sales)}</div>
            <div className="card-metric-sub">
              <span className="pill-badge pill-badge-lime">90D Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics 2-Column: Segmented Bar Chart + Recent Order Items */}
      <div className="overview-analytics-grid">
        {/* Left: Segmented Stacked Pill Bar Chart */}
        <div className="chart-panel-card">
          <div className="chart-header-row">
            <div className="chart-title-group">
              <h3>Demand & Consumption Rhythm</h3>
              <p>Weekly sales patterns and consumption cycle</p>
            </div>
            <span className="pill-badge pill-badge-yellow">Weekly</span>
          </div>

          <SegmentedPillChart
            data={data?.trend_bars || []}
            activePeriod={activePeriod}
            onPeriodChange={setActivePeriod}
          />
        </div>

        {/* Right: Recent Order Items list matching reference image */}
        <div className="recent-orders-card">
          <div className="recent-orders-header">
            <h3>Recent Order</h3>
            <span className="view-all-link" onClick={() => onNavigate('branch-view')}>View All</span>
          </div>

          <div className="orders-items-list">
            {recentItems.map((item, idx) => (
              <div key={idx} className="order-pill-row">
                <div className="order-item-left">
                  <div className="order-avatar-icon" style={{ backgroundColor: item.bgColor, overflow: 'hidden' }}>
                    <img
                      src={item.imgUrl}
                      alt={item.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  </div>
                  <div>
                    <div className="order-item-name">{item.name}</div>
                    <div className="order-item-sub">{item.sub}</div>
                  </div>
                </div>

                <div className="order-item-right">
                  <div className="order-item-price">{item.price}</div>
                  <div className="order-item-count">{item.count}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Team / Branch Manager Cards matching Reference Image with Pune Branches */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
        <div className="neo-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', border: 'var(--border-thick)', overflow: 'hidden' }}>
              <img
                src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80"
                alt="Adam Smith"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.05rem' }}>
                Adam Smith <span style={{ color: '#EAB308', fontSize: '0.9rem' }}>★ 5.0</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--color-gray-600)', fontWeight: 600 }}>Sales Manager • Koregaon Park, Pune</div>
            </div>
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.25rem' }}>
            40 HR/W
          </div>
        </div>

        <div className="neo-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', border: 'var(--border-thick)', overflow: 'hidden' }}>
              <img
                src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=100&auto=format&fit=crop&q=80"
                alt="Elena Rostova"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.05rem' }}>
                Elena Rostova <span style={{ color: '#EAB308', fontSize: '0.9rem' }}>★ 4.9</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--color-gray-600)', fontWeight: 600 }}>Inventory Lead • Viman Nagar, Pune</div>
            </div>
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.25rem' }}>
            38 HR/W
          </div>
        </div>
      </div>

      {/* Branch Rankings Table - Pune Branches & Whole Numbers */}
      <div className="branch-ranking-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.5rem' }}>Pune Branch Performance Ranking</h2>
          <button className="btn-neo btn-neo-lime" onClick={() => onNavigate('procurement')}>
            Plan Orders →
          </button>
        </div>

        <div className="neo-table-container">
          <table className="neo-table">
            <thead>
              <tr>
                <th>Pune Branch</th>
                <th>Gross Sales</th>
                <th>Purchases</th>
                <th>Food Cost %</th>
                <th>Waste Cost</th>
                <th>Waste %</th>
                <th>Unexplained Var</th>
                <th>Audit Status</th>
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
                  <td style={{ fontWeight: 700 }}>{formatINR(b.sales)}</td>
                  <td>{formatINR(b.purchases)}</td>
                  <td>
                    <span className={`pill-badge ${b.food_cost_pct > 32 ? 'pill-badge-red' : 'pill-badge-white'}`}>
                      {formatPct(b.food_cost_pct)}
                    </span>
                  </td>
                  <td style={{ color: '#DC2626', fontWeight: 700 }}>{formatINR(b.waste_cost)}</td>
                  <td>
                    <span className={`pill-badge ${b.waste_pct > 8 ? 'pill-badge-red' : 'pill-badge-yellow'}`}>
                      {formatPct(b.waste_pct)}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>{formatINR(b.variance_cost)}</td>
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
