export const endpoints = {
  health: '/healthz',
  papers: '/api/papers',
  papersByTag: (tag) => `/api/papers?tag=${encodeURIComponent(tag)}`,
  tasks: '/api/tasks',
  prompts: '/api/config/prompts',
  search: '/api/search/filter',
  qa: '/api/qa/ask',
  collector: '/api/collectors/run',
  importDoi: '/api/papers/import/doi',
  importUrl: '/api/papers/import/url',
  importBibtex: '/api/papers/import/bibtex',
  importPdf: '/api/papers/import/pdf',
  enqueueAnalysis: (paperId) => `/api/analysis/${paperId}/enqueue`,
  tags: '/api/papers/paper-tags',
  createTag: (paperId) => `/api/papers/paper-tags?paper_id=${paperId}`,
  updateTag: (tagId) => `/api/papers/paper-tags/${tagId}`,
  deleteTag: (tagId) => `/api/papers/paper-tags/${tagId}`,
  updatePaper: (paperId) => `/api/papers/${paperId}`,
  deletePaper: (paperId) => `/api/papers/${paperId}`,
};

export async function apiFetch(url, options = {}) {
  const headers = options.body instanceof FormData ? options.headers || {} : { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Request failed: ${response.status} ${errorText}`);
  }
  return response.json();
}

function renderHealthSummary(health) {
  const serviceStatus = health.status === 'ok' ? '后端正常' : health.status;
  const workerStatus = health.task_worker_running ? 'worker 运行中' : (health.task_worker_enabled ? 'worker 未运行' : 'worker 已禁用');
  const openaiStatus = health.analysis_available
    ? `OpenAI 分析已启用 · ${health.openai_base_url} · ${workerStatus}`
    : (health.status_message || '未配置 OpenAI Key（导入/浏览可用，分析/问答暂不可用）');

  return `
    <div class="status-line">
      <span class="status-chip ${health.analysis_available ? 'healthy' : 'warning'}">${serviceStatus}</span>
      <span>${health.topic}</span>
      <span>${health.openai_model}</span>
    </div>
    <div class="status-note">${openaiStatus}</div>
  `;
}

export async function loadHealthStatus(element, retries = 8, delayMs = 2500) {
  let lastError = null;
  for (let attempt = 1; attempt <= retries; attempt += 1) {
    try {
      const health = await apiFetch(endpoints.health);
      element.innerHTML = renderHealthSummary(health);
      element.classList.toggle('healthy', health.analysis_available);
      element.classList.toggle('warning', !health.analysis_available);
      return health;
    } catch (error) {
      lastError = error;
      element.textContent = `后端启动中或不可用（第 ${attempt}/${retries} 次重试）：${error.message}`;
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  throw lastError;
}

export function renderSidebar(activePage) {
  document.querySelectorAll('[data-nav]').forEach((anchor) => {
    if (anchor.dataset.nav === activePage) {
      anchor.classList.add('active-link');
    }
  });
}

export function renderPaperCard(paper) {
  return `
    <article class="item paper-card" data-paper-id="${paper.id}">
      <div class="item-head">
        <div>
          <h4>${paper.title}</h4>
          <small>${paper.year} · ${paper.venue || 'Unknown venue'}</small>
        </div>
        <span class="state-pill ${paper.status}">${paper.status}</span>
      </div>
      <div class="badges">
        ${paper.tags.map((tag) => `<span class="badge">${tag}</span>`).join('')}
        ${paper.pdf_preview_url ? '<span class="badge subtle">PDF 可预览</span>' : ''}
      </div>
    </article>
  `;
}

export function renderTaskState(state) {
  const normalized = String(state || 'queued').toLowerCase();
  const labelMap = {
    queued: '已排队',
    running: '处理中',
    processing: '处理中',
    succeeded: '已完成',
    completed: '已完成',
    failed: '失败',
  };
  const tone = {
    queued: 'queued',
    running: 'running',
    processing: 'running',
    succeeded: 'done',
    completed: 'done',
    failed: 'failed',
  }[normalized] || 'queued';
  return `<span class="state-pill ${tone}">${labelMap[normalized] || normalized}</span>`;
}

export function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : '未知时间';
}
