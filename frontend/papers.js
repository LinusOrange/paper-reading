import { apiFetch, endpoints, formatDateTime, loadHealthStatus, renderPaperCard, renderSidebar } from './common.js';

const healthStatus = document.getElementById('health-status');
const paperList = document.getElementById('paper-list');
const paperDetail = document.getElementById('paper-detail');
const pdfPreview = document.getElementById('pdf-preview');
const pdfPreviewEmpty = document.getElementById('pdf-preview-empty');

function renderSummaryList(items, fallbackText = '暂无') {
  if (!items?.length) {
    return `<li>${fallbackText}</li>`;
  }
  return items.map((item) => `<li>${item}</li>`).join('');
}

function mountPreviewFrame(paper) {
  pdfPreviewEmpty.hidden = true;
  pdfPreview.innerHTML = `
    <div class="pdf-preview-toolbar">
      <span>在线预览</span>
      <a class="text-link" href="${paper.pdf_preview_url}" target="_blank" rel="noreferrer">新窗口打开</a>
    </div>
    <iframe src="${paper.pdf_preview_url}#view=FitH" title="${paper.title} PDF 预览"></iframe>
  `;
}

function renderPreviewLauncher(paper) {
  if (!paper.pdf_preview_url) {
    pdfPreview.innerHTML = '';
    pdfPreviewEmpty.hidden = false;
    pdfPreviewEmpty.textContent = '当前论文还没有可预览的 PDF。你可以先在“文献导入”页面上传 PDF。';
    return;
  }

  pdfPreview.innerHTML = '';
  pdfPreviewEmpty.hidden = false;
  pdfPreviewEmpty.innerHTML = `
    <div>
      <p>该论文支持 PDF 预览。</p>
      <button id="preview-start-button" type="button">开始预览</button>
      <p class="muted-text" style="margin-top:10px;">为避免进入论文库时自动触发下载，预览改为手动触发。</p>
    </div>
  `;

  const startButton = document.getElementById('preview-start-button');
  startButton?.addEventListener('click', () => {
    mountPreviewFrame(paper);
  });
}

function showPaperDetail(paper) {
  const summary = paper.summary || {};
  paperDetail.classList.remove('empty-state');
  paperDetail.innerHTML = `
    <div class="detail-stack">
      <div>
        <div class="eyebrow">论文详情</div>
        <h3>${paper.title}</h3>
        <p class="muted-text">${paper.venue || 'Unknown venue'} · ${paper.year} · 更新于 ${formatDateTime(paper.updated_at)}</p>
      </div>
      <div class="meta-grid">
        <div class="meta-card"><span>状态</span><strong>${paper.status}</strong></div>
        <div class="meta-card"><span>DOI</span><strong>${paper.doi || 'N/A'}</strong></div>
        <div class="meta-card"><span>来源链接</span><strong>${paper.source_url || '未提供'}</strong></div>
        <div class="meta-card"><span>PDF</span><strong>${paper.pdf_preview_url ? '可预览（手动打开）' : '暂无'}</strong></div>
      </div>
      <div>
        <h4>结构化摘要</h4>
        <p><strong>场景：</strong>${summary.scenario || '未分析'}</p>
        <p><strong>问题：</strong>${summary.problem || '暂无'}</p>
        <p><strong>方法：</strong>${summary.method || '暂无'}</p>
      </div>
      <div>
        <h4>贡献点</h4>
        <ul>${renderSummaryList(summary.contributions, '尚未生成贡献点')}</ul>
      </div>
      <div>
        <h4>数据与指标</h4>
        <ul>${renderSummaryList([...(summary.datasets_or_simulation || []), ...(summary.metrics || [])], '暂无结构化数据')}</ul>
      </div>
    </div>
  `;
  renderPreviewLauncher(paper);
}

async function loadPage() {
  renderSidebar('papers');
  await loadHealthStatus(healthStatus);
  const papers = await apiFetch(endpoints.papers);
  paperList.innerHTML = papers.map(renderPaperCard).join('');
  paperList.querySelectorAll('[data-paper-id]').forEach((element) => {
    element.addEventListener('click', () => {
      const paper = papers.find((item) => item.id === Number(element.dataset.paperId));
      if (paper) {
        paperList.querySelectorAll('.paper-card').forEach((card) => card.classList.remove('selected'));
        element.classList.add('selected');
        showPaperDetail(paper);
      }
    });
  });
  if (papers.length) {
    const firstCard = paperList.querySelector('[data-paper-id]');
    if (firstCard) firstCard.classList.add('selected');
    showPaperDetail(papers[0]);
  }
}

loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
