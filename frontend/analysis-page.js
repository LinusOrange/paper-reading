import { apiFetch, endpoints, loadHealthStatus, renderSidebar } from './common.js';

const healthStatus = document.getElementById('health-status');
const taskList = document.getElementById('task-list');
const analysisResponse = document.getElementById('analysis-response');
const qaAnswer = document.getElementById('qa-answer');

function renderTasks(tasks) {
  taskList.innerHTML = tasks
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

async function loadTasks() {
  const tasks = await apiFetch(endpoints.tasks);
  renderTasks(tasks);
}

async function runAnalysisQueue(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const paperId = formData.get('paper_id');
  const taskTypes = String(formData.get('task_types')).split(',').map((item) => item.trim()).filter(Boolean);
  const result = await apiFetch(endpoints.enqueueAnalysis(paperId), {
    method: 'POST',
    body: JSON.stringify({ task_types: taskTypes, provider: 'openai' }),
  });
  analysisResponse.classList.remove('empty-state');
  analysisResponse.innerHTML = `<h4>分析任务已排队</h4><p><strong>paper_id：</strong>${result.paper_id}</p><p><strong>model：</strong>${result.model}</p><p><strong>base_url：</strong>${result.base_url}</p>`;
  await loadTasks();
}

async function runQa(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const result = await apiFetch(endpoints.qa, {
    method: 'POST',
    body: JSON.stringify({ question: formData.get('question'), scope_tags: ['large-squint'] }),
  });
  qaAnswer.classList.remove('empty-state');
  qaAnswer.innerHTML = `<h4>问答结果</h4><p><strong>答案：</strong>${result.answer}</p><p><strong>模型：</strong>${result.model}</p><p><strong>引用编号：</strong>${result.citations.join(', ')}</p>`;
}

async function loadPage() {
  renderSidebar('analysis');
  await loadHealthStatus(healthStatus);
  await loadTasks();
}

document.getElementById('analysis-form').addEventListener('submit', runAnalysisQueue);
document.getElementById('qa-form').addEventListener('submit', runQa);
loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
