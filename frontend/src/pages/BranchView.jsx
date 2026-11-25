import React, { useState, useEffect } from 'react';
import { fetchBranchView } from '../api';
import { IconDownload } from '../components/Icons';
import { formatUnitQty, formatINR, formatPct } from '../utils/formatters';
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
    const headers = ["Ingredient", "Category", "Unit", "Opening", "Purchases", "Closing", "Actual Usage", "Theoretical Usage", "Logged Waste", "Unexplained Var", "Var %", "Var (INR)", "Z-Score"];
    const rows = data.ingredients.map(i => [
      `"${i.ingredient_name}"`,
      i.category,
      i.base_unit,
      Math.round(i.opening_stock),
      Math.round(i.purchased_qty),
      Math.round(i.closing_stock),
      Math.round(i.actual_usage),
      Math.round(i.theoretical_usage),
      Math.round(i.logged_waste),
      Math.round(i.unexplained_variance),
      Math.round(i.variance_pct),
      Math.round(i.variance_cost),
      Math.round(i.z_score || 0)
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
          <h2>{data?.branch?.name || "Koregaon Park"}</h2>
          <div className="branch-meta-row">
            <span className="pill-badge pill-badge-white">Branch ID: {currentBranchId}</span>
            <span className="pill-badge pill-badge-white">{data?.branch?.location || "North Main Road, Pune"}</span>
            <span className="pill-badge pill-badge-yellow">{data?.branch?.capacity || 120} Seats</span>
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
            <IconDownload size={16} /> Export CSV
          </button>
        </div>
      </div>

      {/* Clean Category Filter Bar (Formula banner removed per user request) */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', background: '#FFFFFF', padding: '12px 20px', border: 'var(--border-bold)', borderRadius: 'var(--radius-pill)', boxShadow: 'var(--shadow-neo-sm)' }}>
        <span style={{ fontWeight: 800, fontSize: '0.85rem', alignSelf: 'center', marginRight: 8, textTransform: 'uppercase' }}>
          Category:
        </span>
        {['All', 'Meat & Poultry', 'Produce', 'Dairy', 'Dry Goods'].map(cat => (
          <button
            key={cat}
            className={`btn-neo ${category === cat ? 'btn-neo-lime' : ''}`}
            style={{ padding: '6px 14px', fontSize: '0.82rem' }}
            onClick={() => setCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Key Totals Cards with whole numbers */}
      <div className="branch-kpis-bar">
        <div className="branch-kpi-box">
          <div className="branch-kpi-label">Total Spend (90D)</div>
          <div className="branch-kpi-value">{formatINR(data?.total_spend)}</div>
        </div>
        <div className="branch-kpi-box">
          <div className="branch-kpi-label">Logged Waste Cost</div>
          <div className="branch-kpi-value" style={{ color: '#DC2626' }}>{formatINR(data?.total_waste_cost)}</div>
        </div>
        <div className="branch-kpi-box">
          <div className="branch-kpi-label">Unexplained Variance Cost</div>
          <div className="branch-kpi-value" style={{ color: (data?.total_variance_cost || 0) > 0 ? '#DC2626' : '#16A34A' }}>
            {formatINR(data?.total_variance_cost)}
          </div>
        </div>
      </div>

      {/* Ingredient Reconciliation Table - Scaled Units & Whole Numbers */}
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
              <th>Status</th>
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
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)' }}>{row.canonical_id}</div>
                  </td>
                  <td><span className="pill-badge pill-badge-white">{row.category}</span></td>
                  <td>{formatUnitQty(row.opening_stock, row.base_unit)}</td>
                  <td>{formatUnitQty(row.purchased_qty, row.base_unit)}</td>
                  <td>{formatUnitQty(row.closing_stock, row.base_unit)}</td>
                  <td><strong>{formatUnitQty(row.actual_usage, row.base_unit)}</strong></td>
                  <td>{formatUnitQty(row.theoretical_usage, row.base_unit)}</td>
                  <td style={{ color: '#DC2626' }}>{formatUnitQty(row.logged_waste, row.base_unit)}</td>
                  <td style={{ fontWeight: 800 }}>
                    {row.unexplained_variance > 0 ? `+${formatUnitQty(row.unexplained_variance, row.base_unit)}` : formatUnitQty(row.unexplained_variance, row.base_unit)}
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)', marginTop: 2 }}>
                      {formatINR(row.variance_cost)}
                    </div>
                  </td>
                  <td>
                    {isOverPortioning && (
                      <span className="pill-badge pill-badge-yellow">Portion Creep</span>
                    )}
                    {isHighDairy && (
                      <span className="pill-badge pill-badge-red">Cooler Spoilage</span>
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
