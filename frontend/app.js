const endpoints = {
  health: '/healthz',
  papers: '/api/papers',
  tasks: '/api/tasks',
  prompts: '/api/config/prompts',
  search: '/api/search/filter',
  qa: '/api/qa/ask',
  collector: '/api/collectors/run',
  importDoi: '/api/papers/import/doi',
  importUrl: '/api/papers/import/url',
  importBibtex: '/api/papers/import/bibtex',
};

const state = {
  papers: [],
  tasks: [],
  prompts: [],
};

const healthStatus = document.getElementById('health-status');
const statsCards = document.getElementById('stats-cards');
const paperList = document.getElementById('paper-list');
const paperDetail = document.getElementById('paper-detail');
const taskList = document.getElementById('task-list');
const promptList = document.getElementById('prompt-list');
const searchResults = document.getElementById('search-results');
const qaAnswer = document.getElementById('qa-answer');
const collectorResponse = document.getElementById('collector-response');
const importResponse = document.getElementById('import-response');

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function renderStats() {
  const analyzed = state.papers.filter((paper) => paper.status === 'analyzed' || paper.status === 'reviewed').length;
  const highSpeed = state.papers.filter((paper) => paper.tags.includes('high-speed')).length;
  const largeSquint = state.papers.filter((paper) => paper.tags.includes('large-squint')).length;

  const cards = [
    { label: '论文总数', value: state.papers.length },
    { label: '已分析/已审核', value: analyzed },
    { label: '高速场景', value: highSpeed },
    { label: '大斜视场景', value: largeSquint },
    { label: '任务队列', value: state.tasks.length },
  ];

  statsCards.innerHTML = cards
    .map((card) => `<div class="card"><div class="label">${card.label}</div><div class="value">${card.value}</div></div>`)
    .join('');
}

function renderPapers() {
  paperList.innerHTML = state.papers
    .map(
      (paper) => `
        <article class="item" data-paper-id="${paper.id}">
          <h4>${paper.title}</h4>
          <small>${paper.year} · ${paper.venue || 'Unknown venue'} · ${paper.status}</small>
          <div class="badges">
            ${paper.tags.map((tag) => `<span class="badge">${tag}</span>`).join('')}
          </div>
        </article>
      `,
    )
    .join('');

  paperList.querySelectorAll('[data-paper-id]').forEach((element) => {
    element.addEventListener('click', () => showPaperDetail(Number(element.dataset.paperId)));
  });
}

function showPaperDetail(paperId) {
  const paper = state.papers.find((item) => item.id === paperId);
  if (!paper) return;

  const summary = paper.summary || {};
  paperDetail.classList.remove('empty-state');
  paperDetail.innerHTML = `
    <h4>${paper.title}</h4>
    <p><strong>年份：</strong>${paper.year} &nbsp;&nbsp; <strong>来源：</strong>${paper.venue || 'Unknown'}</p>
    <p><strong>DOI：</strong>${paper.doi || 'N/A'}</p>
    <p><strong>场景：</strong>${summary.scenario || '未分析'}</p>
    <p><strong>问题：</strong>${summary.problem || '暂无'}</p>
    <p><strong>方法：</strong>${summary.method || '暂无'}</p>
    <p><strong>速度相关：</strong>${summary.speed_related_issue || '暂无'}</p>
    <p><strong>斜视相关：</strong>${summary.squint_related_issue || '暂无'}</p>
    <p><strong>贡献：</strong></p>
    <ul>${(summary.contributions || []).map((item) => `<li>${item}</li>`).join('')}</ul>
  `;
}

function renderTasks() {
  taskList.innerHTML = state.tasks
    .map(
      (task) => `
        <article class="item">
          <h4>${task.name}</h4>
          <p>状态：${task.state}</p>
          <small>paper_id=${task.paper_id ?? '-'} · ${new Date(task.created_at).toLocaleString()}</small>
        </article>
      `,
    )
    .join('');
}

function renderPrompts() {
  promptList.innerHTML = state.prompts
    .map(
      (prompt) => `
        <article class="item">
          <h4>${prompt.name}</h4>
          <p>${prompt.description}</p>
          <small>版本：${prompt.version}</small>
        </article>
      `,
    )
    .join('');
}

async function loadDashboard() {
  const [health, papers, tasks, prompts] = await Promise.all([
    apiFetch(endpoints.health),
    apiFetch(endpoints.papers),
    apiFetch(endpoints.tasks),
    apiFetch(endpoints.prompts),
  ]);

  healthStatus.textContent = `${health.status} · ${health.topic}`;
  healthStatus.classList.add('healthy');

  state.papers = papers;
  state.tasks = tasks;
  state.prompts = prompts;

  renderStats();
  renderPapers();
  renderTasks();
  renderPrompts();
  if (papers.length > 0) {
    showPaperDetail(papers[0].id);
  }
}

async function runSearch(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = {
    query: formData.get('query'),
    methods: [formData.get('method')].filter(Boolean),
    tags: [formData.get('tag')].filter(Boolean),
  };
  const papers = await apiFetch(endpoints.search, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  searchResults.innerHTML = papers
    .map(
      (paper) => `
        <article class="item">
          <h4>${paper.title}</h4>
          <small>${paper.year} · ${paper.status}</small>
          <div class="badges">${paper.tags.map((tag) => `<span class="badge">${tag}</span>`).join('')}</div>
        </article>
      `,
    )
    .join('');
}

async function runQa(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = { question: formData.get('question'), scope_tags: ['large-squint'] };
  const result = await apiFetch(endpoints.qa, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  qaAnswer.classList.remove('empty-state');
  qaAnswer.innerHTML = `
    <h4>问答结果</h4>
    <p><strong>问题：</strong>${result.question}</p>
    <p><strong>答案：</strong>${result.answer}</p>
    <p><strong>引用编号：</strong>${result.citations.join(', ')}</p>
  `;
}

async function runCollector(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = {
    query_group: formData.get('query_group'),
    limit: Number(formData.get('limit')),
  };
  const result = await apiFetch(endpoints.collector, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  collectorResponse.classList.remove('empty-state');
  collectorResponse.innerHTML = `
    <h4>采集器已启动</h4>
    <p><strong>查询分组：</strong>${result.query_group}</p>
    <p><strong>限制：</strong>${result.limit}</p>
    <p><strong>消息：</strong>${result.message}</p>
  `;
}

async function runImport(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const directionHint = formData.get('direction_hint');
  const value = formData.get('value');
  const importType = formData.get('import_type');
  const endpoint = importType === 'url' ? endpoints.importUrl : endpoints.importDoi;
  const payload = {
    direction_hint: [directionHint],
    auto_analyze: true,
    [importType]: value,
  };
  const result = await apiFetch(endpoint, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  importResponse.classList.remove('empty-state');
  importResponse.innerHTML = `
    <h4>导入已创建</h4>
    <p><strong>消息：</strong>${result.message}</p>
    <p><strong>paper_id：</strong>${result.paper_id ?? '-'}</p>
  `;
  await loadDashboard();
}

async function runBibtexImport(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = {
    bibtex: formData.get('bibtex'),
    direction_hint: ['airborne-sar'],
    auto_analyze: true,
  };
  const result = await apiFetch(endpoints.importBibtex, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  importResponse.classList.remove('empty-state');
  importResponse.innerHTML = `
    <h4>BibTeX 导入已创建</h4>
    <p><strong>消息：</strong>${result.message}</p>
    <p><strong>paper_id：</strong>${result.paper_id ?? '-'}</p>
    <p><strong>长度：</strong>${result.size}</p>
  `;
  await loadDashboard();
}

async function init() {
  document.getElementById('refresh-button').addEventListener('click', loadDashboard);
  document.getElementById('search-form').addEventListener('submit', runSearch);
  document.getElementById('qa-form').addEventListener('submit', runQa);
  document.getElementById('collector-form').addEventListener('submit', runCollector);
  document.getElementById('import-form').addEventListener('submit', runImport);
  document.getElementById('bibtex-form').addEventListener('submit', runBibtexImport);

  try {
    await loadDashboard();
  } catch (error) {
    healthStatus.textContent = `服务不可用：${error.message}`;
    paperDetail.textContent = '请先启动 docker compose 服务，然后刷新页面。';
  }
}

init();
