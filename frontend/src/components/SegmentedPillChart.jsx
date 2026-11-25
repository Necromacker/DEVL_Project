import React from 'react';

export default function SegmentedPillChart({ data = [], activePeriod = 'WEEK', onPeriodChange }) {
  // Period tabs
  const periods = ['WEEK', 'MONTH', 'YEAR', 'CUSTOM'];

  return (
    <div className="segmented-chart-container">
      {/* Top period selector matching reference image */}
      <div className="chart-period-tabs">
        {periods.map((p) => (
          <button
            key={p}
            className={`period-tab-btn ${activePeriod === p ? 'active' : ''}`}
            onClick={() => onPeriodChange && onPeriodChange(p)}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Segmented Capsule Pillars */}
      <div className="pill-bars-wrapper">
        <div className="y-axis-labels">
          <span>20k</span>
          <span>15k</span>
          <span>10k</span>
          <span>5k</span>
          <span>0</span>
        </div>

        <div className="bars-flex">
          {data.map((col, idx) => {
            const isHighlight = col.highlight || col.day === 'Thu' || col.day === 'Sat';
            const totalBlocks = col.total_blocks || 5;
            const yellowBlocks = col.yellow_blocks || 1;

            // Render array of blocks from top to bottom
            const blocks = [];
            for (let b = totalBlocks - 1; b >= 0; b--) {
              let blockClass = 'pill-block';
              if (isHighlight) {
                blockClass += ' pill-block-purple';
              } else if (b < yellowBlocks) {
                blockClass += ' pill-block-yellow';
              } else {
                blockClass += ' pill-block-white';
              }
              blocks.push(<div key={b} className={blockClass} />);
            }

            return (
              <div key={col.day || idx} className="day-column">
                <div className="column-pills-stack">
                  {blocks}
                </div>
                <div className={`column-day-label ${isHighlight ? 'day-highlight' : ''}`}>
                  {col.day}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
