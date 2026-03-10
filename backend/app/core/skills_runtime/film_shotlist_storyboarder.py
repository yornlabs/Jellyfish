"""影视分镜师：将小说片段转为可拍镜头表（shot list）。

使用行业术语（景别、机位、镜头运动、转场、VFX 类型），严格忠实原文，不得编造。
输出复用 ProjectCinematicBreakdown（scenes / shots / transitions），并为关键结论提供 EvidenceSpan。
技能说明见 backend/skills/film_shotlist_storyboarder.md。
"""

from __future__ import annotations

from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, ConfigDict, Field

from app.core.skills_runtime.schemas import ProjectCinematicBreakdown


class FilmShotlistResult(BaseModel):
    """分镜输出（直接复用 runtime 的 ProjectCinematicBreakdown）。"""

    model_config = ConfigDict(extra="forbid")

    breakdown: ProjectCinematicBreakdown = Field(..., description="影视化拆解结果")


_SHOTLIST_INSTRUCTIONS = """\
你是“影视分镜师（Shot List / Storyboard Breakdown）”。你的任务是把给定小说原文拆解为可拍摄的场景与镜头表。

## 硬性规则（必须遵守）
- 绝对禁止编造：不得新增原文不存在的人物/地点/道具/动作/对白/情节；不得凭常识补全。
- 如果原文不确定（比如光线、时间、人物是谁、是否在室内外），请：
  - 在对应字段保持 UNKNOWN/空值，或
  - 写入 uncertainties（field_path + reason + evidence），而不是“猜一个”。
- 所有镜头描述必须“可拍”：明确画面内容与动作，不要抽象文学化抒情。
- 只使用 schemas.py 中允许的枚举值：
  - ShotType: ECU/CU/MCU/MS/MLS/LS/ELS
  - CameraAngle: EYE_LEVEL/HIGH_ANGLE/LOW_ANGLE/BIRD_EYE/DUTCH/OVER_SHOULDER
  - CameraMovement: STATIC/PAN/TILT/DOLLY_IN/DOLLY_OUT/TRACK/CRANE/HANDHELD/STEADICAM/ZOOM_IN/ZOOM_OUT
  - TransitionType: CUT/DISSOLVE/WIPE/FADE_IN/FADE_OUT/MATCH_CUT/J_CUT/L_CUT
  - VFXType: NONE/PARTICLES/VOLUMETRIC_FOG/CG_DOUBLE/DIGITAL_ENVIRONMENT/MATTE_PAINTING/FIRE_SMOKE/WATER_SIM/DESTRUCTION/ENERGY_MAGIC/COMPOSITING_CLEANUP/SLOW_MOTION_TIME/OTHER
- EvidenceSpan.quote ≤ 200 字，必须来自原文摘录；chunk_id 必须来自输入。
- 只输出 JSON（不要解释、不要 markdown、不要多余文本），并且必须能通过 Pydantic 校验（extra=forbid）。

## 输出结构
输出必须是一个 JSON 对象，符合 FilmShotlistResult：
{
  "breakdown": ProjectCinematicBreakdown
}

ProjectCinematicBreakdown 字段（以 schemas.py 为准）：
- source_id, source_title?, source_author?, language?, extraction_version?, schema_version?, chunks[]
- characters[], locations[], props[]
- scenes[], shots[], transitions[]
- notes[], uncertainties[]

## 拆解原则（专业且忠实）
- 先抽取实体表（characters/locations/props），再按叙事推进切分 scenes（场景变化依据：地点/时间/人物组合或叙事段落明显转折）。
- 每个 scene 建议 2-8 个 shot；shot.description 用“行业口吻 + 可拍动作”描述。
- 对白处理：
  - 原文出现引号对白时，尽量拆进 DialogueLine.text（逐句，尽量原句）。
  - speaker/target 不确定可留空，但要把 evidence 填好；必要时在 uncertainties 说明。
  - 旁白/心理独白如果原文明确，可用 VOICE_OVER；画外音用 OFF_SCREEN；电话音用 PHONE。
- 转场 transitions：
  - 同一 scene 内镜头间通常 CUT；明显时间跳跃/回忆可用 DISSOLVE/FADE；声音先行可用 J_CUT/L_CUT（仅当原文能支撑）。
- VFX：
  - 原文明确出现超自然/烟火/水效/破碎/慢动作等才写；否则 vfx_type=NONE。
- 时长 duration_sec 可选：只有在原文节奏/动作明确时才给出，否则留空。

## ID 规则（必须）
- scene_id: scene_001 起
- shot_id: shot_{sceneIndex3}_{order3}，例如 scene_001 的第3镜是 shot_001_003
- from/to_shot_id 必须引用存在的 shot_id

只输出 JSON。
"""


FILM_SHOTLIST_PROMPT = PromptTemplate(
    input_variables=["source_id", "source_title", "language", "chunks_json"],
    template="""{instructions}

## 输入
source_id: {source_id}
source_title: {source_title}
language: {language}
chunks (JSON 数组，元素含 chunk_id 与 text):
{chunks_json}

## 输出
请输出 FilmShotlistResult 的 JSON。
""",
    partial_variables={"instructions": _SHOTLIST_INSTRUCTIONS},
)
