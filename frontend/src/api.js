const API_BASE = '/api';

export async function fetchOverview(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/overview?${query}`);
  return res.json();
}

export async function fetchBranches() {
  const res = await fetch(`${API_BASE}/branches`);
  return res.json();
}

export async function fetchCategories() {
  const res = await fetch(`${API_BASE}/categories`);
  return res.json();
}

export async function fetchBranchView(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/branch-view?${query}`);
  return res.json();
}

export async function fetchMenuItems() {
  const res = await fetch(`${API_BASE}/menu-items`);
  return res.json();
}

export async function fetchProcurement(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/procurement?${query}`);
  return res.json();
}

export async function fetchReviewQueue(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/review-queue?${query}`);
  return res.json();
}

export async function updateReviewFlag(flagId, payload) {
  const res = await fetch(`${API_BASE}/review-queue/${flagId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function fetchDataQuality() {
  const res = await fetch(`${API_BASE}/data-quality`);
  return res.json();
}

export async function confirmAlias(aliasId, canonicalId) {
  const res = await fetch(`${API_BASE}/data-quality/alias/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alias_id: aliasId, canonical_id: canonicalId })
  });
  return res.json();
}

export async function fetchSettings() {
  const res = await fetch(`${API_BASE}/settings`);
  return res.json();
}

export async function saveSettings(payload) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function resetSyntheticData() {
  const res = await fetch(`${API_BASE}/reset-data`, {
    method: 'POST'
  });
  return res.json();
}
