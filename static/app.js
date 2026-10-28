function switchTab(name) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  
  const target = document.getElementById(`view-${name}`);
  const btn = document.getElementById(`tab-${name}`);
  if (target) target.classList.remove('hidden');
  if (btn) btn.classList.add('active');

  if (name === 'logs') loadLogs();
  if (name === 'settings') loadSettings();
}

function showToast(message, isError = false) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `pointer-events-auto px-4 py-3 rounded-lg text-sm font-medium shadow-xl border flex items-center space-x-2 transition-all transform duration-200 ${
    isError 
      ? 'bg-rose-950/90 text-rose-200 border-rose-800/60' 
      : 'bg-emerald-950/90 text-emerald-200 border-emerald-800/60'
  }`;
  toast.innerHTML = `<span>${isError ? '⚠️' : '✓'}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    document.getElementById('setHost').value = data.host || '';
    document.getElementById('setPort').value = data.port || 587;
    document.getElementById('setSenderName').value = data.sender_name || '';
    document.getElementById('setSenderEmail').value = data.sender_email || '';
    document.getElementById('setUser').value = data.username || '';
    document.getElementById('setTls').checked = Boolean(data.use_tls);
    document.getElementById('setSsl').checked = Boolean(data.use_ssl);
    document.getElementById('setDryRun').checked = Boolean(data.dry_run);

    const badge = document.getElementById('dryRunBadge');
    if (data.dry_run) badge.classList.remove('hidden');
    else badge.classList.add('hidden');
  } catch (err) {
    showToast('Failed to load settings', true);
  }
}

document.getElementById('settingsForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    host: document.getElementById('setHost').value,
    port: parseInt(document.getElementById('setPort').value),
    sender_name: document.getElementById('setSenderName').value,
    sender_email: document.getElementById('setSenderEmail').value,
    username: document.getElementById('setUser').value,
    use_tls: document.getElementById('setTls').checked,
    use_ssl: document.getElementById('setSsl').checked,
    dry_run: document.getElementById('setDryRun').checked,
  };
  const pass = document.getElementById('setPass').value;
  if (pass) payload.password = pass;

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    showToast(data.message);
    loadSettings();
  } catch (err) {
    showToast('Failed to save settings', true);
  }
});

document.getElementById('singleSendForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('sendSingleBtn');
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerText = 'Dispatching...';

  const formData = new FormData(e.target);
  try {
    const res = await fetch('/api/send', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message);
      e.target.reset();
    } else {
      showToast(data.message || 'Error occurred', true);
    }
  } catch (err) {
    showToast('Network error while sending', true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
});

document.getElementById('batchSendForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  let recipients;
  try {
    recipients = JSON.parse(document.getElementById('batchRecipients').value);
    if (!Array.isArray(recipients)) throw new Error('Root must be an array');
  } catch (err) {
    showToast('Invalid JSON in recipients field: ' + err.message, true);
    return;
  }

  const payload = {
    recipients: recipients,
    subject: document.getElementById('batchSubject').value,
    body: document.getElementById('batchBody').value
  };

  const btn = document.getElementById('sendBatchBtn');
  btn.disabled = true;
  btn.innerText = 'Running Campaign...';

  try {
    const res = await fetch('/api/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    showToast(`Batch completed. Processed ${data.results.length} recipient(s).`);
  } catch (err) {
    showToast('Error during batch execution', true);
  } finally {
    btn.disabled = false;
    btn.innerText = 'Start Batch Campaign';
  }
});

async function loadLogs() {
  const tbody = document.getElementById('logsTableBody');
  try {
    const res = await fetch('/api/logs');
    const logs = await res.json();
    if (!logs.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center py-6 text-slate-500">No logs recorded yet.</td></tr>';
      return;
    }
    tbody.innerHTML = logs.map(l => `
      <tr class="hover:bg-slate-900/40 transition">
        <td class="px-4 py-3 text-xs text-slate-400 font-mono">${l.created_at}</td>
        <td class="px-4 py-3 font-medium text-slate-200">${escapeHtml(l.recipient)}</td>
        <td class="px-4 py-3 text-slate-300">${escapeHtml(l.subject)}</td>
        <td class="px-4 py-3 text-xs">
          ${l.is_dry_run ? '<span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Dry Run</span>' : '<span class="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">Live SMTP</span>'}
        </td>
        <td class="px-4 py-3">
          ${l.status === 'SUCCESS' 
            ? '<span class="text-emerald-400 font-semibold text-xs flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Sent</span>' 
            : `<span class="text-rose-400 font-semibold text-xs flex items-center gap-1" title="${escapeHtml(l.error_message || '')}"><span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span> Failed</span>`}
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-6 text-rose-400">Failed to fetch logs.</td></tr>';
  }
}

function escapeHtml(str) {
  return String(str).replace(/[&<>'"/]/g, tag => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
    '/': '&#x2F;'
  }[tag] || tag));
}

function toggleHtmlHelp() {
  alert('HTML syntax is directly supported. You can write regular <div>, <p>, <a>, etc.\n\nFor batch campaigns, placeholder tags match your JSON keys, such as {{name}} or {{email}}.');
}

document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
});
