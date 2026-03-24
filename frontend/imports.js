import { apiFetch, endpoints, loadHealthStatus, renderSidebar } from './common.js';

const healthStatus = document.getElementById('health-status');
const importResponse = document.getElementById('import-response');
const pdfResponse = document.getElementById('pdf-response');

function setResult(container, html, isError = false) {
  container.classList.remove('empty-state');
  container.classList.toggle('error-state', isError);
  container.innerHTML = html;
}

function renderError(container, title, error) {
  const message = error instanceof Error ? error.message : String(error);
  setResult(
    container,
    `<h4>${title}</h4><p><strong>错误信息：</strong>${message}</p><p>请检查后端日志与浏览器 Network 面板。</p>`,
    true,
  );
}

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

  try {
    const result = await apiFetch(endpoint, { method: 'POST', body: JSON.stringify(payload) });
    setResult(importResponse, `<h4>导入已创建</h4><p><strong>消息：</strong>${result.message}</p><p><strong>paper_id：</strong>${result.paper_id ?? '-'}</p>`);
  } catch (error) {
    renderError(importResponse, '导入失败', error);
  }
}

async function runBibtexImport(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = { bibtex: formData.get('bibtex'), direction_hint: ['airborne-sar'], auto_analyze: true };

  try {
    const result = await apiFetch(endpoints.importBibtex, { method: 'POST', body: JSON.stringify(payload) });
    setResult(importResponse, `<h4>BibTeX 导入已创建</h4><p><strong>消息：</strong>${result.message}</p><p><strong>paper_id：</strong>${result.paper_id ?? '-'}</p>`);
  } catch (error) {
    renderError(importResponse, 'BibTeX 导入失败', error);
  }
}

async function runPdfImport(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const fileInput = form.querySelector('input[name="file"]');
  const submitButton = form.querySelector('button[type="submit"]');

  if (!fileInput?.files?.length) {
    setResult(pdfResponse, '<h4>上传失败</h4><p><strong>错误信息：</strong>请先选择一个 PDF 文件再上传。</p>', true);
    return;
  }

  const formData = new FormData(form);
  const originalText = submitButton ? submitButton.textContent : '';
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = '上传中...';
  }

  try {
    const result = await apiFetch(endpoints.importPdf, { method: 'POST', body: formData });
    setResult(
      pdfResponse,
      `
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
    `,
    );
  } catch (error) {
    renderError(pdfResponse, 'PDF 上传失败', error);
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = originalText || '上传 PDF 并自动解析';
    }
  }
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
