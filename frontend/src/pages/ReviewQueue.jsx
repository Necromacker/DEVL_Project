import React, { useState, useEffect } from 'react';
import { fetchReviewQueue, updateReviewFlag } from '../api';
import { IconDownload, IconAlert, IconCheck } from '../components/Icons';
import '../styles/ReviewQueue.css';

export default function ReviewQueue() {
  const [flags, setFlags] = useState([]);
  const [activeStatus, setActiveStatus] = useState('All');
  const [loading, setLoading] = useState(true);
  const [notesDraft, setNotesDraft] = useState({});

  useEffect(() => {
    loadQueue();
  }, [activeStatus]);

  const loadQueue = async () => {
    try {
      setLoading(true);
      const res = await fetchReviewQueue({ status: activeStatus });
      setFlags(res);
      const drafts = {};
      res.forEach(f => { drafts[f.id] = f.notes || ''; });
      setNotesDraft(drafts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (flagId, newStatus) => {
    try {
      await updateReviewFlag(flagId, { status: newStatus, notes: notesDraft[flagId] });
      loadQueue();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveNotes = async (flagId) => {
    try {
      await updateReviewFlag(flagId, { notes: notesDraft[flagId] });
      loadQueue();
    } catch (err) {
      console.error(err);
    }
  };

  const exportQueueCsv = () => {
    const headers = ["Flag ID", "Branch", "Entity ID", "Flag Type", "Severity", "Reason", "Status", "Notes"];
    const rows = flags.map(f => [
      f.id,
      `"${f.branch_name}"`,
      f.entity_id,
      f.flag_type,
      f.severity_score,
      `"${f.reason.replace(/"/g, '""')}"`,
      f.status,
      `"${(f.notes || '').replace(/"/g, '""')}"`
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `audit_review_queue.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="review-queue-page">
      <div className="page-headline-wrap">
        <div>
          <h1 className="page-headline">Audit & Review Queue</h1>
          <p style={{ color: 'var(--color-gray-600)', fontWeight: 600, marginTop: 4 }}>
            Algorithmic anomaly detection with plain language diagnostics
          </p>
        </div>
        <button className="btn-neo btn-neo-yellow" onClick={exportQueueCsv}>
          <IconDownload size={16} /> Export Queue CSV
        </button>
      </div>

      {/* Status Filter Tabs */}
      <div className="status-tabs-row">
        {['All', 'open', 'investigating', 'resolved'].map(st => (
          <button
            key={st}
            className={`status-tab-btn ${activeStatus === st ? 'active' : ''}`}
            onClick={() => setActiveStatus(st)}
          >
            {st.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Flags List */}
      <div className="flag-cards-list">
        {flags.length === 0 ? (
          <div className="neo-card" style={{ textAlign: 'center', padding: '40px' }}>
            <h3>No flagged items matching status "{activeStatus}"</h3>
          </div>
        ) : (
          flags.map((flag) => {
            const isCritical = flag.severity_score >= 85;
            return (
              <div key={flag.id} className="flag-card">
                <div className="flag-card-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                    <span
                      className="flag-severity-pill"
                      style={{
                        backgroundColor: isCritical ? 'var(--color-red)' : 'var(--color-yellow)',
                        color: isCritical ? '#FFFFFF' : '#121212'
                      }}
                    >
                      Score: {flag.severity_score}
                    </span>
                    <strong style={{ fontSize: '1.1rem' }}>{flag.branch_name}</strong>
                    <span className="pill-badge pill-badge-white">{flag.entity_id}</span>
                  </div>

                  <div>
                    <span
                      className="pill-badge"
                      style={{
                        backgroundColor: flag.status === 'resolved' ? '#DCFCE7' : (flag.status === 'investigating' ? '#FEF9C3' : '#FEE2E2'),
                        color: flag.status === 'resolved' ? '#166534' : (flag.status === 'investigating' ? '#854D0E' : '#991B1B')
                      }}
                    >
                      Status: {flag.status}
                    </span>
                  </div>
                </div>

                <div className="flag-reason-text">
                  <strong>Diagnosis:</strong> {flag.reason}
                </div>

                <div className="flag-actions-bar">
                  <div className="notes-input-wrap">
                    <input
                      type="text"
                      className="input-neo"
                      style={{ flex: 1 }}
                      placeholder="Add investigation notes..."
                      value={notesDraft[flag.id] || ''}
                      onChange={(e) => setNotesDraft({ ...notesDraft, [flag.id]: e.target.value })}
                    />
                    <button className="btn-neo btn-neo-white" onClick={() => handleSaveNotes(flag.id)}>
                      Save Note
                    </button>
                  </div>

                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      className={`btn-neo ${flag.status === 'open' ? 'btn-neo-yellow' : ''}`}
                      style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                      onClick={() => handleStatusChange(flag.id, 'open')}
                    >
                      Open
                    </button>
                    <button
                      className={`btn-neo ${flag.status === 'investigating' ? 'btn-neo-purple' : ''}`}
                      style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                      onClick={() => handleStatusChange(flag.id, 'investigating')}
                    >
                      Investigating
                    </button>
                    <button
                      className={`btn-neo ${flag.status === 'resolved' ? 'btn-neo-lime' : ''}`}
                      style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                      onClick={() => handleStatusChange(flag.id, 'resolved')}
                    >
                      Resolve
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
