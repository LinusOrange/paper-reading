import { apiFetch, endpoints, loadHealthStatus, renderPaperCard, renderSidebar } from './common.js';

const healthStatus = document.getElementById('health-status');
const paperList = document.getElementById('paper-list');
const paperDetail = document.getElementById('paper-detail');

function showPaperDetail(paper) {
  const summary = paper.summary || {};
  paperDetail.classList.remove('empty-state');
  paperDetail.innerHTML = `
    <h4>${paper.title}</h4>
    <p><strong>年份：</strong>${paper.year}</p>
    <p><strong>来源：</strong>${paper.venue || 'Unknown'}</p>
    <p><strong>DOI：</strong>${paper.doi || 'N/A'}</p>
    <p><strong>PDF：</strong>${paper.pdf_object_key || '暂无'}</p>
    <p><strong>场景：</strong>${summary.scenario || '未分析'}</p>
    <p><strong>问题：</strong>${summary.problem || '暂无'}</p>
    <p><strong>方法：</strong>${summary.method || '暂无'}</p>
    <ul>${(summary.contributions || []).map((item) => `<li>${item}</li>`).join('')}</ul>
  `;
}

async function loadPage() {
  renderSidebar('papers');
  await loadHealthStatus(healthStatus);
  const papers = await apiFetch(endpoints.papers);
  paperList.innerHTML = papers.map(renderPaperCard).join('');
  paperList.querySelectorAll('[data-paper-id]').forEach((element) => {
    element.addEventListener('click', () => {
      const paper = papers.find((item) => item.id === Number(element.dataset.paperId));
      if (paper) showPaperDetail(paper);
    });
  });
  if (papers.length) showPaperDetail(papers[0]);
}

loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
