let agencies = [];
let meetings = [];
let editingMeetingId = null;
let calYear, calMonth;

async function loadAll() {
  try {
    [agencies, meetings] = await Promise.all([
      api('/api/agencies?limit=500'),
      api('/api/meetings?limit=500'),
    ]);
    populateAgencySelect();
    renderMeetingsList();
    renderCalendar();
  } catch (e) {
    toast(e.message, 'error');
  }
}

function populateAgencySelect() {
  const select = document.getElementById('m-agency');
  if (!select) return;
  select.innerHTML = '<option value="">Select agency…</option>' +
    agencies.map(a => `<option value="${a.id}">${a.name}</option>`).join('');
}

function renderMeetingsList() {
  const tbody = document.getElementById('meetings-tbody');
  if (!meetings.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:48px;color:var(--text-secondary)">No meetings scheduled yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = meetings.map(m => {
    const agency = agencies.find(a => a.id === m.agency_id);
    return `
      <tr>
        <td><strong>${m.title}</strong></td>
        <td>${agency?.name || '—'}</td>
        <td>${fmtDateTime(m.scheduled_date)}</td>
        <td>${m.duration_minutes} min</td>
        <td>${badge(m.status)}</td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn btn-secondary btn-sm" onclick="openNotesModal(${m.id})">Notes</button>
            <a href="/api/meetings/${m.id}/ical" class="btn btn-secondary btn-sm">📅 ICS</a>
            <button class="btn btn-danger btn-sm" onclick="deleteMeeting(${m.id})">Cancel</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderCalendar() {
  const now = new Date();
  if (calYear === undefined) { calYear = now.getFullYear(); calMonth = now.getMonth(); }

  document.getElementById('cal-title').textContent =
    new Date(calYear, calMonth).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' });

  const grid = document.getElementById('cal-grid');
  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const startOffset = (firstDay + 6) % 7; // Mon = 0

  let html = '';
  for (let i = 0; i < startOffset; i++) html += `<div class="cal-cell other-month"></div>`;

  for (let d = 1; d <= daysInMonth; d++) {
    const isToday = now.getFullYear() === calYear && now.getMonth() === calMonth && now.getDate() === d;
    const dayMeetings = meetings.filter(m => {
      const md = new Date(m.scheduled_date);
      return md.getFullYear() === calYear && md.getMonth() === calMonth && md.getDate() === d;
    });
    html += `
      <div class="cal-cell ${isToday ? 'today' : ''}">
        <div class="cal-date">${d}</div>
        ${dayMeetings.map(m => `
          <div class="cal-event" onclick="openNotesModal(${m.id})" title="${m.title}">
            ${new Date(m.scheduled_date).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })} ${m.title}
          </div>
        `).join('')}
      </div>
    `;
  }
  grid.innerHTML = html;
}

function prevMonth() { calMonth--; if (calMonth < 0) { calMonth = 11; calYear--; } renderCalendar(); }
function nextMonth() { calMonth++; if (calMonth > 11) { calMonth = 0; calYear++; } renderCalendar(); }

async function scheduleMeeting(e) {
  e.preventDefault();
  const payload = {
    agency_id: parseInt(document.getElementById('m-agency').value),
    title: document.getElementById('m-title').value.trim(),
    scheduled_date: document.getElementById('m-date').value,
    duration_minutes: parseInt(document.getElementById('m-duration').value) || 60,
    description: document.getElementById('m-description').value.trim(),
    location: document.getElementById('m-location').value.trim(),
  };
  if (!payload.agency_id) return toast('Select an agency', 'warning');
  if (!payload.title) return toast('Title is required', 'warning');
  if (!payload.scheduled_date) return toast('Date is required', 'warning');

  const sendInvite = document.getElementById('m-send-invite').checked;
  const btn = document.getElementById('schedule-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Scheduling…';
  try {
    await api(`/api/meetings?send_invite=${sendInvite}`, { method: 'POST', body: payload });
    toast('Meeting scheduled' + (sendInvite ? ' and invite sent' : ''), 'success');
    closeModal('meeting-modal');
    document.getElementById('meeting-form').reset();
    await loadAll();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Schedule Meeting';
  }
}

function openNotesModal(id) {
  editingMeetingId = id;
  const m = meetings.find(x => x.id === id);
  if (!m) return;
  const agency = agencies.find(a => a.id === m.agency_id);
  document.getElementById('notes-title').textContent = m.title;
  document.getElementById('notes-agency').textContent = agency?.name || '—';
  document.getElementById('notes-date').textContent = fmtDateTime(m.scheduled_date);
  document.getElementById('n-status').value = m.status;
  document.getElementById('n-outcome').value = m.outcome || '';
  document.getElementById('n-notes').value = m.meeting_notes || '';
  openModal('notes-modal');
}

async function saveMeetingNotes(e) {
  e.preventDefault();
  const payload = {
    status: document.getElementById('n-status').value,
    outcome: document.getElementById('n-outcome').value,
    meeting_notes: document.getElementById('n-notes').value.trim(),
  };
  try {
    await api(`/api/meetings/${editingMeetingId}`, { method: 'PUT', body: payload });
    toast('Meeting notes saved', 'success');
    closeModal('notes-modal');
    await loadAll();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function deleteMeeting(id) {
  const m = meetings.find(x => x.id === id);
  if (!confirm(`Cancel meeting "${m?.title}"?`)) return;
  try {
    await api(`/api/meetings/${id}`, { method: 'DELETE' });
    toast('Meeting cancelled', 'success');
    await loadAll();
  } catch (e) {
    toast(e.message, 'error');
  }
}

document.getElementById('meeting-form')?.addEventListener('submit', scheduleMeeting);
document.getElementById('notes-form')?.addEventListener('submit', saveMeetingNotes);

loadAll();
