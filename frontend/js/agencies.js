let allAgencies = [];
let editingId = null;

async function loadAgencies(search = '', status = '') {
  let url = '/api/agencies?limit=200';
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (status) url += `&status=${status}`;
  try {
    allAgencies = await api(url);
    renderTable(allAgencies);
  } catch (e) {
    toast(e.message, 'error');
  }
}

function renderTable(agencies) {
  const tbody = document.getElementById('agencies-tbody');
  if (!agencies.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:48px;color:var(--text-secondary)">No agencies found. Use "Find Agencies" to discover UK care agencies.</td></tr>`;
    return;
  }
  tbody.innerHTML = agencies.map(a => `
    <tr>
      <td><strong>${a.name}</strong></td>
      <td style="max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${a.address || '—'}</td>
      <td>${a.phone || '—'}</td>
      <td>${a.contact_person || '—'}</td>
      <td>${a.email ? `<a href="mailto:${a.email}">${a.email}</a>` : '—'}</td>
      <td>${badge(a.status)}</td>
      <td>
        <div style="display:flex;gap:6px">
          <button class="btn btn-secondary btn-sm" onclick="editAgency(${a.id})">Edit</button>
          <button class="btn btn-secondary btn-sm" onclick="window.location='/communications.html?agency_id=${a.id}'">Email</button>
          <button class="btn btn-danger btn-sm" onclick="deleteAgency(${a.id}, '${a.name.replace(/'/g,"\\'")}')">Delete</button>
        </div>
      </td>
    </tr>
  `).join('');
}

async function editAgency(id) {
  const a = allAgencies.find(x => x.id === id);
  if (!a) return;
  editingId = id;
  document.getElementById('modal-title').textContent = 'Edit Agency';
  document.getElementById('f-name').value = a.name || '';
  document.getElementById('f-address').value = a.address || '';
  document.getElementById('f-phone').value = a.phone || '';
  document.getElementById('f-contact').value = a.contact_person || '';
  document.getElementById('f-email').value = a.email || '';
  document.getElementById('f-website').value = a.website || '';
  document.getElementById('f-status').value = a.status || 'new';
  document.getElementById('f-notes').value = a.notes || '';
  openModal('agency-modal');
}

function newAgency() {
  editingId = null;
  document.getElementById('modal-title').textContent = 'Add Agency';
  document.getElementById('agency-form').reset();
  openModal('agency-modal');
}

async function saveAgency(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById('f-name').value.trim(),
    address: document.getElementById('f-address').value.trim(),
    phone: document.getElementById('f-phone').value.trim(),
    contact_person: document.getElementById('f-contact').value.trim(),
    email: document.getElementById('f-email').value.trim(),
    website: document.getElementById('f-website').value.trim(),
    status: document.getElementById('f-status').value,
    notes: document.getElementById('f-notes').value.trim(),
  };
  try {
    if (editingId) {
      await api(`/api/agencies/${editingId}`, { method: 'PUT', body: payload });
      toast('Agency updated', 'success');
    } else {
      await api('/api/agencies', { method: 'POST', body: payload });
      toast('Agency added', 'success');
    }
    closeModal('agency-modal');
    loadAgencies();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function deleteAgency(id, name) {
  if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
  try {
    await api(`/api/agencies/${id}`, { method: 'DELETE' });
    toast('Agency deleted', 'success');
    loadAgencies();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function findAgencies() {
  const btn = document.getElementById('find-btn');
  const maxResults = parseInt(document.getElementById('scrape-count').value) || 50;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Searching CQC Registry…';
  try {
    const res = await api('/api/scrape', { method: 'POST', body: { max_results: maxResults, page: 1 } });
    toast('Search started. This may take a minute…', 'info');
    pollScrapeStatus(btn);
  } catch (e) {
    toast(e.message, 'error');
    btn.disabled = false;
    btn.textContent = 'Find Agencies';
  }
}

async function pollScrapeStatus(btn) {
  const interval = setInterval(async () => {
    try {
      const status = await api('/api/scrape/status');
      if (!status.running) {
        clearInterval(interval);
        btn.disabled = false;
        btn.textContent = 'Find Agencies';
        toast(status.message || 'Search complete', 'success');
        loadAgencies();
      }
    } catch {
      clearInterval(interval);
      btn.disabled = false;
      btn.textContent = 'Find Agencies';
    }
  }, 2000);
}

// Search & filter
document.getElementById('search-input')?.addEventListener('input', e => {
  const status = document.getElementById('status-filter').value;
  loadAgencies(e.target.value, status);
});

document.getElementById('status-filter')?.addEventListener('change', e => {
  const search = document.getElementById('search-input').value;
  loadAgencies(search, e.target.value);
});

document.getElementById('agency-form')?.addEventListener('submit', saveAgency);

loadAgencies();
