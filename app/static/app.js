/**
 * VolForensics Studio - Frontend Reactive Application (Bản Tiếng Việt)
 */

const state = {
  engine: 'vol3',
  imagePath: '',
  profile: '',
  plugins: { vol3: [], vol2: [], recipes: {} },
  selectedCategory: 'All',
  searchQuery: '',
  selectedPlugin: null,
  pluginOptions: {},
  customArgs: '',
  currentTaskId: null,
  activeTab: 'terminal',
  tasksHistory: [],
  tableData: { columns: [], rows: [] },
  tableFilter: '',
  sortCol: null,
  sortAsc: true,
  treeData: [],
  extractedFiles: [],
  isRunning: false,
  eventSource: null,
  terminalLogs: [],
  autoScrollLogs: true,
  config: {}
};
state.triageTasks = [];
state.stopRequested = false;
state.resultPlugin = '';

async function api(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || data));
  if (data.status === 'error') throw new Error(data.message || 'Thao tác thất bại');
  return data;
}

function setRunning(running) {
  state.isRunning = running;
  document.getElementById('btn-run-plugin').style.display = running ? 'none' : 'inline-flex';
  document.getElementById('btn-kill-plugin').style.display = running ? 'inline-flex' : 'none';
  document.getElementById('btn-quick-triage').disabled = running;
  document.dispatchEvent(new CustomEvent('analysis-state', {detail: {running}}));
}

function resetResults() {
  state.tableData = {columns: [], rows: []};
  state.treeData = [];
  state.extractedFiles = [];
  state.tableFilter = '';
  state.sortCol = null;
  document.getElementById('table-search-input').value = '';
  ['table', 'tree', 'files'].forEach(name => document.getElementById(`tab-badge-${name}`).textContent = '0');
  renderTable(); renderTree(); renderExtractedFiles();
}

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  try {
    state.imagePath = localStorage.getItem('imagePath') || '';
    state.profile = localStorage.getItem('profile') || '';
    document.getElementById('image-path-input').value = state.imagePath;
    document.getElementById('profile-input').value = state.profile;
  } catch (_) {}
  await loadConfig();
  await loadPlugins();
  renderPluginList();
  renderExecutionBar();
  loadTasksHistory();
});

function setupEventListeners() {
  const categories = document.getElementById('category-pills');
  categories.addEventListener('scroll', updateCategoryScrollButtons, {passive: true});
  new ResizeObserver(updateCategoryScrollButtons).observe(categories);
  document.getElementById('btn-category-prev').addEventListener('click', () => scrollCategories(-1));
  document.getElementById('btn-category-next').addEventListener('click', () => scrollCategories(1));
  document.getElementById('btn-engine-vol3').addEventListener('click', () => setEngine('vol3'));
  document.getElementById('btn-engine-vol2').addEventListener('click', () => setEngine('vol2'));

  document.getElementById('btn-browse-image').addEventListener('click', pickMemoryImage);
  document.getElementById('btn-quick-triage').addEventListener('click', startQuickTriage);

  document.getElementById('btn-open-settings').addEventListener('click', openSettingsModal);
  document.getElementById('btn-close-settings').addEventListener('click', closeSettingsModal);
  document.getElementById('btn-save-settings').addEventListener('click', saveSettings);
  document.getElementById('btn-open-dumps-folder').addEventListener('click', openOutputDirectory);

  document.getElementById('plugin-search-input').addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase();
    renderPluginList();
  });

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabName = btn.getAttribute('data-tab');
      switchTab(tabName);
    });
  });

  document.getElementById('btn-clear-terminal').addEventListener('click', () => {
    state.terminalLogs = [];
    document.getElementById('terminal-content').innerHTML = '';
  });
  document.getElementById('btn-copy-terminal').addEventListener('click', () => {
    navigator.clipboard.writeText(state.terminalLogs.join('\n'));
    alert('Đã sao chép toàn bộ log vào clipboard!');
  });

  document.getElementById('table-search-input').addEventListener('input', (e) => {
    state.tableFilter = e.target.value.toLowerCase();
    renderTable();
  });
  document.getElementById('btn-export-csv').addEventListener('click', exportTableCSV);
  document.getElementById('btn-export-json').addEventListener('click', exportTableJSON);

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (!state.isRunning) executePlugin();
    }
  });

  const fileInput = document.getElementById('image-path-input');
  fileInput.addEventListener('input', (e) => {
    state.imagePath = e.target.value.trim().replace(/^"|"$/g, '');
    document.getElementById('image-stats-badge').style.display = 'none';
    updateCommandPreview();
  });
  fileInput.addEventListener('change', async () => {
    try {
      const path = state.imagePath;
      const info = await api(`/api/file-info?path=${encodeURIComponent(path)}`);
      if (path !== state.imagePath) return;
      const badge = document.getElementById('image-stats-badge');
      badge.classList.toggle('error', !info.exists);
      badge.textContent = info.exists ? `File đã sẵn sàng: ${info.size_mb} MB` : 'Không tìm thấy file tại đường dẫn này';
      badge.style.display = 'flex';
    } catch (err) { appendTerminalLine(err.message, 'log-warn'); }
  });
}

async function loadConfig() {
  try {
    const data = await api('/api/config');
    state.config = data;
    
    const vol3Status = document.getElementById('vol3-status-dot');
    if (data.vol3_ready) {
      vol3Status.className = 'engine-status ready';
      vol3Status.textContent = 'Sẵn sàng';
      vol3Status.title = 'Volatility 3 đã sẵn sàng';
    } else {
      vol3Status.className = 'engine-status warning';
      vol3Status.textContent = 'Chưa sẵn sàng';
      vol3Status.title = 'Chưa phát hiện Volatility 3';
    }

    const vol2Status = document.getElementById('vol2-status-dot');
    if (data.vol2_ready) {
      vol2Status.className = 'engine-status ready';
      vol2Status.textContent = 'Sẵn sàng';
      vol2Status.title = 'Volatility 2 đã sẵn sàng';
    } else {
      vol2Status.className = 'engine-status warning';
      vol2Status.textContent = 'Chưa sẵn sàng';
      vol2Status.title = data.vol2_error || 'Volatility 2 chưa sẵn sàng';
    }

    checkVol2Warning();
    updateCommandPreview();
  } catch (err) {
    appendTerminalLine('Lỗi kết nối máy chủ: ' + err.message, 'log-warn');
  }
}

function checkVol2Warning() {
  const warningBox = document.getElementById('vol2-warning-box');
  if (state.engine === 'vol2' && !state.config.vol2_ready) {
    warningBox.style.display = 'block';
  } else {
    warningBox.style.display = 'none';
  }
}

async function loadPlugins() {
  try {
    const data = await api('/api/plugins');
    state.plugins = data;
    
    const list = data[state.engine] || [];
    if (list.length > 0) {
      selectPlugin(list[0]);
    }
    renderCategoryPills();
  } catch (err) {
    console.error('Lỗi khi tải danh sách plugin:', err);
  }
}

function setEngine(engine) {
  state.engine = engine;
  state.selectedCategory = 'All';
  state.searchQuery = '';
  state.customArgs = '';
  document.getElementById('plugin-search-input').value = '';
  document.getElementById('custom-cli-args').value = '';
  document.getElementById('btn-engine-vol3').classList.toggle('active', engine === 'vol3');
  document.getElementById('btn-engine-vol2').classList.toggle('active', engine === 'vol2');
  
  document.getElementById('profile-container').style.display = (engine === 'vol2') ? 'block' : 'none';
  checkVol2Warning();

  const pluginList = state.plugins[engine] || [];
  if (pluginList.length > 0) {
    selectPlugin(pluginList[0]);
  }
  renderCategoryPills();
  renderPluginList();
  updateCommandPreview();
}

function renderCategoryPills() {
  const container = document.getElementById('category-pills');
  container.innerHTML = '';
  
  const currentList = state.plugins[state.engine] || [];
  const categories = ['All', ...new Set(currentList.map(p => p.category))];

  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = `pill-btn ${state.selectedCategory === cat ? 'active' : ''}`;
    btn.textContent = (cat === 'All') ? 'Tất cả' : cat;
    btn.onclick = () => {
      state.selectedCategory = cat;
      renderCategoryPills();
      renderPluginList();
    };
    container.appendChild(btn);
  });
  if (state.selectedCategory !== 'All') {
    container.querySelector('.pill-btn.active')?.scrollIntoView({block:'nearest', inline:'nearest'});
  }
  updateCategoryScrollButtons();
}

function updateCategoryScrollButtons() {
  const container = document.getElementById('category-pills');
  document.getElementById('btn-category-prev').disabled = container.scrollLeft <= 1;
  document.getElementById('btn-category-next').disabled = container.scrollLeft + container.clientWidth >= container.scrollWidth - 1;
}

function scrollCategories(direction) {
  const container = document.getElementById('category-pills');
  container.scrollBy({left: direction * Math.max(180, container.clientWidth * .8),
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
}

function renderPluginList() {
  const container = document.getElementById('plugin-list-container');
  container.innerHTML = '';
  
  const currentList = state.plugins[state.engine] || [];
  const filtered = currentList.filter(p => {
    const matchCat = (state.selectedCategory === 'All') || (p.category === state.selectedCategory);
    const matchSearch = !state.searchQuery || 
      p.name.toLowerCase().includes(state.searchQuery) || 
      p.desc.toLowerCase().includes(state.searchQuery);
    return matchCat && matchSearch;
  });
  document.getElementById('plugin-count-badge').textContent = `${filtered.length}/${currentList.length}`;

  if (filtered.length === 0) {
    container.innerHTML = '<div style="padding:15px; color:var(--text-muted); font-size:12px; text-align:center;">Không tìm thấy plugin phù hợp</div>';
    return;
  }

  filtered.forEach(p => {
    const card = document.createElement('div');
    const isSelected = state.selectedPlugin && state.selectedPlugin.name === p.name;
    card.className = `plugin-card ${isSelected ? 'active' : ''}`;
    card.innerHTML = `
      <div class="plugin-card-header">
        <span class="plugin-title">${escapeHtml(p.name)}</span>
        <span class="category-tag tag-${p.category}">${p.category}</span>
      </div>
      <div class="plugin-card-desc">${escapeHtml(plainLabel(p.desc))}</div>
    `;
    card.onclick = () => selectPlugin(p);
    container.appendChild(card);
  });
}

function selectPlugin(plugin) {
  state.selectedPlugin = plugin;
  state.customArgs = '';
  document.getElementById('custom-cli-args').value = '';
  state.pluginOptions = {};
  if (plugin.options) {
    plugin.options.forEach(opt => {
      if (opt.type === 'boolean') {
        state.pluginOptions[opt.name] = opt.default || false;
      }
    });
  }
  renderPluginList();
  renderExecutionBar();
  updateCommandPreview();
}

function renderExecutionBar() {
  const p = state.selectedPlugin;
  if (!p) return;

  document.getElementById('exec-plugin-name').textContent = p.name;
  document.getElementById('exec-plugin-desc').textContent = plainLabel(p.desc);
  
  const tagEl = document.getElementById('exec-plugin-tag');
  tagEl.textContent = p.category;
  tagEl.className = `category-tag tag-${p.category}`;

  const argsContainer = document.getElementById('plugin-dynamic-args');
  argsContainer.innerHTML = '';

  if (p.options && p.options.length > 0) {
    p.options.forEach(opt => {
      const field = document.createElement('div');
      field.className = 'arg-field';
      
      const label = document.createElement('label');
      label.className = opt.type === 'boolean' ? 'arg-checkbox' : 'arg-label';
      label.htmlFor = `arg-${opt.name}`;
      const input = document.createElement(opt.type === 'choice' ? 'select' : 'input');
      input.id = `arg-${opt.name}`;
      if (opt.type === 'boolean') {
        input.type = 'checkbox';
        input.checked = Boolean(state.pluginOptions[opt.name]);
        const caption = document.createElement('span');
        caption.textContent = opt.label;
        label.append(input, caption);
        field.appendChild(label);
      } else {
        label.textContent = opt.label;
        if (opt.required) label.classList.add('arg-required');
        input.className = 'arg-input';
        if (opt.type === 'choice') {
          const empty = document.createElement('option');
          empty.value = '';
          empty.textContent = 'Chọn giá trị…';
          input.appendChild(empty);
          (opt.choices || []).forEach(value => {
            const option = document.createElement('option');
            option.value = String(value); option.textContent = String(value);
            input.appendChild(option);
          });
        } else {
          input.type = 'text'; input.placeholder = opt.placeholder || '';
        }
        input.value = state.pluginOptions[opt.name] ?? '';
        input.required = Boolean(opt.required);
        field.append(label, input);
      }
      input.addEventListener(opt.type === 'boolean' || opt.type === 'choice' ? 'change' : 'input', () => {
        state.pluginOptions[opt.name] = opt.type === 'boolean' ? input.checked : input.value;
        updateCommandPreview();
      });
      if (opt.help) {
        const help = document.createElement('div');
        help.className = 'arg-help'; help.textContent = opt.help;
        field.appendChild(help);
      }
      argsContainer.appendChild(field);
    });
  }

  document.getElementById('custom-cli-args').oninput = (e) => {
    state.customArgs = e.target.value;
    updateCommandPreview();
  };
}

function updateCommandPreview() {
  const p = state.selectedPlugin;
  if (!p) return;

  let cmd = '';
  if (state.engine === 'vol3') {
    cmd = `"${state.config.vol3_command || 'vol.exe'}" -q -r csv`;
    if (state.imagePath) {
      if (state.imagePath.startsWith('\\\\') || state.imagePath.startsWith('//')) {
        const uri = 'file://' + state.imagePath.replace(/\\/g, '/').replace(/^\/\//, '').split('/').map(encodeURIComponent).join('/');
        cmd += ` --single-location "${uri}"`;
      } else cmd += ` -f "${state.imagePath}"`;
    }
    cmd += ` -o "${state.config.output_dir || './output'}" ${p.name}`;
    for (const [k, v] of Object.entries(state.pluginOptions)) {
      if (v === true) cmd += ` ${k}`;
      else if (v && typeof v === 'string' && v.trim()) cmd += ` ${k} ${v.trim()}`;
    }
  } else {
    cmd = state.config.vol2_custom_exe ? `"${state.config.vol2_custom_exe}"` : `"${state.config.vol2_python || 'python2.exe'}" "${state.config.vol2_script || 'vol.py'}"`;
    if (state.imagePath) cmd += ` -f "${state.imagePath}"`;
    if (state.profile) cmd += ` --profile=${state.profile}`;
    cmd += ` ${p.name}`;
    for (const [k, v] of Object.entries(state.pluginOptions)) {
      if (k === '-D') cmd += ` -D "${v || state.config.output_dir || './output'}"`;
      else if (v === true) cmd += ` ${k}`;
      else if (v && typeof v === 'string' && v.trim()) cmd += ` ${k} ${v.trim()}`;
    }
  }

  if (state.customArgs && state.customArgs.trim()) {
    cmd += ` ${state.customArgs.trim()}`;
  }

  document.getElementById('command-preview-text').textContent = cmd;
  try {
    localStorage.setItem('imagePath', state.imagePath);
    localStorage.setItem('profile', state.profile);
  } catch (_) {}
  clearTimeout(state.previewTimer);
  const version = state.previewVersion = (state.previewVersion || 0) + 1;
  const payload = {engine:state.engine, image_path:state.imagePath, plugin_name:p.name,
    profile:state.profile || null, options:{...state.pluginOptions}, custom_args:state.customArgs || null};
  state.previewTimer = setTimeout(async () => {
    try {
      const result = await api('/api/preview', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      if (state.previewVersion === version) document.getElementById('command-preview-text').textContent = result.command;
    } catch (err) {
      if (state.previewVersion === version) document.getElementById('command-preview-text').textContent = 'Lỗi tham số: ' + err.message;
    }
  }, 150);
}

async function pickMemoryImage() {
  try {
    const data = await api('/api/pick-file', { method: 'POST' });
    if (data.status === 'ok' && data.path) {
      state.imagePath = data.path;
      document.getElementById('image-path-input').value = data.path;
      const statsBadge = document.getElementById('image-stats-badge');
      statsBadge.classList.remove('error');
      statsBadge.textContent = `File đã sẵn sàng: ${data.size_mb} MB (${(data.size_mb / 1024).toFixed(2)} GB)`;
      statsBadge.style.display = 'flex';
      updateCommandPreview();
    }
  } catch (err) {
    alert('Không thể mở cửa sổ chọn file của Windows: ' + err);
  }
}

async function executePlugin() {
  if (state.isRunning) return;
  if (!state.imagePath) {
    alert('Vui lòng chọn hoặc nhập đường dẫn file Memory Dump trước!');
    return;
  }
  if (!state.selectedPlugin) return;

  setRunning(true);
  state.currentTaskId = null;
  state.stopRequested = false;
  resetResults();

  state.terminalLogs = [];
  const term = document.getElementById('terminal-content');
  term.innerHTML = '';
  switchTab('terminal');

  try {
    const payload = {
      engine: state.engine,
      image_path: state.imagePath,
      plugin_name: state.selectedPlugin.name,
      profile: state.profile || null,
      options: state.pluginOptions,
      custom_args: state.customArgs || null
    };

    const data = await api('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (data.task_id) {
      state.currentTaskId = data.task_id;
      if (state.stopRequested) await api(`/api/task/${data.task_id}/kill`, {method: 'POST'});
      await listenToTaskStream(data.task_id);
    }
  } catch (err) {
    appendTerminalLine('[LỖI] ' + err.message, 'log-error');
    alert('Lỗi khởi động tiến trình: ' + err.message);
    setRunning(false);
  }
}

async function listenToTaskStream(taskId, triage = false) {
  if (state.eventSource) state.eventSource.close();
  try {
    await new Promise((resolve, reject) => {
      let seen = 0;
      let polling = false;
      const sse = new EventSource(`/api/task/${taskId}/stream`);
      state.eventSource = sse;
      sse.onmessage = event => {
        const msg = JSON.parse(event.data);
        if (msg.line !== undefined) { appendTerminalLine(msg.line); seen++; }
        if (msg.done) { sse.close(); resolve(msg); }
      };
      sse.onerror = async () => {
        sse.close();
        if (polling) return;
        polling = true;
        appendTerminalLine('Kết nối log bị ngắt, đang lấy trạng thái trực tiếp...', 'log-warn');
        let failures = 0;
        while (true) {
          try {
            const task = await api(`/api/task/${taskId}`);
            failures = 0;
            (task.raw_logs || []).slice(seen).forEach(line => appendTerminalLine(line));
            seen = (task.raw_logs || []).length;
            if (!['RUNNING', 'QUEUED'].includes(task.status)) { resolve(task); break; }
          } catch (err) {
            if (++failures >= 5) { reject(err); break; }
          }
          await new Promise(r => setTimeout(r, 1000));
        }
      };
    });
    await onTaskFinished(taskId, !triage, true);
    await loadTasksHistory();
  } catch (err) {
    appendTerminalLine('Không thể theo dõi tác vụ: ' + err.message + '. Mở Lịch sử để kiểm tra lại.', 'log-warn');
    throw err;
  } finally {
    state.eventSource = null;
    if (!triage) setRunning(false);
  }
}

async function killCurrentTask() {
  state.stopRequested = true;
  const ids = state.triageTasks.length ? state.triageTasks.map(t => t.task_id) : [state.currentTaskId].filter(Boolean);
  try {
    await Promise.all(ids.map(id => api(`/api/task/${id}/kill`, {method: 'POST'})));
    appendTerminalLine('[!] Đã gửi yêu cầu dừng tiến trình và hàng đợi.', 'log-warn');
  } catch (err) { alert('Không thể dừng: ' + err.message); }
}

function classifyLogLine(text) {
  return /(^\s*(ERROR|CRITICAL|FATAL|Traceback)\b|\[LỖI\]|\b(ValueError|TypeError|FileNotFoundError|PermissionError|RuntimeError)\b|error:|unsatisfied requirement|Lỗi|không thể|không tìm thấy)/i.test(text) ? 'log-error' : '';
}

function appendTerminalLine(text, className = '') {
  state.terminalLogs.push(text);
  const term = document.getElementById('terminal-content');
  const div = document.createElement('div');
  div.className = `log-line ${className || classifyLogLine(text)}`;
  div.textContent = text;
  term.appendChild(div);

  if (state.autoScrollLogs) {
    term.scrollTop = term.scrollHeight;
  }
}

function downloadTaskJSON(taskId) {
  const link = document.createElement('a');
  link.href = `/api/task/${encodeURIComponent(taskId)}/export-json`;
  link.download = `memmap_${taskId.slice(0, 8)}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

async function onTaskFinished(taskId, autoSwitch = true, autoDownload = false) {
  const task = await api(`/api/task/${taskId}`);
  clearTimeout(state.previewTimer);
  state.previewVersion = (state.previewVersion || 0) + 1;
  resetResults();
  state.resultPlugin = task.plugin;
  state.tableData = task.table_data || {columns: [], rows: []};
  state.treeData = task.tree_data || [];
  state.extractedFiles = task.extracted_files || [];
  renderTable(); renderTree(); renderExtractedFiles();
  document.getElementById('tab-badge-table').textContent = state.tableData.rows.length;
  document.getElementById('tab-badge-tree').textContent = state.treeData.length;
  document.getElementById('tab-badge-files').textContent = state.extractedFiles.length;
  document.getElementById('command-preview-text').textContent = task.command;
  if (task.engine === 'vol2' && task.plugin === 'imageinfo' && task.status === 'SUCCESS') {
    const match = (task.raw_logs || []).join('\n').match(/Suggested Profile\(s\)\s*:\s*([^,\s]+)/);
    if (match && !state.profile) {
      state.profile = match[1];
      document.getElementById('profile-input').value = state.profile;
      try { localStorage.setItem('profile', state.profile); } catch (_) {}
    }
  }
  appendTerminalLine(`[${task.status}] ${task.plugin} — ${task.duration ?? 0} giây`, task.status === 'SUCCESS' ? 'log-success' : 'log-error');
  if (task.json_export) {
    const exported = task.json_export;
    document.getElementById('files-content-area').insertAdjacentHTML('afterbegin', `
      <div style="padding:16px; border-bottom:1px solid var(--border-color);">
        <strong>Memmap đã xuất ra JSON: ${Number(exported.rows_count).toLocaleString()} dòng</strong>
        <p>Kết quả được lưu trong thư mục lần chạy và không tải vào bảng dữ liệu.</p>
        <button class="btn btn-primary" onclick="downloadTaskJSON('${taskId}')">Tải JSON</button>
        <button class="btn" onclick="openFileInFolder('${escapeHtml(escapeJs(exported.path))}')"> Mở thư mục JSON</button>
      </div>`);
    if (autoSwitch) switchTab('files');
    if (autoDownload) downloadTaskJSON(taskId);
    return task;
  }
  if (autoSwitch) switchTab(state.tableData.rows.length ? 'table' : 'terminal');
  return task;
}

function renderTable() {
  const container = document.getElementById('table-content-area');
  const cols = state.tableData.columns || [];
  let rows = [...(state.tableData.rows || [])];

  if (cols.length === 0 || rows.length === 0) {
    container.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-muted);">Không có bảng. Xem tab Log.</div>';
    document.getElementById('table-row-count').textContent = '0 dòng';
    return;
  }

  if (state.tableFilter) {
    rows = rows.filter(r => r.some(cell => String(cell).toLowerCase().includes(state.tableFilter)));
  }

  if (state.sortCol !== null && state.sortCol < cols.length) {
    rows.sort((a, b) => {
      let va = a[state.sortCol] || '';
      let vb = b[state.sortCol] || '';
      let na = parseFloat(va);
      let nb = parseFloat(vb);
      if (!isNaN(na) && !isNaN(nb)) {
        return state.sortAsc ? (na - nb) : (nb - na);
      }
      return state.sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
  }

  document.getElementById('table-row-count').textContent = `${rows.length} dòng`;

  let html = `<table class="forensic-table"><thead><tr>`;
  cols.forEach((c, idx) => {
    const isSorted = (state.sortCol === idx);
    const arrow = isSorted ? (state.sortAsc ? ' (tăng dần)' : ' (giảm dần)') : '';
    html += `<th onclick="sortTable(${idx})">${escapeHtml(String(c))}${arrow}</th>`;
  });
  html += `</tr></thead><tbody>`;

  rows.forEach(r => {
    html += `<tr>`;
    r.forEach(cell => {
      html += `<td>${escapeHtml(String(cell))}</td>`;
    });
    html += `</tr>`;
  });
  html += `</tbody></table>`;

  container.innerHTML = html;
}

window.sortTable = function(colIdx) {
  if (state.sortCol === colIdx) {
    state.sortAsc = !state.sortAsc;
  } else {
    state.sortCol = colIdx;
    state.sortAsc = true;
  }
  renderTable();
};

function renderTree() {
  const container = document.getElementById('tree-content-area');
  if (!state.treeData || state.treeData.length === 0) {
    container.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-muted);">Cây tiến trình chỉ hiển thị khi chạy plugin pstree.</div>';
    return;
  }

  let html = '<div class="tree-container">';
  state.treeData.forEach(node => {
    const indentPx = (node.level || 0) * 24 + 10;
    html += `
      <div class="tree-node" style="padding-left: ${indentPx}px;">
        <span class="tree-pid-badge">PID ${escapeHtml(String(node.pid))}</span>
        <span style="color:var(--text-muted); font-size:11px;">(PPID ${escapeHtml(String(node.ppid))})</span>
        <span style="font-weight:600; color:var(--text-primary);">${escapeHtml(String(node.name))}</span>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

function renderExtractedFiles() {
  const container = document.getElementById('files-content-area');
  if (!state.extractedFiles || state.extractedFiles.length === 0) {
    container.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-muted);">Chưa có tệp trích xuất.</div>';
    return;
  }

  let html = state.extractedFiles.some(f => f.original_name) ? '<div style="padding:12px; color:var(--accent-amber); font-size:12px;">Tên gốc bên dưới được lấy từ tên bản dump. Volatility thêm .img/.dat/.vacb theo loại cache RAM. File 0 byte không có dữ liệu để mở.</div>' : '';
  html += '<div class="files-grid">';
  state.extractedFiles.forEach(f => {
    const szKb = (f.size / 1024).toFixed(1);
    html += `
      <div class="file-dump-card">
        <div style="font-weight:600; font-family:var(--font-mono); margin-bottom:4px; word-break:break-all;">${escapeHtml(f.original_name || f.name)}</div>
        ${f.original_name ? `<div style="font-size:11px; word-break:break-all; color:var(--text-muted); margin-bottom:6px;">Tên bản dump: ${escapeHtml(f.name)}</div>` : ''}
        <div style="font-size:11px; color:var(--text-muted); margin-bottom:8px;">Kích thước: ${szKb} KB${f.file_type ? '  |  ' + escapeHtml(f.file_type) : ''}${f.cache_type ? '  |  ' + escapeHtml(f.cache_type) : ''}</div>
        ${f.warning ? `<div style="color:var(--accent-amber); font-size:12px; margin-bottom:8px;">${escapeHtml(f.warning)}</div>` : ''}
        ${f.recovered_path ? `<button class="btn btn-sm btn-primary" onclick="openFileInFolder('${escapeHtml(escapeJs(f.recovered_path))}')"> Bản sao giữ tên gốc</button>` : ''}
        <button class="btn btn-sm" onclick="openFileInFolder('${escapeHtml(escapeJs(f.path))}')"> Bản dump từ RAM</button>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

async function loadTasksHistory() {
  try {
    const res = await fetch('/api/tasks');
    const tasks = await res.json();
    state.tasksHistory = tasks;
    document.getElementById('tab-badge-history').textContent = tasks.length;
    renderTasksHistory();
  } catch (err) {
    console.error('Lỗi tải lịch sử:', err);
  }
}

function renderTasksHistory() {
  const container = document.getElementById('history-content-area');
  if (!state.tasksHistory || state.tasksHistory.length === 0) {
    container.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-muted);">Chưa có lịch sử.</div>';
    return;
  }

  let html = '<div style="padding:16px; display:flex; flex-direction:column; gap:8px;">';
  state.tasksHistory.forEach(t => {
    const timeStr = new Date(t.start_time * 1000).toLocaleTimeString();
    html += `
      <div class="plugin-card" style="display:flex; justify-content:space-between; align-items:center;" onclick="loadPastTask('${t.id}')">
        <div>
          <span style="font-weight:700; color:var(--text-primary); font-family:var(--font-mono);">${t.plugin}</span>
          <span class="category-tag" style="margin-left:8px;">${t.engine.toUpperCase()}</span>
          <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">${escapeHtml(t.image_path)}  |  ${t.rows_count} dòng  |  Thời gian: ${t.duration || 0}s</div>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
          <span class="brand-badge task-status ${['FAILED','ERROR','CANCELLED','KILLED'].includes(t.status) ? 'error' : t.status === 'RUNNING' ? 'running' : 'success'}">${t.status}</span>
          <span style="font-size:11px; color:var(--text-muted);">${timeStr}</span>
        </div>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

async function loadPastTask(taskId) {
  if (state.isRunning) return alert('Hãy đợi hoặc dừng tác vụ hiện tại trước khi mở lịch sử.');
  try {
    const task = await api(`/api/task/${taskId}`);
    state.imagePath = task.image_path;
    state.profile = task.profile || '';
    document.getElementById('image-path-input').value = state.imagePath;
    document.getElementById('profile-input').value = state.profile;
    setEngine(task.engine);
    const plugin = (state.plugins[task.engine] || []).find(item => item.name === task.plugin);
    if (plugin) selectPlugin(plugin);
    state.currentTaskId = taskId;
    state.terminalLogs = [];
    document.getElementById('terminal-content').innerHTML = '';
    (task.raw_logs || []).forEach(line => appendTerminalLine(line));
    await onTaskFinished(taskId);
    if (['RUNNING', 'QUEUED'].includes(task.status)) {
      setRunning(true);
      state.terminalLogs = [];
      document.getElementById('terminal-content').innerHTML = '';
      switchTab('terminal');
      await listenToTaskStream(taskId);
    }
  } catch (err) { alert('Không tải được tác vụ: ' + err.message); }
}

function switchTab(tabName) {
  state.activeTab = tabName;
  if (tabName === 'history') loadTasksHistory();
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
  });
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.remove('active');
  });
  document.getElementById(`tab-pane-${tabName}`).classList.add('active');
  document.dispatchEvent(new CustomEvent('analysis-view', {detail: {tab: tabName}}));
}

async function startQuickTriage() {
  if (state.isRunning) return;
  if (!state.imagePath) return alert('Vui lòng chọn file memory trước!');
  const payload = {engine: state.engine, image_path: state.imagePath, profile: state.profile || null};
  setRunning(true);
  state.stopRequested = false;
  state.currentTaskId = null;
  state.triageTasks = [];
  resetResults();
  state.terminalLogs = [];
  document.getElementById('terminal-content').innerHTML = '';
  switchTab('terminal');
  try {
    const data = await api('/api/run-triage', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    state.triageTasks = data.tasks;
    if (state.stopRequested) await killCurrentTask();
    appendTerminalLine('=== BẮT ĐẦU TRIAGE ===', 'log-success');
    for (const item of data.tasks) {
      if (state.stopRequested) break;
      state.currentTaskId = item.task_id;
      appendTerminalLine(`>>> ${item.label}: ${item.plugin}`, 'log-success');
      await listenToTaskStream(item.task_id, true);
    }
    appendTerminalLine(state.stopRequested ? '=== ĐÃ DỪNG TRIAGE ===' : '=== TRIAGE HOÀN TẤT — Xem từng kết quả trong Lịch sử ===');
  } catch (err) {
    if (state.triageTasks.length) await killCurrentTask();
    alert('Triage: ' + err.message);
  } finally {
    state.triageTasks = [];
    setRunning(false);
    await loadTasksHistory();
  }
}

function downloadBlob(content, type, extension) {
  const url = URL.createObjectURL(new Blob([content], {type}));
  const link = document.createElement('a');
  link.href = url;
  link.download = `${state.resultPlugin || 'vol_export'}.${extension}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportTableCSV() {
  const {columns, rows} = state.tableData;
  if (!columns.length) return alert('Không có dữ liệu bảng để xuất.');
  const cell = value => '"' + String(value ?? '').replace(/"/g, '""') + '"';
  const csv = [columns, ...rows].map(row => row.map(cell).join(',')).join('\r\n');
  downloadBlob('\ufeff' + csv, 'text/csv;charset=utf-8', 'csv');
}

function exportTableJSON() {
  const {columns, rows} = state.tableData;
  if (!columns.length) return alert('Không có dữ liệu bảng để xuất.');
  const objects = rows.map(row => Object.fromEntries(columns.map((col, i) => [col, row[i] ?? ''])));
  downloadBlob(JSON.stringify(objects, null, 2), 'application/json', 'json');
}

function openSettingsModal() {
  const cfg = state.config;
  document.getElementById('cfg-vol3-cmd').value = cfg.vol3_command || 'vol.exe';
  document.getElementById('cfg-vol2-py').value = cfg.vol2_python || 'python2.exe';
  document.getElementById('cfg-vol2-script').value = cfg.vol2_script || '';
  document.getElementById('cfg-vol2-exe').value = cfg.vol2_custom_exe || '';
  document.getElementById('cfg-output-dir').value = cfg.output_dir || '';
  document.getElementById('settings-modal').classList.add('open');
}

function closeSettingsModal() {
  document.getElementById('settings-modal').classList.remove('open');
}

async function saveSettings() {
  const update = {
    vol3_command: document.getElementById('cfg-vol3-cmd').value,
    vol2_python: document.getElementById('cfg-vol2-py').value,
    vol2_script: document.getElementById('cfg-vol2-script').value,
    vol2_custom_exe: document.getElementById('cfg-vol2-exe').value,
    output_dir: document.getElementById('cfg-output-dir').value
  };
  try {
    await api('/api/config', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(update)});
    await loadConfig();
    closeSettingsModal();
    alert('Đã lưu cấu hình.');
  } catch (err) { alert('Không lưu được cấu hình: ' + err.message); }
}

async function openOutputDirectory() {
  try {
    const dir = state.config.output_dir || './output';
    await api(`/api/open-folder?path=${encodeURIComponent(dir)}`);
  } catch (err) {
    alert('Không mở được thư mục: ' + err.message);
  }
}

window.openFileInFolder = async function(filePath) {
  try {
    const dir = filePath.substring(0, Math.max(filePath.lastIndexOf('/'), filePath.lastIndexOf('\\')));
    await api(`/api/open-folder?path=${encodeURIComponent(dir)}`);
  } catch (err) {
    alert('Không mở được thư mục: ' + err.message);
  }
};

function plainLabel(text) {
  return String(text).replace(/[\p{Extended_Pictographic}\uFE0F]/gu, '').replace(/\[TƯƠNG ĐƯƠNG IMAGEINFO\]\s*/g, '').replace(/[➔→]/g, ' tới ').trim();
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function escapeJs(str) {
  return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}
