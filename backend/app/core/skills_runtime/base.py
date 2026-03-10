"""影视技能抽象基类：关键信息提取、分镜提取。

底层通过 agent（Runnable）调用，支持按 skill_id 加载 skill（Prompt + 输出模型）并格式化输出。
当 agent 支持 with_structured_output 时，优先使用 Tool/函数调用策略直接得到 BaseModel；
否则回退为「原始字符串 → JSON 解析 → 规范化 → Pydantic 校验」。
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, cast

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel

# 使用 Tool/函数调用策略时的方法名（OpenAI function calling）
STRUCTURED_OUTPUT_METHOD = "function_calling"

from app.core.skills_runtime.film_entity_extractor import (
    FILM_ENTITY_EXTRACTION_PROMPT,
    FilmEntityExtractionResult,
)
from app.core.skills_runtime.film_shotlist_storyboarder import (
    FILM_SHOTLIST_PROMPT,
    FilmShotlistResult,
)


T = TypeVar("T", bound=BaseModel)

# 技能注册表：skill_id -> (PromptTemplate, 输出 Pydantic 类型)
SKILL_REGISTRY: dict[str, tuple[PromptTemplate, type[BaseModel]]] = {
    "film_entity_extractor": (FILM_ENTITY_EXTRACTION_PROMPT, FilmEntityExtractionResult),
    "film_shotlist": (FILM_SHOTLIST_PROMPT, FilmShotlistResult),
}


def _extract_json_from_text(raw: str) -> str:
    """从 LLM 原始输出中剥离 markdown 代码块并提取 JSON 字符串。"""
    text = raw.strip()
    # 去除 ```json ... ``` 或 ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


def _normalize_entity_result(data: dict[str, Any]) -> dict[str, Any]:
    """将 LLM 常见字段名/结构映射为 FilmEntityExtractionResult 所需，便于真实模型通过校验。"""
    data = dict(data)
    for key in ("characters", "locations", "props"):
        if key not in data or not isinstance(data[key], list):
            continue
        out = []
        for item in list(data[key]):
            item = dict(item)
            if "name" not in item and item.get("normalized_name"):
                item["name"] = item["normalized_name"]
            if "evidence" in item:
                ev = item.pop("evidence", [])
                if ev and "first_appearance" not in item:
                    item["first_appearance"] = ev[0] if isinstance(ev[0], dict) else None
            if key != "characters":
                item.pop("aliases", None)
            out.append(item)
        data[key] = out
    if "chunks" not in data:
        data["chunks"] = []
    return data


def _normalize_shotlist_result(data: dict[str, Any]) -> dict[str, Any]:
    """将 LLM 常见字段名/结构映射为 FilmShotlistResult(ProjectCinematicBreakdown) 所需。"""
    if "breakdown" not in data:
        return data
    b = dict(data["breakdown"])
    if "characters" in b:
        b["characters"] = [_norm_character(c) for c in b["characters"]]
    if "scenes" in b:
        b["scenes"] = [_norm_scene(s) for s in b["scenes"]]
    if "shots" in b:
        b["shots"] = [_norm_shot(s, i) for i, s in enumerate(b["shots"])]
    if "transitions" in b:
        shots = b.get("shots") or []
        shot_ids = [s.get("id") or (s.get("shot_id") if isinstance(s, dict) else None) for s in shots]
        shot_ids = [x for x in shot_ids if x]
        b["transitions"] = [
            _norm_transition(t, i, shot_ids) for i, t in enumerate(b["transitions"])
        ]
    data["breakdown"] = b
    return data


def _norm_character(c: dict[str, Any]) -> dict[str, Any]:
    c = dict(c)
    if "id" not in c and c.get("character_id"):
        c["id"] = c.pop("character_id")
    return c


def _norm_scene(s: dict[str, Any]) -> dict[str, Any]:
    s = dict(s)
    if "id" not in s and s.get("scene_id"):
        s["id"] = s.pop("scene_id")
    if "summary" not in s and s.get("description"):
        s["summary"] = s.pop("description")
    return s


def _norm_shot(s: dict[str, Any], index: int = 0) -> dict[str, Any]:
    s = dict(s)
    if "id" not in s and s.get("shot_id"):
        s["id"] = s.pop("shot_id")
    if "order" not in s:
        s["order"] = index + 1
    if "evidence_spans" in s:
        s["evidence"] = s.pop("evidence_spans", [])
    if "vfx_type" in s and "vfx" not in s:
        vfx_type = s.pop("vfx_type", "NONE")
        s["vfx"] = [{"vfx_type": vfx_type}]
    return s


def _norm_transition(
    t: dict[str, Any], index: int = 0, shot_ids: list[str] | None = None
) -> dict[str, Any]:
    t = dict(t)
    t.pop("transition_id", None)
    t.pop("evidence_spans", None)
    if "transition" not in t and t.get("transition_type"):
        t["transition"] = t.pop("transition_type")
    if "from_shot_id" not in t or "to_shot_id" not in t:
        shot_ids = shot_ids or []
        if index + 1 < len(shot_ids):
            t.setdefault("from_shot_id", shot_ids[index])
            t.setdefault("to_shot_id", shot_ids[index + 1])
    return t


class ExtractionSkillBase(ABC, Generic[T]):
    """影视抽取技能抽象基类：加载 skill、调用 agent、格式化输出。

    agent：LangChain Runnable。若为 ChatModel（如 ChatOpenAI），则通过 with_structured_output
    (Tool/函数调用策略) 直接得到 BaseModel；否则走「原始字符串 → JSON 解析 → 规范化 → 校验」。
    """

    def __init__(
        self,
        agent: Runnable,
        *,
        structured_output_method: str = STRUCTURED_OUTPUT_METHOD,
    ) -> None:
        self._agent = agent
        self._structured_output_method = structured_output_method
        self._prompt: PromptTemplate | None = None
        self._output_model: type[BaseModel] | None = None
        self._skill_id: str | None = None
        self._structured_chain: Runnable | None = None  # prompt | llm.with_structured_output(...)

    @property
    def skill_id(self) -> str | None:
        return self._skill_id

    @abstractmethod
    def load_skill(self, skill_id: str) -> None:
        """按 skill_id 加载 skill（设置 prompt 与 output_model）。"""
        ...

    def _ensure_loaded(self) -> None:
        if self._prompt is None or self._output_model is None:
            raise RuntimeError(
                "Skill not loaded; call load_skill(skill_id) first. "
                f"Available: {list(SKILL_REGISTRY.keys())}"
            )

    def _build_structured_chain(self) -> Runnable | None:
        """若 agent 支持 with_structured_output，则构建 prompt | agent.with_structured_output(schema)。"""
        self._ensure_loaded()
        with_structured = getattr(self._agent, "with_structured_output", None)
        if not callable(with_structured):
            return None
        assert self._prompt is not None and self._output_model is not None
        structured_llm = cast(
            Runnable,
            with_structured(
                self._output_model,
                method=self._structured_output_method,
            ),
        )
        return self._prompt | structured_llm

    def _get_structured_chain(self) -> Runnable | None:
        """返回已缓存的或新构建的 structured chain。"""
        if self._structured_chain is not None:
            return self._structured_chain
        self._structured_chain = self._build_structured_chain()
        return self._structured_chain

    def run(self, input_dict: dict[str, Any]) -> str:
        """调用 agent，返回原始字符串（通常为 JSON）。"""
        self._ensure_loaded()
        assert self._prompt is not None
        chain: Runnable = self._prompt | self._agent
        result = chain.invoke(input_dict)
        if hasattr(result, "content"):
            return getattr(result, "content", str(result))
        return str(result)

    async def arun(self, input_dict: dict[str, Any]) -> str:
        """异步调用 agent。"""
        self._ensure_loaded()
        assert self._prompt is not None
        chain: Runnable = self._prompt | self._agent
        result = await chain.ainvoke(input_dict)
        if hasattr(result, "content"):
            return getattr(result, "content", str(result))
        return str(result)

    def format_output(self, raw: str) -> T:
        """将 agent 原始输出解析为结构化结果（JSON → 规范化 → Pydantic）。"""
        self._ensure_loaded()
        assert self._output_model is not None
        json_str = _extract_json_from_text(raw)
        data = json.loads(json_str)
        if isinstance(data, dict):
            if "breakdown" in data:
                data = _normalize_shotlist_result(data)
            else:
                data = _normalize_entity_result(data)
        return self._output_model.model_validate(data)  # type: ignore[return-value]

    def extract(self, input_dict: dict[str, Any]) -> T:
        """执行抽取：优先走 with_structured_output 直接得到 BaseModel，否则 run + format_output。"""
        chain = self._get_structured_chain()
        if chain is not None:
            result = chain.invoke(input_dict)
            if isinstance(result, BaseModel):
                return result  # type: ignore[return-value]
            if isinstance(result, dict):
                data = _normalize_shotlist_result(result) if "breakdown" in result else _normalize_entity_result(result)
                return self._output_model.model_validate(data)  # type: ignore[return-value]
        raw = self.run(input_dict)
        return self.format_output(raw)

    async def aextract(self, input_dict: dict[str, Any]) -> T:
        """异步执行抽取。"""
        chain = self._get_structured_chain()
        if chain is not None:
            result = await chain.ainvoke(input_dict)
            if isinstance(result, BaseModel):
                return result  # type: ignore[return-value]
            if isinstance(result, dict):
                data = _normalize_shotlist_result(result) if "breakdown" in result else _normalize_entity_result(result)
                return self._output_model.model_validate(data)  # type: ignore[return-value]
        raw = await self.arun(input_dict)
        return self.format_output(raw)


# ---------------------------------------------------------------------------
# 关键信息提取（人物/地点/道具）
# ---------------------------------------------------------------------------


class KeyInfoExtractorBase(ExtractionSkillBase[FilmEntityExtractionResult], ABC):
    """关键信息提取抽象基类：从小说文本抽取人物、地点、道具等实体。"""

    @abstractmethod
    def load_skill(self, skill_id: str) -> None:
        """加载实体抽取类 skill（如 film_entity_extractor）。"""
        ...


# ---------------------------------------------------------------------------
# 分镜提取（场景/镜头/转场）
# ---------------------------------------------------------------------------


class ShotlistExtractorBase(ExtractionSkillBase[FilmShotlistResult], ABC):
    """分镜提取抽象基类：将小说片段转为可拍镜头表（shot list）。"""

    @abstractmethod
    def load_skill(self, skill_id: str) -> None:
        """加载分镜类 skill（如 film_shotlist）。"""
        ...


# ---------------------------------------------------------------------------
# 实现类
# ---------------------------------------------------------------------------


class FilmEntityExtractor(KeyInfoExtractorBase):
    """关键信息提取实现：使用 film_entity_extractor skill，输出人物/地点/道具。"""

    KEY_INFO_SKILL_IDS = ("film_entity_extractor",)

    def load_skill(self, skill_id: str) -> None:
        if skill_id not in self.KEY_INFO_SKILL_IDS or skill_id not in SKILL_REGISTRY:
            raise ValueError(
                f"Unknown or invalid key-info skill_id: {skill_id}. "
                f"Allowed: {self.KEY_INFO_SKILL_IDS}"
            )
        self._prompt, self._output_model = SKILL_REGISTRY[skill_id]
        self._skill_id = skill_id
        self._structured_chain = None


class FilmShotlistStoryboarder(ShotlistExtractorBase):
    """分镜提取实现：使用 film_shotlist skill，输出场景/镜头/转场（ProjectCinematicBreakdown）。"""

    SHOTLIST_SKILL_IDS = ("film_shotlist",)

    def load_skill(self, skill_id: str) -> None:
        if skill_id not in self.SHOTLIST_SKILL_IDS or skill_id not in SKILL_REGISTRY:
            raise ValueError(
                f"Unknown or invalid shotlist skill_id: {skill_id}. "
                f"Allowed: {self.SHOTLIST_SKILL_IDS}"
            )
        self._prompt, self._output_model = SKILL_REGISTRY[skill_id]
        self._skill_id = skill_id
        self._structured_chain = None
