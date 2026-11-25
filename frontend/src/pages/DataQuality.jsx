import React, { useState, useEffect } from 'react';
import { fetchDataQuality, confirmAlias } from '../api';
import '../styles/DataQuality.css';

export default function DataQuality() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMap, setSelectedMap] = useState({});

  useEffect(() => {
    loadQualityData();
  }, []);

  const loadQualityData = async () => {
    try {
      setLoading(true);
      const res = await fetchDataQuality();
      setData(res);
      const initial = {};
      (res.unmapped_aliases || []).forEach(a => {
        initial[a.id] = a.canonical_id || res.canonical_ingredients[0]?.id;
      });
      setSelectedMap(initial);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (aliasId) => {
    try {
      const canonicalId = selectedMap[aliasId];
      await confirmAlias(aliasId, canonicalId);
      loadQualityData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="data-quality-page">
      <div className="page-headline-wrap">
        <div>
          <h1 className="page-headline">Data Quality & Normalization Auditor</h1>
          <p style={{ color: 'var(--color-gray-600)', fontWeight: 600, marginTop: 4 }}>
            Alias fuzzy mapping, missing recipe BOMs, unit conflicts, and count anomaly resolution
          </p>
        </div>
      </div>

      <div className="quality-sections-grid">
        {/* Section 1: Unmapped / Low Confidence Aliases */}
        <div className="quality-card">
          <div className="quality-card-header">
            <h3>1. Ingredient Alias Resolution Queue</h3>
            <p style={{ color: 'var(--color-gray-600)', fontSize: '0.85rem' }}>
              Raw supplier strings with fuzzy match confidence &lt; 80%. Confirm or re-map to a canonical ingredient.
            </p>
          </div>

          <div>
            {(data?.unmapped_aliases || []).length === 0 ? (
              <div style={{ padding: '16px', background: '#F0FDF4', borderRadius: 12, border: '1.5px solid #22C55E' }}>
                🎉 All ingredient aliases are currently 100% mapped and verified!
              </div>
            ) : (
              data?.unmapped_aliases.map((a) => (
                <div key={a.id} className="alias-row-match">
                  <div>
                    <strong style={{ fontSize: '1.05rem', fontFamily: 'var(--font-display)' }}>"{a.alias_name}"</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)' }}>
                      Match Score: <span className="confidence-score">{a.confidence}%</span> • Suggested: <strong>{a.suggested_name}</strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <select
                      className="filter-select"
                      value={selectedMap[a.id] || ''}
                      onChange={(e) => setSelectedMap({ ...selectedMap, [a.id]: e.target.value })}
                    >
                      {(data?.canonical_ingredients || []).map(c => (
                        <option key={c.id} value={c.id}>{c.name} ({c.id})</option>
                      ))}
                    </select>

                    <button className="btn-neo btn-neo-lime" onClick={() => handleConfirm(a.id)}>
                      Confirm Mapping ✓
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Section 2: Missing Recipe BOMs */}
        <div className="quality-card">
          <div className="quality-card-header">
            <h3>2. Missing Recipes & "Not Estimable" Items</h3>
            <p style={{ color: 'var(--color-gray-600)', fontSize: '0.85rem' }}>
              Sales exist in POS, but recipe BOM is incomplete or missing portion quantities. (Theoretical usage is never guessed).
            </p>
          </div>

          <div className="neo-table-container">
            <table className="neo-table">
              <thead>
                <tr>
                  <th>Menu Item ID</th>
                  <th>Menu Item Name</th>
                  <th>Category</th>
                  <th>Identified Issue</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {(data?.missing_recipes || []).map((m) => (
                  <tr key={m.menu_item_id}>
                    <td><strong>{m.menu_item_id}</strong></td>
                    <td>{m.menu_item_name}</td>
                    <td><span className="pill-badge pill-badge-white">{m.category}</span></td>
                    <td style={{ color: '#DC2626', fontWeight: 700 }}>⚠️ {m.issue}</td>
                    <td><span className="pill-badge pill-badge-red">Action Required</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 3: Suspicious Inventory Counts */}
        <div className="quality-card">
          <div className="quality-card-header">
            <h3>3. Inventory Count Discrepancies & Audit Log</h3>
            <p style={{ color: 'var(--color-gray-600)', fontSize: '0.85rem' }}>
              Counts showing &gt;5x historical consumption jumps or transcription errors.
            </p>
          </div>

          <div>
            {(data?.suspicious_counts || []).map((s) => (
              <div key={s.id} style={{ background: '#FEF2F2', border: '2px solid #EF4444', borderRadius: 16, padding: '16px', marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong>{s.branch_name} ({s.branch_id})</strong>
                  <span className="pill-badge pill-badge-red">Suspicious Count Typo</span>
                </div>
                <p style={{ marginTop: 6, fontSize: '0.9rem', color: '#7F1D1D' }}>
                  {s.reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
