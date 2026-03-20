import { apiFetch, endpoints, loadHealthStatus, renderPaperCard, renderSidebar } from './common.js';

const healthStatus = document.getElementById('health-status');
const statsCards = document.getElementById('stats-cards');
const recentPapers = document.getElementById('recent-papers');
const queueHighlights = document.getElementById('queue-highlights');

function renderStats(papers, tasks) {
  const analyzed = papers.filter((paper) => paper.status === 'analyzed' || paper.status === 'reviewed').length;
  const queued = tasks.filter((task) => String(task.state).toLowerCase() === 'queued').length;
  const running = tasks.filter((task) => ['running', 'processing'].includes(String(task.state).toLowerCase())).length;
  const cards = [
    { label: '论文总数', value: papers.length },
    { label: '已分析/已审核', value: analyzed },
    { label: '进行中任务', value: running },
    { label: '排队中任务', value: queued },
  ];
  statsCards.innerHTML = cards.map((card) => `<div class="card"><div class="label">${card.label}</div><div class="value">${card.value}</div></div>`).join('');
}

function renderQueue(tasks) {
  const latestTasks = tasks.slice(0, 4);
  if (!latestTasks.length) {
    queueHighlights.innerHTML = '<div class="empty-state">当前还没有任务，创建分析任务后这里会显示最新队列。</div>';
    return;
  }
  queueHighlights.innerHTML = latestTasks.map((task) => `
    <article class="item">
      <h4>${task.name}</h4>
      <p>${task.paper_title || `paper_id=${task.paper_id ?? '-'}`}</p>
      <small>${task.state} · ${new Date(task.updated_at || task.created_at).toLocaleString()}</small>
    </article>
  `).join('');
}

async function loadPage() {
  renderSidebar('dashboard');
  await loadHealthStatus(healthStatus);
  const [papers, tasks] = await Promise.all([apiFetch(endpoints.papers), apiFetch(endpoints.tasks)]);
  renderStats(papers, tasks);
  recentPapers.innerHTML = papers.slice(0, 6).map(renderPaperCard).join('');
  renderQueue(tasks);
}

document.getElementById('refresh-button').addEventListener('click', loadPage);
loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
