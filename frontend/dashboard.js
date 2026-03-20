import { apiFetch, endpoints, loadHealthStatus, renderPaperCard, renderSidebar } from './common.js';

const healthStatus = document.getElementById('health-status');
const statsCards = document.getElementById('stats-cards');
const recentPapers = document.getElementById('recent-papers');

function renderStats(papers, tasks) {
  const analyzed = papers.filter((paper) => paper.status === 'analyzed' || paper.status === 'reviewed').length;
  const cards = [
    { label: '论文总数', value: papers.length },
    { label: '已分析/已审核', value: analyzed },
    { label: '任务队列', value: tasks.length },
  ];
  statsCards.innerHTML = cards.map((card) => `<div class="card"><div class="label">${card.label}</div><div class="value">${card.value}</div></div>`).join('');
}

async function loadPage() {
  renderSidebar('dashboard');
  await loadHealthStatus(healthStatus);
  const [papers, tasks] = await Promise.all([apiFetch(endpoints.papers), apiFetch(endpoints.tasks)]);
  renderStats(papers, tasks);
  recentPapers.innerHTML = papers.slice(0, 6).map(renderPaperCard).join('');
}

document.getElementById('refresh-button').addEventListener('click', loadPage);
loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
