import React, { useState, useEffect } from 'react';
import { fetchMenuItems } from '../api';
import '../styles/MenuItemReview.css';

export default function MenuItemReview() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedItem, setExpandedItem] = useState(null);

  useEffect(() => {
    loadMenuItems();
  }, []);

  const loadMenuItems = async () => {
    try {
      setLoading(true);
      const res = await fetchMenuItems();
      setItems(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportMenuCsv = () => {
    const headers = ["Item ID", "Name", "Category", "Price", "Units Sold", "Total Sales", "Cost Per Serving", "Margin %", "Estimable", "Flag"];
    const rows = items.map(i => [
      i.id,
      `"${i.name}"`,
      i.category,
      i.price,
      i.units_sold,
      i.total_sales,
      i.cost_per_serving,
      i.margin_pct,
      i.is_estimable ? "YES" : "NO",
      `"${i.flag_reason || ''}"`
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `menu_items_recipe_audit.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="menu-review-page">
      <div className="page-headline-wrap">
        <div>
          <h1 className="page-headline">Menu Item BOM & Margin Review</h1>
          <p style={{ color: 'var(--color-gray-600)', fontWeight: 600, marginTop: 4 }}>
            Recipe explosion validation, ingredient portion weights & margin risk detection
          </p>
        </div>
        <button className="btn-neo btn-neo-yellow" onClick={exportMenuCsv}>
          📥 Export Menu BOM
        </button>
      </div>

      <div className="menu-items-grid">
        {items.map((item) => {
          const isExpanded = expandedItem === item.id;
          return (
            <div key={item.id} className="menu-card">
              <div className="menu-card-top">
                <div>
                  <div className="menu-card-title">{item.name}</div>
                  <div className="menu-card-category">{item.category} • ID: {item.id}</div>
                </div>

                <div>
                  {item.is_estimable ? (
                    <span className="pill-badge pill-badge-lime">Estimable</span>
                  ) : (
                    <span className="pill-badge pill-badge-red">Not Estimable</span>
                  )}
                </div>
              </div>

              {!item.is_estimable && (
                <div style={{ background: '#FEE2E2', border: '1.5px solid #DC2626', borderRadius: 12, padding: '8px 12px', fontSize: '0.8rem', fontWeight: 700, color: '#991B1B' }}>
                  ⚠️ {item.flag_reason}
                </div>
              )}

              <div className="menu-metrics-row">
                <div className="menu-metric-col">
                  <span className="metric-micro-label">Price</span>
                  <span className="metric-micro-value">${item.price.toFixed(2)}</span>
                </div>
                <div className="menu-metric-col">
                  <span className="metric-micro-label">Est. Cost</span>
                  <span className="metric-micro-value">
                    {item.is_estimable ? `$${item.cost_per_serving.toFixed(2)}` : 'N/A'}
                  </span>
                </div>
                <div className="menu-metric-col">
                  <span className="metric-micro-label">Margin %</span>
                  <span className="metric-micro-value" style={{ color: item.margin_pct > 65 ? '#16A34A' : '#121212' }}>
                    {item.is_estimable ? `${item.margin_pct}%` : 'N/A'}
                  </span>
                </div>
                <div className="menu-metric-col">
                  <span className="metric-micro-label">Sold</span>
                  <span className="metric-micro-value">{item.units_sold}</span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>
                  Gross Revenue: <strong>${item.total_sales?.toLocaleString()}</strong>
                </span>
                <button
                  className="btn-neo btn-neo-white"
                  style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                  onClick={() => setExpandedItem(isExpanded ? null : item.id)}
                >
                  {isExpanded ? 'Hide BOM ▲' : `View BOM (${item.ingredients_count}) ▼`}
                </button>
              </div>

              {isExpanded && (
                <div className="bom-accordion">
                  <div style={{ fontWeight: 800, fontSize: '0.82rem', marginBottom: 6, textTransform: 'uppercase' }}>
                    Recipe Ingredients (adjusted for trim/yield loss):
                  </div>
                  {item.bom.length === 0 ? (
                    <p style={{ fontSize: '0.82rem', color: '#DC2626', fontWeight: 700 }}>
                      No BOM records found. Never guessed in theoretical usage.
                    </p>
                  ) : (
                    item.bom.map((b, bIdx) => (
                      <div key={bIdx} className="bom-ingredient-row">
                        <span>{b.ingredient_name}</span>
                        <span>
                          <strong>{b.quantity !== null ? `${b.quantity} ${b.unit}` : 'Missing Qty'}</strong>
                          {b.yield_pct < 100 && ` (${b.yield_pct}% yield)`}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
