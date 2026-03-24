import { apiFetch, endpoints, formatDateTime, loadHealthStatus, renderSidebar, renderTaskState } from './common.js';

const healthStatus = document.getElementById('health-status');
const taskList = document.getElementById('task-list');
const analysisResponse = document.getElementById('analysis-response');
const qaAnswer = document.getElementById('qa-answer');
const taskSummary = document.getElementById('task-summary');
const activeTask = document.getElementById('active-task');
const paperSearchInput = document.getElementById('analysis-paper-search');
const paperSelect = document.getElementById('analysis-paper-select');
const taskTypesSelect = document.getElementById('analysis-task-types');

let allPapers = [];

function summarizeTasks(tasks) {
  const summary = { total: tasks.length, queued: 0, running: 0, completed: 0, failed: 0 };
  tasks.forEach((task) => {
    const state = String(task.state || '').toLowerCase();
    if (state === 'running' || state === 'processing') summary.running += 1;
    else if (state === 'completed' || state === 'succeeded') summary.completed += 1;
    else if (state === 'failed') summary.failed += 1;
    else summary.queued += 1;
  });
  return summary;
}

function renderTaskSummary(tasks) {
  const summary = summarizeTasks(tasks);
  taskSummary.innerHTML = [
    { label: '总任务', value: summary.total },
    { label: '处理中', value: summary.running },
    { label: '已排队', value: summary.queued },
    { label: '已完成/失败', value: summary.completed + summary.failed },
  ].map((card) => `<div class="mini-stat"><span>${card.label}</span><strong>${card.value}</strong></div>`).join('');
}

function renderActiveTask(tasks) {
  const runningTask = tasks.find((task) => ['running', 'processing'].includes(String(task.state).toLowerCase()));
  const latestQueued = tasks.find((task) => String(task.state).toLowerCase() === 'queued');
  const target = runningTask || latestQueued;

  if (!target) {
    activeTask.innerHTML = '<div class="empty-state">当前没有任务。创建分析任务后，这里会展示最新的执行状态。</div>';
    return;
  }

  const stateLabel = runningTask ? '当前正在处理' : '当前暂时没有运行中的任务；最近排队任务如下';
  activeTask.innerHTML = `
    <div class="hero-card soft-accent">
      <div class="eyebrow">${stateLabel}</div>
      <h3>${target.name}</h3>
      <p class="muted-text">${target.paper_title || `paper_id=${target.paper_id ?? '-'}`}</p>
      <div class="inline-meta">
        ${renderTaskState(target.state)}
        <span>${target.provider || 'openai'}</span>
        <span>${formatDateTime(target.updated_at || target.created_at)}</span>
      </div>
    </div>
  `;
}

function renderTasks(tasks) {
  taskList.innerHTML = tasks
    .map(
      (task) => `
        <article class="item task-card">
          <div class="item-head">
            <div>
              <h4>${task.name}</h4>
              <small>${task.paper_title || `paper_id=${task.paper_id ?? '-'}`}</small>
            </div>
            ${renderTaskState(task.state)}
          </div>
          <div class="inline-meta muted-text">
            <span>provider: ${task.provider || 'openai'}</span>
            <span>创建：${formatDateTime(task.created_at)}</span>
            <span>更新：${formatDateTime(task.updated_at || task.created_at)}</span>
          </div>
          ${task.error_message ? `<p class="muted-text">错误：${task.error_message}</p>` : ''}
        </article>
      `,
    )
    .join('');
}

async function loadTasks() {
  const tasks = await apiFetch(endpoints.tasks);
  renderTaskSummary(tasks);
  renderActiveTask(tasks);
  renderTasks(tasks);
}

async function runAnalysisQueue(event) {
  event.preventDefault();
  const paperId = Number(paperSelect.value);
  const taskTypes = Array.from(taskTypesSelect.selectedOptions).map((option) => option.value).filter(Boolean);
  if (!paperId) {
    analysisResponse.classList.remove('empty-state');
    analysisResponse.textContent = '请先选择论文标题。';
    return;
  }
  if (!taskTypes.length) {
    analysisResponse.classList.remove('empty-state');
    analysisResponse.textContent = '请至少选择一个任务。';
    return;
  }
  const result = await apiFetch(endpoints.enqueueAnalysis(paperId), {
    method: 'POST',
    body: JSON.stringify({ task_types: taskTypes, provider: 'openai' }),
  });
  analysisResponse.classList.remove('empty-state');
  analysisResponse.innerHTML = `
    <div class="detail-stack">
      <div class="eyebrow">任务已创建</div>
      <h3>paper_id ${result.paper_id}</h3>
      <p class="muted-text">已将 ${result.task_types.length} 个分析任务加入队列。</p>
      <div class="meta-grid">
        <div class="meta-card"><span>模型</span><strong>${result.model}</strong></div>
        <div class="meta-card"><span>Base URL</span><strong>${result.base_url}</strong></div>
        <div class="meta-card"><span>任务数</span><strong>${result.task_types.length}</strong></div>
      </div>
      <ul>${result.task_types.map((item) => `<li>${item}</li>`).join('')}</ul>
    </div>
  `;
  await loadTasks();
}

function renderPaperSelect(keyword = '') {
  const query = keyword.trim().toLowerCase();
  const papers = query
    ? allPapers.filter((paper) => String(paper.title || '').toLowerCase().includes(query))
    : allPapers;

  paperSelect.innerHTML = papers
    .map((paper) => `<option value="${paper.id}">P-${paper.library_index ?? '-'} · ${paper.title}</option>`)
    .join('');
}

async function loadPapersForAnalysis() {
  allPapers = await apiFetch(endpoints.papers);
  renderPaperSelect();
}

async function runQa(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const result = await apiFetch(endpoints.qa, {
    method: 'POST',
    body: JSON.stringify({ question: formData.get('question'), scope_tags: ['large-squint'] }),
  });
  qaAnswer.classList.remove('empty-state');
  qaAnswer.innerHTML = `
    <div class="detail-stack">
      <div class="eyebrow">问答结果</div>
      <h3>${result.model}</h3>
      <p>${result.answer}</p>
      <p class="muted-text">引用论文编号：${result.citations.join(', ')}</p>
    </div>
  `;
}

async function loadPage() {
  renderSidebar('analysis');
  await loadHealthStatus(healthStatus);
  await loadPapersForAnalysis();
  await loadTasks();
  window.clearInterval(window.__sarTaskPoller);
  window.__sarTaskPoller = window.setInterval(() => {
    loadTasks().catch(() => {});
  }, 10000);
}

document.getElementById('analysis-form').addEventListener('submit', runAnalysisQueue);
paperSearchInput.addEventListener('input', () => {
  renderPaperSelect(paperSearchInput.value);
});
document.getElementById('qa-form').addEventListener('submit', runQa);
loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
