import { apiFetch, endpoints, loadHealthStatus, renderSidebar } from './common.js';

const DEFAULT_TEMPLATE = `你是一名熟悉合成孔径雷达（SAR）成像、机载SAR系统、频域与时域成像算法、Chirp Scaling / Nonlinear Chirp Scaling（NCS）算法、运动补偿与复杂成像几何处理的科研助手。

请围绕研究主题完成系统检索：机载SAR成像算法、复杂几何成像、高斜视/滑动聚束、NCS/CSA改进、运动补偿与自聚焦。

执行要求：
1) 输出分层结果：candidate -> priority -> core；
2) 输出证据提取表：题目、作者、年份、venue、数据库来源、DOI/arXiv、PDF可得性、核心算法类别、创新点、局限性、推荐等级；
3) 不得虚构元数据，无法确认的信息标注 UNVERIFIED；
4) 优先 2020-至今，重点 2024-2026。`;

const healthStatus = document.getElementById('health-status');
const workflowStatus = document.getElementById('workflow-status');
const optimizedPrompt = document.getElementById('optimized-prompt');
const literatureResult = document.getElementById('literature-result');
const promptTemplate = document.getElementById('prompt-template');

promptTemplate.value = DEFAULT_TEMPLATE;

function showBlock(el, title, body, isError = false) {
  el.classList.remove('empty-state');
  el.classList.toggle('error-state', isError);
  el.innerHTML = `
    <div class="detail-stack">
      <h4>${title}</h4>
      <pre style="white-space:pre-wrap;word-break:break-word;margin:0;">${body}</pre>
    </div>
  `;
}

async function runWorkflow(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = {
    user_requirement: String(formData.get('user_requirement') || '').trim(),
    prompt_template: String(formData.get('prompt_template') || '').trim() || null,
    use_web_search: document.getElementById('use-web-search').checked,
  };

  showBlock(workflowStatus, '执行中', '正在调用 Codex：1) 生成新提示词 2) 文献联网检索...');

  const workflowEndpoint = endpoints.literatureWorkflow || '/api/analysis/literature-workflow';
  if (!workflowEndpoint) {
    showBlock(workflowStatus, '执行失败', '文献工作流接口未配置（endpoints.literatureWorkflow）。', true);
    return;
  }

  try {
    const result = await apiFetch(workflowEndpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    showBlock(
      workflowStatus,
      '执行完成',
      `模型：${result.model}\nWeb Search：${result.used_web_search ? '启用' : '关闭'}`,
    );
    showBlock(optimizedPrompt, '优化后的提示词', result.optimized_prompt || '未生成。');
    showBlock(literatureResult, '检索结果', result.search_result || '未返回内容。');
  } catch (error) {
    showBlock(workflowStatus, '执行失败', error.message, true);
  }
}

async function loadPage() {
  renderSidebar('literature');
  await loadHealthStatus(healthStatus);
}

document.getElementById('literature-form').addEventListener('submit', runWorkflow);
loadPage().catch((error) => {
  healthStatus.textContent = `服务不可用：${error.message}`;
});
