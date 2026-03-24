from __future__ import annotations

from backend.app.config import settings
from backend.app.services.openai_provider import build_openai_client


DEFAULT_PROMPT_TEMPLATE = """
你是一名熟悉合成孔径雷达（SAR）成像、机载SAR系统、频域与时域成像算法、Chirp Scaling / Nonlinear Chirp Scaling（NCS）算法、运动补偿与复杂成像几何处理的科研助手。

请围绕以下研究主题，系统检索并筛选最新且权威的学术论文，并以适合博士论文/综述论文写作的方式输出结果。

研究主题：
{USER_REQUIREMENT}

输出要求：
1) 必须优先给出候选文献池 -> 重点文献 -> 核心必读文献三层结构；
2) 每篇论文必须标注可核验来源与可下载状态；
3) 对无法核验信息标注“UNVERIFIED”；
4) 不得虚构题目、作者、DOI、期刊、年份；
5) 输出中文说明，论文元信息保持原文。
""".strip()


def run_literature_workflow(user_requirement: str, prompt_template: str | None = None, use_web_search: bool = True) -> dict:
    if not settings.openai_api_key or not settings.openai_enabled:
        return {
            "optimized_prompt": "",
            "search_result": "OpenAI 未配置，无法执行 Codex 文献检索流程。",
            "model": settings.openai_model,
            "used_web_search": False,
        }

    template = (prompt_template or DEFAULT_PROMPT_TEMPLATE).strip()
    client = build_openai_client()

    optimized_prompt = _optimize_prompt(client, user_requirement, template)
    if not optimized_prompt:
        optimized_prompt = template.replace("{USER_REQUIREMENT}", user_requirement.strip())

    search_result = _search_with_prompt(client, optimized_prompt, use_web_search)
    return {
        "optimized_prompt": optimized_prompt,
        "search_result": search_result,
        "model": settings.openai_model,
        "used_web_search": bool(use_web_search),
    }


def _optimize_prompt(client, user_requirement: str, template: str) -> str:
    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": "你是提示词工程专家。请输出可直接给 Codex 执行的完整提示词文本。",
                },
                {
                    "role": "user",
                    "content": (
                        "请基于下面模板，融合用户需求，生成一份更可执行、更结构化的最终提示词。"
                        "\n\n[模板]\n"
                        f"{template}\n\n[用户需求]\n{user_requirement}\n\n"
                        "要求：\n"
                        "- 保留三层文献结构输出（candidate/priority/core）；\n"
                        "- 保留证据提取表字段；\n"
                        "- 明确合法来源与UNVERIFIED标注规则；\n"
                        "- 输出中文提示词正文；\n"
                        "- 只输出最终提示词文本，不要解释。"
                    ),
                },
            ],
            max_output_tokens=2200,
        )
        return (getattr(response, "output_text", "") or "").strip()
    except Exception:
        return ""


def _search_with_prompt(client, optimized_prompt: str, use_web_search: bool) -> str:
    try:
        kwargs = {
            "model": settings.openai_model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "你是SAR文献检索与综述助手。请严格按用户提示词执行，并保留核验标记。"
                        "当启用web_search时，应尽量给出论文标题、作者、年份、DOI/链接、摘要要点与来源。"
                        "对于无法确认的摘要或元数据，标注UNVERIFIED。"
                    ),
                },
                {"role": "user", "content": optimized_prompt},
            ],
            "max_output_tokens": 4200,
        }
        if use_web_search:
            kwargs["tools"] = [{"type": "web_search"}]
            kwargs["tool_choice"] = "auto"

        response = client.responses.create(**kwargs)
        return (getattr(response, "output_text", "") or "").strip() or "未返回可读结果。"
    except Exception as exc:
        return f"调用模型失败：{exc}"
