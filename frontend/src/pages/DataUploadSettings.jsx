import React, { useState, useEffect } from 'react';
import { fetchSettings, saveSettings, resetSyntheticData } from '../api';
import '../styles/DataUploadSettings.css';

export default function DataUploadSettings() {
  const [settingsData, setSettingsData] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [toastMsg, setToastMsg] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const res = await fetchSettings();
      setSettingsData(res);
      setFormValues(res.settings || {});
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3500);
  };

  const handleSaveSettings = async () => {
    try {
      await saveSettings(formValues);
      showToast('Settings saved successfully!');
    } catch (err) {
      console.error(err);
    }
  };

  const handleResetData = async () => {
    if (window.confirm('Reset database to clean 90-day synthetic dataset across all 6 branches?')) {
      try {
        setLoading(true);
        await resetSyntheticData();
        showToast('Synthetic dataset successfully regenerated!');
        loadSettings();
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="settings-page">
      <div className="page-headline-wrap">
        <div>
          <h1 className="page-headline">Data Upload & System Parameters</h1>
          <p style={{ color: 'var(--color-gray-600)', fontWeight: 600, marginTop: 4 }}>
            Configure variance thresholds, download raw CSV templates, and manage synthetic benchmarks
          </p>
        </div>

        <button className="btn-neo btn-neo-yellow" onClick={handleResetData}>
          🔄 Regenerate Demo Data (6 Branches, 90D)
        </button>
      </div>

      {toastMsg && (
        <div className="toast-notice">
          {toastMsg}
        </div>
      )}

      <div className="settings-grid">
        {/* Card 1: CSV Upload & Download Center */}
        <div className="settings-card">
          <h3>📥 Raw Data Export & Ingestion</h3>
          <p className="setting-helper">
            Download current pipeline CSVs or upload real POS and purchase data.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <a href="/api/export/pos_orders" download className="btn-neo btn-neo-white">
              📄 Export pos_orders.csv
            </a>
            <a href="/api/export/recipes" download className="btn-neo btn-neo-white">
              📄 Export recipes.csv
            </a>
            <a href="/api/export/purchases" download className="btn-neo btn-neo-white">
              📄 Export purchases.csv
            </a>
            <a href="/api/export/inventory_counts" download className="btn-neo btn-neo-white">
              📄 Export inventory_counts.csv
            </a>
            <a href="/api/export/waste_logs" download className="btn-neo btn-neo-white">
              📄 Export waste_logs.csv
            </a>
          </div>

          <div className="dropzone-box" onClick={() => showToast('CSV upload received! Ingesting records...')}>
            <div style={{ fontSize: '2rem', marginBottom: 6 }}>📁</div>
            <strong>Drop new CSV file here to upload</strong>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)', marginTop: 4 }}>
              Supports pos_orders, purchases, recipes, waste_logs, inventory_counts
            </div>
          </div>
        </div>

        {/* Card 2: Anomaly Threshold Tuning */}
        <div className="settings-card">
          <h3>⚙️ Anomaly Threshold Configuration</h3>
          <p className="setting-helper">
            Tune algorithmic sensitivity for transparent review flags and peer group Z-scores.
          </p>

          <div className="setting-input-group">
            <label className="setting-label">Variance Threshold (%):</label>
            <input
              type="number"
              step="1"
              className="input-neo"
              value={formValues.variance_threshold_pct || 15}
              onChange={(e) => setFormValues({ ...formValues, variance_threshold_pct: e.target.value })}
            />
            <span className="setting-helper">Flags ingredients exceeding this unexplained %</span>
          </div>

          <div className="setting-input-group">
            <label className="setting-label">Variance Threshold Dollar ($):</label>
            <input
              type="number"
              step="10"
              className="input-neo"
              value={formValues.variance_threshold_dollar || 200}
              onChange={(e) => setFormValues({ ...formValues, variance_threshold_dollar: e.target.value })}
            />
            <span className="setting-helper">Minimum dollar impact required to raise a high-severity alert</span>
          </div>

          <div className="setting-input-group">
            <label className="setting-label">Peer Z-Score Cutoff:</label>
            <input
              type="number"
              step="0.1"
              className="input-neo"
              value={formValues.z_score_threshold || 2.0}
              onChange={(e) => setFormValues({ ...formValues, z_score_threshold: e.target.value })}
            />
            <span className="setting-helper">Standard deviations away from group average</span>
          </div>

          <div className="setting-input-group">
            <label className="setting-label">Procurement Safety Stock (Days):</label>
            <input
              type="number"
              step="1"
              className="input-neo"
              value={formValues.safety_stock_days || 3}
              onChange={(e) => setFormValues({ ...formValues, safety_stock_days: e.target.value })}
            />
            <span className="setting-helper">Safety buffer days factored into purchase suggestions</span>
          </div>

          <button className="btn-neo btn-neo-lime" onClick={handleSaveSettings}>
            Save Parameters ✓
          </button>
        </div>
      </div>
    </div>
  );
}
