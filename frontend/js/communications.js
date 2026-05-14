let agencies = [];
let communications = [];
let selectedComm = null;

const params = new URLSearchParams(location.search);
const preselectedAgency = params.get('agency_id');

async function loadAll() {
  try {
    [agencies, communications] = await Promise.all([
      api('/api/agencies?limit=500'),
      api('/api/communications?limit=500'),
    ]);
    populateAgencySelects();
    renderList(communications);
    if (preselectedAgency) {
      document.getElementById('filter-agency').value = preselectedAgency;
      filterComms();
    }
  } catch (e) {
    toast(e.message, 'error');
  }
}

function populateAgencySelects() {
  const opts = agencies.map(a => `<option value="${a.id}">${a.name}</option>`).join('');
  ['filter-agency', 'send-agency'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = `<option value="">All agencies</option>` + opts;
  });
}

function renderList(comms) {
  const list = document.getElementById('email-list');
  if (!comms.length) {
    list.innerHTML = `<div class="empty-state" style="padding:40px 20px"><p>No emails yet</p></div>`;
    return;
  }
  list.innerHTML = comms.map(c => {
    const agency = agencies.find(a => a.id === c.agency_id);
    return `
      <div class="email-item ${selectedComm?.id === c.id ? 'active' : ''}" onclick="showDetail(${c.id})">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          ${badge(c.direction)}
          <span style="font-size:12px;color:var(--text-secondary)">${fmtDateTime(c.date)}</span>
        </div>
        <div class="email-item-subject">${c.subject}</div>
        <div class="email-item-meta">${agency?.name || 'Unknown agency'}</div>
      </div>
    `;
  }).join('');
}

function showDetail(id) {
  selectedComm = communications.find(c => c.id === id);
  if (!selectedComm) return;
  renderList(getCurrentFiltered());
  const agency = agencies.find(a => a.id === selectedComm.agency_id);
  const detail = document.getElementById('email-detail');
  detail.innerHTML = `
    <div class="email-detail-subject">${selectedComm.subject}</div>
    <div class="email-detail-meta">
      <strong>${selectedComm.direction === 'sent' ? 'To' : 'From'}:</strong>
      ${selectedComm.direction === 'sent' ? selectedComm.email_to : selectedComm.email_from}<br>
      <strong>Agency:</strong> ${agency?.name || '—'}<br>
      <strong>Date:</strong> ${fmtDateTime(selectedComm.date)}<br>
      <strong>Status:</strong> ${badge(selectedComm.status)}
    </div>
    <div class="email-detail-body">${selectedComm.message}</div>
  `;
}

function getCurrentFiltered() {
  const agencyId = document.getElementById('filter-agency')?.value;
  const direction = document.getElementById('filter-direction')?.value;
  return communications.filter(c => {
    if (agencyId && c.agency_id !== parseInt(agencyId)) return false;
    if (direction && c.direction !== direction) return false;
    return true;
  });
}

function filterComms() {
  const filtered = getCurrentFiltered();
  renderList(filtered);
}

async function sendEmail(e) {
  e.preventDefault();
  const agencyId = parseInt(document.getElementById('send-agency').value);
  if (!agencyId) return toast('Select an agency', 'warning');
  const payload = {
    agency_id: agencyId,
    subject: document.getElementById('send-subject').value.trim(),
    message: document.getElementById('send-body').value.trim(),
    use_template: document.getElementById('use-template').checked,
  };
  if (!payload.subject) return toast('Subject is required', 'warning');
  if (!payload.message && !payload.use_template) return toast('Message or template required', 'warning');

  const btn = document.getElementById('send-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Sending…';
  try {
    await api('/api/communications/send', { method: 'POST', body: payload });
    toast('Email sent successfully', 'success');
    closeModal('compose-modal');
    document.getElementById('compose-form').reset();
    await loadAll();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Send Email';
  }
}

async function fetchInbox() {
  const btn = document.getElementById('fetch-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Checking inbox…';
  try {
    const res = await api('/api/communications/fetch-inbox', { method: 'POST' });
    toast(res.message, 'success');
    await loadAll();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Check Inbox';
  }
}

document.getElementById('filter-agency')?.addEventListener('change', filterComms);
document.getElementById('filter-direction')?.addEventListener('change', filterComms);
document.getElementById('compose-form')?.addEventListener('submit', sendEmail);

// Toggle template hint
document.getElementById('use-template')?.addEventListener('change', function () {
  document.getElementById('template-hint').style.display = this.checked ? 'block' : 'none';
});

loadAll();
