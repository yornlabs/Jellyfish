"""影视信息抽取系统（人物/地点/道具）。

从给定小说文本 chunk 中抽取人物、地点、道具，并提供可追溯证据（EvidenceSpan）。
要求：严格忠实原文，不得编造；无法确定时写入 uncertainties。
技能说明见 backend/skills/film_entity_extractor.md。
"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, ConfigDict, Field

from app.core.skills_runtime.schemas import Character, Location, Prop, Uncertainty


class TextChunk(BaseModel):
    """输入的文本块。chunk_id 会写入 EvidenceSpan.chunk_id 用于回查。"""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(..., description="例如 chapter1_p03 / ch05_para12")
    text: str = Field(..., description="该 chunk 的原文文本")


class FilmEntityExtractionResult(BaseModel):
    """实体抽取结果（复用 runtime schemas 的 Character/Location/Prop）。"""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="小说/章节标识，例如 novel_x_ch05")
    language: Optional[str] = Field(None, description="如 zh/en（可选）")
    extraction_version: Optional[str] = Field(None, description="抽取器版本（可选）")
    schema_version: Optional[str] = Field(None, description="schemas 版本（可选）")

    chunks: List[str] = Field(default_factory=list, description="本次处理的 chunk_id 列表")

    characters: List[Character] = Field(default_factory=list)
    locations: List[Location] = Field(default_factory=list)
    props: List[Prop] = Field(default_factory=list)

    notes: List[str] = Field(default_factory=list, description="全局备注（可选）")
    uncertainties: List[Uncertainty] = Field(default_factory=list, description="结构化不确定项")


_ENTITY_EXTRACTION_INSTRUCTIONS = """\
你是“影视文本信息抽取系统”。你的唯一任务是：从输入小说原文中抽取【人物】【地点】【道具】，并给出可追溯证据。

## 硬性规则（必须遵守）
- 绝对禁止编造：不得凭常识补全姓名、身份、外貌、地点类型、道具用途等；原文没写就不写。
- 只抽取原文明确出现的实体：如果只是“他/她/那里/东西”等代词且无法指代明确实体，不要强行新建实体；可在 uncertainties 说明原因。
- 所有实体的关键字段都应尽量附带 EvidenceSpan（至少给 first_appearance；quote ≤ 200 字，必须是原文摘录）。
- 不要输出 schemas 未定义的字段；输出 JSON，且必须能被 Pydantic 校验（extra=forbid）。
- ID 规则：characters 用 char_001 起；locations 用 loc_001 起；props 用 prop_001 起。保持稳定、不要跳号。
- 同一实体可能有多个称呼：把原文出现的别名放进 aliases；normalized_name 只能来自原文（例如原文既叫“王二”也叫“二哥”）。
- confidence：可选；如果给出必须在 0-1 之间；不确定就留空。

## 输出结构
输出必须是一个 JSON 对象，符合下列模型（字段名必须完全一致）：
- source_id: string
- language?: string
- extraction_version?: string
- schema_version?: string
- chunks: string[]
- characters: Character[]
- locations: Location[]
- props: Prop[]
- notes: string[]
- uncertainties: Uncertainty[]

其中 Character/Location/Prop/EvidenceSpan/Uncertainty 的字段以 schemas.py 为准：
- EvidenceSpan: { chunk_id, start_char?, end_char?, quote? }
- Uncertainty: { field_path, reason, evidence[] }

## 抽取策略（尽量“忠实 + 可用”）
- 人物：优先抽取具名角色；对“掌柜/车夫/士兵”等泛称，只有在原文多次出现且可作为角色稳定识别时才建人物。
- 地点：出现明确地名/场所名时抽取；若只是“屋里/门外”且无稳定命名，可不抽取或写入 uncertainties。
- 道具：只抽取剧情关键或明确被提及的物件（信件、刀、钥匙、手机等）。不要把“桌椅板凳”当道具堆砌，除非原文强调其关键性。

只输出 JSON，不要输出任何解释性文字。
"""


FILM_ENTITY_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["source_id", "language", "chunks_json"],
    template="""{instructions}

## 输入
source_id: {source_id}
language: {language}
chunks (JSON 数组，元素含 chunk_id 与 text):
{chunks_json}

## 输出
请输出 FilmEntityExtractionResult 的 JSON。
""",
    partial_variables={"instructions": _ENTITY_EXTRACTION_INSTRUCTIONS},
)
