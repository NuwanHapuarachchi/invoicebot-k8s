const form = document.getElementById('upload-form');
const previewEl = document.getElementById('preview');
const messagesEl = document.getElementById('messages');
const proceedBtn = document.getElementById('proceed-btn');
const importResultEl = document.getElementById('import-result');

function showMessage(msg, isError=false) {
  messagesEl.textContent = msg;
  messagesEl.className = isError ? 'error' : 'info';
}

function renderTable(headers, rows) {
  previewEl.innerHTML = '';
  const table = document.createElement('table');
  table.className = 'preview-table';

  if (headers && headers.length) {
    const thead = document.createElement('thead');
    const tr = document.createElement('tr');
    headers.forEach(h => {
      const th = document.createElement('th');
      th.textContent = h;
      tr.appendChild(th);
    });
    thead.appendChild(tr);
    table.appendChild(thead);
  }

  const tbody = document.createElement('tbody');
  rows.forEach(row => {
    const tr = document.createElement('tr');
    row.forEach(cell => {
      const td = document.createElement('td');
      td.textContent = cell;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  previewEl.appendChild(table);
}

form.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const fileInput = document.getElementById('file');
  const hasHeader = document.getElementById('hasHeader').checked;

  if (!fileInput.files || fileInput.files.length === 0) {
    showMessage('Please select a CSV file to upload.', true);
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);
  formData.append('has_header', hasHeader ? '1' : '0');

  showMessage('Uploading & parsing...', false);

  try {
    const resp = await fetch('/api/preview_csv', {
      method: 'POST',
      body: formData
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: 'Unknown error' }));
      showMessage(err.error || 'Upload failed', true);
      proceedBtn.disabled = true; // Disable proceed button on error
      return;
    }

    const data = await resp.json();
    showMessage(`Preview: showing ${data.rows.length} row(s)`);
    renderTable(data.headers || [], data.rows);
    
    // Enable the proceed button after successful preview
    proceedBtn.disabled = false;
  } catch (err) {
    console.error(err);
    showMessage('Network or server error while uploading file', true);
    proceedBtn.disabled = true; // Disable proceed button on error
  }
});

// Enable proceed button after preview; send original file to import endpoint
proceedBtn.addEventListener('click', async () => {
  const fileInput = document.getElementById('file');
  const hasHeader = document.getElementById('hasHeader').checked;
  if (!fileInput.files || fileInput.files.length === 0) {
    showMessage('Please select a CSV file to upload before proceeding.', true);
    return;
  }

  proceedBtn.disabled = true;
  showMessage('Importing CSV to server...', false);

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('has_header', hasHeader ? '1' : '0');

  try {
    const resp = await fetch('/api/import_csv', {
      method: 'POST',
      body: formData
    });

    const data = await resp.json();
    if (!resp.ok) {
      showMessage(data.error || 'Import failed', true);
      proceedBtn.disabled = false;
      return;
    }

    showMessage(`Import complete: inserted=${data.inserted} skipped=${data.skipped}`);
    importResultEl.textContent = `Inserted: ${data.inserted}, Skipped (duplicates): ${data.skipped}`;
    if (data.s3 && data.s3.url) {
      const a = document.createElement('a');
      a.href = data.s3.url;
      a.textContent = 'View archived CSV in S3 (expires in 1 hour)';
      a.target = '_blank';
      importResultEl.appendChild(document.createElement('br'));
      importResultEl.appendChild(a);
    }
    if (data.s3_error) {
      const err = document.createElement('div');
      err.className = 'error';
      err.textContent = `S3 upload error: ${data.s3_error}`;
      importResultEl.appendChild(document.createElement('br'));
      importResultEl.appendChild(err);
    }
  } catch (err) {
    console.error(err);
    showMessage('Network or server error while importing file', true);
  } finally {
    proceedBtn.disabled = false;
  }
});
