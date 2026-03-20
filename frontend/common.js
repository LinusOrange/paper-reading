export const endpoints = {
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
  importPdf: '/api/papers/import/pdf',
  enqueueAnalysis: (paperId) => `/api/analysis/${paperId}/enqueue`,
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

export async function loadHealthStatus(element, retries = 8, delayMs = 2500) {
  let lastError = null;
  for (let attempt = 1; attempt <= retries; attempt += 1) {
    try {
      const health = await apiFetch(endpoints.health);
      element.textContent = `${health.status} · ${health.topic} · ${health.openai_model} · ${health.openai_configured ? 'OpenAI configured' : 'OpenAI missing key'}`;
      element.classList.add('healthy');
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
    <article class="item" data-paper-id="${paper.id}">
      <h4>${paper.title}</h4>
      <small>${paper.year} · ${paper.venue || 'Unknown venue'} · ${paper.status}</small>
      <div class="badges">
        ${paper.tags.map((tag) => `<span class="badge">${tag}</span>`).join('')}
      </div>
    </article>
  `;
}
