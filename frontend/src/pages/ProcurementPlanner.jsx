import React, { useState, useEffect } from 'react';
import { fetchProcurement } from '../api';
import { IconDownload, IconCheck } from '../components/Icons';
import '../styles/ProcurementPlanner.css';

export default function ProcurementPlanner({ selectedBranch, setSelectedBranch, branches = [] }) {
  const [plan, setPlan] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('All');
  const [editedPacks, setEditedPacks] = useState({});
  const [savedNotice, setSavedNotice] = useState(false);

  useEffect(() => {
    loadProcurement();
  }, [selectedBranch, category]);

  const loadProcurement = async () => {
    try {
      setLoading(true);
      const res = await fetchProcurement({
        branch_id: selectedBranch === 'All' ? 'B01' : selectedBranch,
        category: category
      });
      setPlan(res);
      const initial = {};
      res.forEach(item => {
        const key = `${item.branch_id}_${item.canonical_id}`;
        initial[key] = item.suggested_packs;
      });
      setEditedPacks(initial);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePackChange = (key, val) => {
    const num = Math.max(0, parseInt(val) || 0);
    setEditedPacks(prev => ({ ...prev, [key]: num }));
  };

  const calculateTotalOrderSpend = () => {
    return plan.reduce((sum, item) => {
      const key = `${item.branch_id}_${item.canonical_id}`;
      const packs = editedPacks[key] !== undefined ? editedPacks[key] : item.suggested_packs;
      return sum + (packs * item.pack_unit_cost);
    }, 0);
  };

  const exportProcurementCsv = () => {
    const headers = [
      "Branch ID", "Branch Name", "Canonical ID", "Ingredient Name", "Category",
      "Current Stock", "Daily Run Rate", "Days of Supply", "7-Day Projected Demand",
      "Safety Buffer", "Pack Description", "Pack Unit Cost (INR)", "Packs To Order",
      "Total Order Qty (Base)", "Estimated Cost (INR)", "Urgency"
    ];

    const rows = plan.map(item => {
      const key = `${item.branch_id}_${item.canonical_id}`;
      const packs = editedPacks[key] !== undefined ? editedPacks[key] : item.suggested_packs;
      const orderQty = packs * item.pack_size_base;
      const totalCost = packs * item.pack_unit_cost;

      return [
        item.branch_id,
        `"${item.branch_name}"`,
        item.canonical_id,
        `"${item.ingredient_name}"`,
        item.category,
        item.current_stock,
        item.daily_run_rate,
        item.days_of_supply,
        item.projected_7day_demand,
        item.safety_stock_buffer,
        `"${item.pack_description}"`,
        item.pack_unit_cost,
        packs,
        orderQty,
        totalCost.toFixed(2),
        item.urgency
      ];
    });

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `procurement_order_sheet_${selectedBranch}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSaveOrder = () => {
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  const totalSpend = calculateTotalOrderSpend();

  return (
    <div className="procurement-page">
      {/* Banner */}
      <div className="procurement-header-banner">
        <div className="procurement-banner-text">
          <h2>Procurement & Purchase Planner</h2>
          <p style={{ fontWeight: 600, color: 'var(--color-black)', marginTop: 4 }}>
            Forecast demand + waste safety buffer + automated pack size rounding
          </p>
        </div>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select
            className="filter-select"
            value={selectedBranch}
            onChange={(e) => setSelectedBranch(e.target.value)}
          >
            <option value="All">All Branches</option>
            {branches.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
          <button className="btn-neo btn-neo-black" onClick={exportProcurementCsv}>
            <IconDownload size={16} color="#FFFFFF" /> Export CSV
          </button>
        </div>
      </div>

      {/* Summary Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#FFFFFF', padding: '16px 24px', border: 'var(--border-bold)', borderRadius: 'var(--radius-card)', boxShadow: 'var(--shadow-neo)' }}>
        <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--color-gray-600)' }}>
              Projected Order Total
            </span>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800 }}>
              ₹{totalSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
          <span className="pill-badge pill-badge-lime">{plan.length} SKU Items</span>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn-neo btn-neo-yellow" onClick={handleSaveOrder}>
            Save Quantities
          </button>
        </div>
      </div>

      {savedNotice && (
        <div className="toast-notice">
          Procurement adjustments saved successfully!
        </div>
      )}

      {/* Procurement Order Table */}
      <div className="neo-table-container">
        <table className="neo-table">
          <thead>
            <tr>
              <th>Ingredient</th>
              <th>Status</th>
              <th>Current Stock</th>
              <th>Daily Burn</th>
              <th>Days Supply</th>
              <th>7-Day Demand</th>
              <th>Safety Buffer</th>
              <th>Commercial Pack Size</th>
              <th>Order Packs</th>
              <th>Total Order Qty</th>
              <th>Est. Cost</th>
            </tr>
          </thead>
          <tbody>
            {plan.map((item) => {
              const key = `${item.branch_id}_${item.canonical_id}`;
              const packs = editedPacks[key] !== undefined ? editedPacks[key] : item.suggested_packs;
              const totalCost = (packs * item.pack_unit_cost).toFixed(2);
              const totalOrderQty = (packs * item.pack_size_base).toLocaleString();

              return (
                <tr key={key}>
                  <td>
                    <strong style={{ fontFamily: 'var(--font-display)', fontSize: '0.95rem' }}>{item.ingredient_name}</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)' }}>
                      {item.branch_name} • {item.category}
                    </div>
                  </td>
                  <td>
                    <span
                      className="urgency-badge"
                      style={{
                        backgroundColor: item.urgency === 'Critical Low' ? '#FEE2E2' : (item.urgency === 'Reorder Soon' ? '#FEF9C3' : '#DCFCE7'),
                        color: item.urgency === 'Critical Low' ? '#991B1B' : (item.urgency === 'Reorder Soon' ? '#854D0E' : '#166534')
                      }}
                    >
                      {item.urgency}
                    </span>
                  </td>
                  <td>{item.current_stock?.toLocaleString()} {item.base_unit}</td>
                  <td>{item.daily_run_rate} {item.base_unit}/day</td>
                  <td>
                    <strong style={{ color: item.days_of_supply < 2 ? '#DC2626' : '#121212' }}>
                      {item.days_of_supply} days
                    </strong>
                  </td>
                  <td>{item.projected_7day_demand?.toLocaleString()} {item.base_unit}</td>
                  <td>+{item.safety_stock_buffer?.toLocaleString()} {item.base_unit}</td>
                  <td>
                    <span className="pill-badge pill-badge-white" style={{ fontSize: '0.75rem' }}>
                      {item.pack_description}
                    </span>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)', marginTop: 2 }}>
                      ₹{item.pack_unit_cost} / pack
                    </div>
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      className="order-qty-input"
                      value={packs}
                      onChange={(e) => handlePackChange(key, e.target.value)}
                    />
                  </td>
                  <td style={{ fontWeight: 800 }}>
                    {totalOrderQty} {item.base_unit}
                  </td>
                  <td style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.05rem' }}>
                    ₹{totalCost}
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
