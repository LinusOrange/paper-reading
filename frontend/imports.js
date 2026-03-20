import { apiFetch, endpoints, loadHealthStatus, renderSidebar } from './common.js';

const healthStatus = document.getElementById('health-status');
const importResponse = document.getElementById('import-response');
const pdfResponse = document.getElementById('pdf-response');

async function runImport(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const importType = formData.get('import_type');
  const endpoint = importType === 'url' ? endpoints.importUrl : endpoints.importDoi;
  const payload = {
    direction_hint: [formData.get('direction_hint')],
    auto_analyze: true,
    [importType]: formData.get('value'),
  };
  const result = await apiFetch(endpoint, { method: 'POST', body: JSON.stringify(payload) });
  importResponse.classList.remove('empty-state');
  importResponse.innerHTML = `<h4>导入已创建</h4><p><strong>消息：</strong>${result.message}</p><p><strong>paper_id：</strong>${result.paper_id ?? '-'}</p>`;
}

async function runBibtexImport(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = { bibtex: formData.get('bibtex'), direction_hint: ['airborne-sar'], auto_analyze: true };
  const result = await apiFetch(endpoints.importBibtex, { method: 'POST', body: JSON.stringify(payload) });
  importResponse.classList.remove('empty-state');
  importResponse.innerHTML = `<h4>BibTeX 导入已创建</h4><p><strong>消息：</strong>${result.message}</p><p><strong>paper_id：</strong>${result.paper_id ?? '-'}</p>`;
}

async function runPdfImport(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const result = await apiFetch(endpoints.importPdf, { method: 'POST', body: formData });
  pdfResponse.classList.remove('empty-state');
  pdfResponse.innerHTML = `
    <div class="detail-stack">
      <div class="eyebrow">PDF 上传成功</div>
      <h3>${result.parsed_title}</h3>
      <div class="meta-grid">
        <div class="meta-card"><span>paper_id</span><strong>${result.paper_id}</strong></div>
        <div class="meta-card"><span>文件</span><strong>${result.filename}</strong></div>
        <div class="meta-card"><span>年份</span><strong>${result.parsed_year || '未识别'}</strong></div>
      </div>
      <p class="muted-text">系统已经自动解析元数据并创建了后续任务。</p>
      ${result.pdf_preview_url ? `<p><a class="text-link" href="${result.pdf_preview_url}" target="_blank" rel="noreferrer">立即预览 PDF</a></p>` : ''}
    </div>
  `;
}

async function loadPage() {
  renderSidebar('imports');
  await loadHealthStatus(healthStatus);
}

document.getElementById('import-form').addEventListener('submit', runImport);
document.getElementById('bibtex-form').addEventListener('submit', runBibtexImport);
document.getElementById('pdf-form').addEventListener('submit', runPdfImport);
loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
