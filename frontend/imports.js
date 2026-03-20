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
    <h4>PDF 上传成功</h4>
    <p><strong>paper_id：</strong>${result.paper_id}</p>
    <p><strong>文件：</strong>${result.filename}</p>
    <p><strong>自动标题：</strong>${result.parsed_title}</p>
    <p><strong>自动年份：</strong>${result.parsed_year || '未识别'}</p>
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
