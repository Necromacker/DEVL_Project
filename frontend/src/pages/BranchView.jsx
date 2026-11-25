import React, { useState, useEffect } from 'react';
import { fetchBranchView, fetchBranches } from '../api';
import '../styles/BranchView.css';

export default function BranchView({ selectedBranch, setSelectedBranch, branches = [] }) {
  const [data, setData] = useState(null);
  const [category, setCategory] = useState('All');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBranchData();
  }, [selectedBranch, category]);

  const loadBranchData = async () => {
    try {
      setLoading(true);
      const res = await fetchBranchView({
        branch_id: selectedBranch === 'All' ? 'B01' : selectedBranch,
        category: category
      });
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportBranchCsv = () => {
    if (!data?.ingredients) return;
    const headers = ["Ingredient", "Category", "Unit", "Opening", "Purchases", "Closing", "Actual Usage", "Theoretical Usage", "Logged Waste", "Unexplained Var", "Var %", "Var ($)", "Z-Score"];
    const rows = data.ingredients.map(i => [
      `"${i.ingredient_name}"`,
      i.category,
      i.base_unit,
      i.opening_stock,
      i.purchased_qty,
      i.closing_stock,
      i.actual_usage,
      i.theoretical_usage,
      i.logged_waste,
      i.unexplained_variance,
      i.variance_pct,
      i.variance_cost,
      i.z_score || 0
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `branch_${selectedBranch}_inventory_balance.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const currentBranchId = selectedBranch === 'All' ? 'B01' : selectedBranch;

  return (
    <div className="branch-view-page">
      {/* Branch Header Banner */}
      <div className="branch-header-card">
        <div className="branch-title-group">
          <h2>{data?.branch?.name || "Downtown Bistro"}</h2>
          <div className="branch-meta-row">
            <span className="pill-badge pill-badge-white">Branch ID: {currentBranchId}</span>
            <span className="pill-badge pill-badge-white">Location: {data?.branch?.location || "Financial District"}</span>
            <span className="pill-badge pill-badge-yellow">Capacity: {data?.branch?.capacity || 120} Seats</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select
            className="filter-select"
            value={currentBranchId}
            onChange={(e) => setSelectedBranch(e.target.value)}
          >
            {branches.map(b => (
              <option key={b.id} value={b.id}>{b.name} ({b.id})</option>
            ))}
          </select>
          <button className="btn-neo btn-neo-yellow" onClick={exportBranchCsv}>
            📥 Export CSV
          </button>
        </div>
      </div>

      {/* Reconciliation Formula Banner */}
      <div className="balance-formula-banner">
        <div>
          <span>📐 Formula: </span>
          <span className="formula-tag">Actual Usage = Opening + Purchases - Closing</span>
          <span style={{ margin: '0 8px' }}>&</span>
          <span className="formula-tag">Unexplained = Actual - Theoretical - Logged Waste</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {['All', 'Meat & Poultry', 'Produce', 'Dairy', 'Dry Goods'].map(cat => (
            <button
              key={cat}
              className={`btn-neo ${category === cat ? 'btn-neo-lime' : ''}`}
              style={{ padding: '4px 12px', fontSize: '0.78rem' }}
              onClick={() => setCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Key Totals Cards */}
      <div className="branch-kpis-bar">
        <div className="branch-kpi-box">
          <div className="branch-kpi-label">Total Spend (90D)</div>
          <div className="branch-kpi-value">${data?.total_spend?.toLocaleString() || 0}</div>
        </div>
        <div className="branch-kpi-box">
          <div className="branch-kpi-label">Logged Waste Cost</div>
          <div className="branch-kpi-value" style={{ color: '#DC2626' }}>${data?.total_waste_cost?.toLocaleString() || 0}</div>
        </div>
        <div className="branch-kpi-box">
          <div className="branch-kpi-label">Unexplained Variance Cost</div>
          <div className="branch-kpi-value" style={{ color: data?.total_variance_cost > 0 ? '#DC2626' : '#16A34A' }}>
            ${data?.total_variance_cost?.toLocaleString() || 0}
          </div>
        </div>
      </div>

      {/* Ingredient Reconciliation Table */}
      <div className="neo-table-container">
        <table className="neo-table">
          <thead>
            <tr>
              <th>Canonical Ingredient</th>
              <th>Category</th>
              <th>Opening</th>
              <th>Purchases</th>
              <th>Closing</th>
              <th>Actual Usage</th>
              <th>Theoretical</th>
              <th>Waste</th>
              <th>Unexplained Var</th>
              <th>Var %</th>
              <th>Peer Z-Score</th>
              <th>Diagnosis</th>
            </tr>
          </thead>
          <tbody>
            {(data?.ingredients || []).map((row) => {
              const isOverPortioning = row.variance_pct > 20 && row.canonical_id === 'ING-CHICKEN';
              const isHighDairy = row.waste_pct > 10 && row.category === 'Dairy';

              return (
                <tr key={row.canonical_id}>
                  <td>
                    <strong style={{ fontFamily: 'var(--font-display)', fontSize: '0.95rem' }}>{row.ingredient_name}</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)' }}>{row.canonical_id} • Unit: {row.base_unit}</div>
                  </td>
                  <td><span className="pill-badge pill-badge-white">{row.category}</span></td>
                  <td>{row.opening_stock?.toLocaleString()} {row.base_unit}</td>
                  <td>{row.purchased_qty?.toLocaleString()} {row.base_unit}</td>
                  <td>{row.closing_stock?.toLocaleString()} {row.base_unit}</td>
                  <td><strong>{row.actual_usage?.toLocaleString()} {row.base_unit}</strong></td>
                  <td>{row.theoretical_usage?.toLocaleString()} {row.base_unit}</td>
                  <td style={{ color: '#DC2626' }}>{row.logged_waste?.toLocaleString()} {row.base_unit}</td>
                  <td style={{ fontWeight: 800 }}>
                    {row.unexplained_variance > 0 ? `+${row.unexplained_variance?.toLocaleString()}` : row.unexplained_variance?.toLocaleString()} {row.base_unit}
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)' }}>${row.variance_cost?.toLocaleString()}</div>
                  </td>
                  <td>
                    <span className={`pill-badge ${Math.abs(row.variance_pct) > 15 ? 'pill-badge-red' : (Math.abs(row.variance_pct) > 6 ? 'pill-badge-yellow' : 'pill-badge-lime')}`}>
                      {row.variance_pct > 0 ? `+${row.variance_pct}%` : `${row.variance_pct}%`}
                    </span>
                  </td>
                  <td>
                    <span className={`pill-badge ${Math.abs(row.z_score || 0) > 2 ? 'pill-badge-red' : 'pill-badge-white'}`}>
                      {row.z_score > 0 ? `+${row.z_score}σ` : `${row.z_score || 0}σ`}
                    </span>
                  </td>
                  <td>
                    {isOverPortioning && (
                      <span className="pill-badge pill-badge-yellow">⚠️ Portion Creep</span>
                    )}
                    {isHighDairy && (
                      <span className="pill-badge pill-badge-red">⚠️ Cooler Spoilage</span>
                    )}
                    {!isOverPortioning && !isHighDairy && Math.abs(row.variance_pct) <= 8 && (
                      <span className="pill-badge pill-badge-lime">Balanced</span>
                    )}
                    {!isOverPortioning && !isHighDairy && Math.abs(row.variance_pct) > 8 && (
                      <span className="pill-badge pill-badge-white">Variance Review</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
