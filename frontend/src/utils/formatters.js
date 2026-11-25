/**
 * Formatting utilities for Indian Rupee (INR) and human-friendly scaled physical units.
 * Converts large numbers (e.g. 14,00,000 g -> 1,400 kg; 50,000 ml -> 50 L)
 * and ensures all numbers are clean whole numbers without decimals.
 */

export function formatUnitQty(val, baseUnit = '') {
  if (val === null || val === undefined || isNaN(val)) return '0';
  const num = Math.round(Number(val));
  const u = (baseUnit || '').trim().toLowerCase();

  // Mass conversion: g -> kg
  if (u === 'g' || u === 'grams' || u === 'gram') {
    if (Math.abs(num) >= 1000) {
      const kgVal = Math.round(num / 1000);
      return `${kgVal.toLocaleString('en-IN')} kg`;
    }
    return `${num.toLocaleString('en-IN')} g`;
  }

  // Volume conversion: ml -> L
  if (u === 'ml' || u === 'milliliters' || u === 'milliliter') {
    if (Math.abs(num) >= 1000) {
      const lVal = Math.round(num / 1000);
      return `${lVal.toLocaleString('en-IN')} L`;
    }
    return `${num.toLocaleString('en-IN')} ml`;
  }

  // Count / default
  if (u === 'each' || u === 'ea' || u === 'unit') {
    return `${num.toLocaleString('en-IN')} pcs`;
  }

  return `${num.toLocaleString('en-IN')} ${baseUnit || ''}`.trim();
}

export function formatINR(val) {
  if (val === null || val === undefined || isNaN(val)) return '₹0';
  const num = Math.round(Number(val));
  return `₹${num.toLocaleString('en-IN')}`;
}

export function formatWhole(val) {
  if (val === null || val === undefined || isNaN(val)) return '0';
  return Math.round(Number(val)).toLocaleString('en-IN');
}

export function formatPct(val) {
  if (val === null || val === undefined || isNaN(val)) return '0%';
  return `${Math.round(Number(val))}%`;
}
