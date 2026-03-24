import { apiFetch, endpoints, formatDateTime, loadHealthStatus, renderPaperCard, renderSidebar } from './common.js';

const healthStatus = document.getElementById('health-status');
const paperList = document.getElementById('paper-list');
const paperDetail = document.getElementById('paper-detail');
const pdfPreview = document.getElementById('pdf-preview');
const pdfPreviewEmpty = document.getElementById('pdf-preview-empty');
const paperCreateResult = document.getElementById('paper-create-result');
const tagList = document.getElementById('tag-list');
const tagCreateResult = document.getElementById('tag-create-result');
const tagFilter = document.getElementById('tag-filter');

let currentPapers = [];
let currentTags = [];

const tagLabelMap = {
  'airborne-sar': '机载SAR',
  'high-resolution': '高分辨率',
  'large-squint': '大斜视',
  'high-speed': '高速',
};

function zhTag(tag) {
  return tagLabelMap[tag] || tag;
}

function setResult(el, html, isError = false) {
  el.classList.remove('empty-state');
  el.classList.toggle('error-state', isError);
  el.innerHTML = html;
}

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

async function deletePaper(paperId) {
  if (!window.confirm(`确认删除论文 #${paperId} 吗？`)) return;
  await apiFetch(endpoints.deletePaper(paperId), { method: 'DELETE' });
  await loadData();
}

async function updatePaper(paperId, payload) {
  await apiFetch(endpoints.updatePaper(paperId), {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  await loadData();
}

function showPaperDetail(paper) {
  const summary = paper.summary || {};
  paperDetail.classList.remove('empty-state');
  paperDetail.innerHTML = `
    <div class="detail-stack">
      <div>
        <div class="eyebrow">论文详情</div>
        <h3>${paper.title}</h3>
        <p class="muted-text">${paper.venue || '未知来源'} · ${paper.year} · 更新于 ${formatDateTime(paper.updated_at)}</p>
      </div>
      <div class="meta-grid">
        <div class="meta-card"><span>状态</span><strong>${paper.status}</strong></div>
        <div class="meta-card"><span>DOI</span><strong>${paper.doi || 'N/A'}</strong></div>
        <div class="meta-card"><span>来源链接</span><strong>${paper.source_url || '未提供'}</strong></div>
        <div class="meta-card"><span>PDF</span><strong>${paper.pdf_preview_url ? '可预览（手动打开）' : '暂无'}</strong></div>
      </div>
      <div>
        <h4>标签</h4>
        <div class="badges">${paper.tags.map((tag) => `<span class="badge">${zhTag(tag)}</span>`).join('')}</div>
      </div>
      <div>
        <h4>结构化摘要（中文）</h4>
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
      <div class="inline-meta">
        <button id="paper-delete-btn" type="button">删除论文</button>
        <button id="paper-mark-reviewed-btn" type="button">标记为 reviewed</button>
      </div>
    </div>
  `;

  document.getElementById('paper-delete-btn')?.addEventListener('click', () => deletePaper(paper.id));
  document.getElementById('paper-mark-reviewed-btn')?.addEventListener('click', () => updatePaper(paper.id, { status: 'reviewed' }));

  renderPreviewLauncher(paper);
}

function renderTagFilterOptions(tags) {
  const uniqueTagNames = [...new Set(tags.map((tag) => tag.tag_name))];
  tagFilter.innerHTML = '<option value="">全部标签</option>' + uniqueTagNames.map((tag) => `<option value="${tag}">${zhTag(tag)}</option>`).join('');
}

function bindPaperListEvents(papers) {
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
}

function renderTagList(tags) {
  tagList.innerHTML = tags.map((tag) => `
    <article class="item task-card">
      <div class="item-head">
        <div>
          <h4>${zhTag(tag.tag_name)}</h4>
          <small>tag_id=${tag.id} · paper_id=${tag.paper_id} · ${tag.tag_category}</small>
        </div>
        <div class="inline-meta">
          <button data-tag-edit="${tag.id}" type="button">改名</button>
          <button data-tag-delete="${tag.id}" type="button">删除</button>
        </div>
      </div>
    </article>
  `).join('');

  tagList.querySelectorAll('[data-tag-delete]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const tagId = Number(btn.dataset.tagDelete);
      if (!window.confirm(`确认删除标签 #${tagId} 吗？`)) return;
      await apiFetch(endpoints.deleteTag(tagId), { method: 'DELETE' });
      await loadData();
    });
  });

  tagList.querySelectorAll('[data-tag-edit]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const tagId = Number(btn.dataset.tagEdit);
      const newName = window.prompt('请输入新的标签名称（中文）');
      if (!newName) return;
      await apiFetch(endpoints.updateTag(tagId), {
        method: 'PATCH',
        body: JSON.stringify({ tag_name: newName }),
      });
      await loadData();
    });
  });
}

async function loadData() {
  const selectedTag = tagFilter.value;
  currentPapers = selectedTag ? await apiFetch(endpoints.papersByTag(selectedTag)) : await apiFetch(endpoints.papers);
  currentTags = await apiFetch(endpoints.tags);

  paperList.innerHTML = currentPapers.map((paper) => renderPaperCard({
    ...paper,
    tags: paper.tags.map(zhTag),
  })).join('');

  bindPaperListEvents(currentPapers);
  renderTagFilterOptions(currentTags);
  if (selectedTag) tagFilter.value = selectedTag;
  renderTagList(currentTags);

  if (currentPapers.length) {
    const firstCard = paperList.querySelector('[data-paper-id]');
    if (firstCard) firstCard.classList.add('selected');
    showPaperDetail(currentPapers[0]);
  } else {
    paperDetail.classList.add('empty-state');
    paperDetail.textContent = '当前筛选条件下没有论文。';
    renderPreviewLauncher({});
  }
}

async function createPaper(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = {
    title: String(formData.get('title') || '').trim(),
    year: Number(formData.get('year')),
    venue: String(formData.get('venue') || '').trim() || null,
    doi: String(formData.get('doi') || '').trim() || null,
    source_url: String(formData.get('source_url') || '').trim() || null,
    abstract: String(formData.get('abstract') || '').trim() || null,
    tags: String(formData.get('tags') || '').split(',').map((v) => v.trim()).filter(Boolean),
  };

  try {
    const created = await apiFetch(endpoints.papers, { method: 'POST', body: JSON.stringify(payload) });
    setResult(paperCreateResult, `<h4>创建成功</h4><p>paper_id=${created.id} · ${created.title}</p>`);
    event.currentTarget.reset();
    await loadData();
  } catch (error) {
    setResult(paperCreateResult, `<h4>创建失败</h4><p>${error.message}</p>`, true);
  }
}

async function createTag(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const paperId = Number(formData.get('paper_id'));
  const payload = {
    tag_name: String(formData.get('tag_name') || '').trim(),
    tag_category: String(formData.get('tag_category') || '').trim() || 'topic',
  };

  try {
    const created = await apiFetch(endpoints.createTag(paperId), {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setResult(tagCreateResult, `<h4>标签创建成功</h4><p>tag_id=${created.id} · ${zhTag(created.tag_name)}</p>`);
    event.currentTarget.reset();
    await loadData();
  } catch (error) {
    setResult(tagCreateResult, `<h4>标签创建失败</h4><p>${error.message}</p>`, true);
  }
}

async function loadPage() {
  renderSidebar('papers');
  await loadHealthStatus(healthStatus);
  await loadData();
}

document.getElementById('paper-create-form').addEventListener('submit', createPaper);
document.getElementById('tag-create-form').addEventListener('submit', createTag);
document.getElementById('paper-filter-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  await loadData();
});

loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
