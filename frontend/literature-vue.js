import { apiFetch, endpoints, loadHealthStatus, renderSidebar } from './common.js';

const { createApp } = window.Vue;

const DEFAULT_TEMPLATE = `你是一名熟悉合成孔径雷达（SAR）成像、机载SAR系统、频域与时域成像算法、Chirp Scaling / Nonlinear Chirp Scaling（NCS）算法、运动补偿与复杂成像几何处理的科研助手。

请围绕研究主题完成系统检索：机载SAR成像算法、复杂几何成像、高斜视/滑动聚束、NCS/CSA改进、运动补偿与自聚焦。

执行要求：
1) 输出分层结果：candidate -> priority -> core；
2) 输出证据提取表：题目、作者、年份、venue、数据库来源、DOI/arXiv、PDF可得性、核心算法类别、创新点、局限性、推荐等级；
3) 不得虚构元数据，无法确认的信息标注 UNVERIFIED；
4) 优先 2020-至今，重点 2024-2026。`;

createApp({
  data() {
    return {
      form: {
        user_requirement: '机载SAR成像领域的论文系统整理与综述构建，重点关注NCS/CSA及复杂几何场景下的成像算法。',
        prompt_template: DEFAULT_TEMPLATE,
        use_web_search: true,
        store_to_library: true,
      },
      loading: false,
      statusText: '提交后这里会显示执行状态。',
      statusError: false,
      optimizedPrompt: '',
      searchResult: '',
      healthText: '正在检查服务…',
    };
  },
  computed: {
    workflowEndpoint() {
      return endpoints.literatureWorkflow || '/api/analysis/literature-workflow';
    },
    buttonText() {
      return this.loading ? '检索中，请稍候…' : '生成新提示词并检索文献';
    },
  },
  methods: {
    async runWorkflow() {
      if (!this.form.user_requirement.trim()) {
        this.statusText = '请先填写研究需求。';
        this.statusError = true;
        return;
      }

      this.loading = true;
      this.statusText = '正在调用 Codex：1) 生成新提示词 2) 文献联网检索...';
      this.statusError = false;

      const payload = {
        user_requirement: this.form.user_requirement.trim(),
        prompt_template: this.form.prompt_template.trim() || null,
        use_web_search: this.form.use_web_search,
        compact_output: true,
        store_to_library: this.form.store_to_library,
      };

      try {
        const result = await apiFetch(this.workflowEndpoint, {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        const stored = result.stored?.created_count ?? 0;
        this.statusText = `执行完成 · 模型：${result.model} · Web Search：${result.used_web_search ? '启用' : '关闭'} · 外部检索回退：${result.used_external_fallback ? '是(OpenAlex)' : '否'} · 入库新增：${stored}`;
        this.optimizedPrompt = result.optimized_prompt || '未生成。';
        this.searchResult = this.prettyResult(result.search_result);
      } catch (error) {
        this.statusText = `执行失败：${error.message}`;
        this.statusError = true;
      } finally {
        this.loading = false;
      }
    },
    async initPage() {
      renderSidebar('literature');
      const healthEl = document.getElementById('health-status');
      try {
        await loadHealthStatus(healthEl);
      } catch (error) {
        this.healthText = `服务不可用：${error.message}`;
        healthEl.textContent = this.healthText;
      }
    },
    prettyResult(raw) {
      if (!raw) return '未返回内容。';
      try {
        return JSON.stringify(JSON.parse(raw), null, 2);
      } catch {
        return raw;
      }
    },
  },
  mounted() {
    this.initPage().catch(() => {});
  },
}).mount('#literature-app');
