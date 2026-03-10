"""从小说文本抽取的影视化分镜数据结构：人物/地点/道具、场景、镜头、转场及可追溯证据。"""

from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# ---------- Common ----------
DialogueLineMode = Literal["DIALOGUE", "VOICE_OVER", "OFF_SCREEN", "PHONE"]


class EvidenceSpan(BaseModel):
    """可追溯证据：原文定位（chunk + 起止位置/摘录），用于审核与回查。"""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(..., description="输入文本块的唯一ID（例如 chapter1_p03）")
    start_char: Optional[int] = Field(None, description="在该 chunk 中的起始字符位置（可选）")
    end_char: Optional[int] = Field(None, description="在该 chunk 中的结束字符位置（可选）")
    quote: Optional[str] = Field(None, description="不超过200字的原文摘录（可选，便于人工审核）")


class DialogueLine(BaseModel):
    """单条对白：说话人/对象、正文、情绪与表达方式、旁白/电话等模式、镜头内时间点。"""

    model_config = ConfigDict(extra="forbid")

    speaker_character_id: Optional[str] = Field(None, description="说话人角色ID，若无法判定可为空")
    target_character_id: Optional[str] = Field(None, description="对谁说（听者角色ID），可选")
    text: str = Field(..., description="对白正文")
    emotion: Optional[str] = Field(None, description="情绪/语气（如：愤怒、平静、哽咽）")
    delivery: Optional[str] = Field(None, description="表达方式（如：低声、喊叫、旁白腔）")
    line_mode: DialogueLineMode = Field(
        "DIALOGUE",
        description="DIALOGUE=正常对白, VOICE_OVER=旁白, OFF_SCREEN=画外音, PHONE=电话音等",
    )
    start_time_sec: Optional[float] = Field(None, ge=0, description="在该镜头内相对起始时间（秒），用于对口型/字幕切分")
    evidence: List[EvidenceSpan] = Field(default_factory=list, description="原文依据")


# ---------- Entities ----------
class Character(BaseModel):
    """从小说中抽取的角色：主名、别名、外貌与性格、服装描述、首次出场证据及抽取置信度。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="稳定ID，例如 char_001")
    name: str = Field(..., description="主名称（尽量取原文最常用的称呼）")
    normalized_name: Optional[str] = Field(None, description="归一化主名，如将「王二/二哥/王二哥」统一为同一主名（来自文本）")
    aliases: List[str] = Field(default_factory=list, description="别名/称呼（原文出现过的）")
    description: Optional[str] = Field(None, description="外貌/身份/气质（忠实原文，与服装区分）")
    costume_note: Optional[str] = Field(
        None,
        description="从原文抽取的服装/造型描述（如款式、颜色、配饰），与 description 区分，便于后续关联服装资产",
    )
    traits: List[str] = Field(default_factory=list, description="性格/特征词（尽量来自原文）")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="抽取确定度 0-1（模型输出）")
    first_appearance: Optional[EvidenceSpan] = None


class Location(BaseModel):
    """从小说中抽取的地点：名称、类型、场景描写及首次出场证据、置信度。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="稳定ID，例如 loc_001")
    name: str = Field(..., description="地点名称（原文）")
    normalized_name: Optional[str] = Field(None, description="归一化名称（来自文本）")
    type: Optional[str] = Field(None, description="地点类型：房间/街道/森林/车厢等（可选）")
    description: Optional[str] = Field(None, description="场景描写（忠实原文，简短）")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="抽取确定度 0-1（模型输出）")
    first_appearance: Optional[EvidenceSpan] = None


class Prop(BaseModel):
    """从小说中抽取的道具：名称、类别、外观/用途、归属角色及首次出场证据、置信度。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="稳定ID，例如 prop_001")
    name: str = Field(..., description="道具名称（原文）")
    normalized_name: Optional[str] = Field(None, description="归一化名称（来自文本）")
    category: Optional[str] = Field(None, description="可选：weapon/document/vehicle/clothing/device/magic_item/other")
    description: Optional[str] = Field(None, description="外观/用途（忠实原文）")
    owner_character_id: Optional[str] = Field(None, description="拥有者（如果明确）")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="抽取确定度 0-1（模型输出）")
    first_appearance: Optional[EvidenceSpan] = None


# ---------- Story / Scenes ----------
SceneTime = Literal["DAY", "NIGHT", "DAWN", "DUSK", "UNKNOWN"]
SceneInterior = Literal["INT", "EXT", "INT_EXT", "UNKNOWN"]

class Scene(BaseModel):
    """场景：内/外景、时间、关联地点与人物/道具，含原文标题与系统格式化标题。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="例如 scene_001")
    raw_title: Optional[str] = Field(None, description="来自原文的场景标题（若存在）")
    formatted_title: Optional[str] = Field(None, description="系统生成的影视格式标题，如 INT. 地点 - TIME")
    interior: SceneInterior = "UNKNOWN"
    time_of_day: SceneTime = "UNKNOWN"

    location_id: Optional[str] = Field(None, description="loc_xxx，如可判定")
    summary: Optional[str] = Field(None, description="场景发生了什么（忠实原文，短）")

    character_ids: List[str] = Field(default_factory=list, description="该场景出现的人物ID")
    prop_ids: List[str] = Field(default_factory=list, description="该场景关键道具ID")
    evidence: List[EvidenceSpan] = Field(default_factory=list, description="支持该场景的证据片段（可多条）")


# ---------- Cinematic (Shots / Transitions / VFX) ----------
ShotType = Literal["ECU", "CU", "MCU", "MS", "MLS", "LS", "ELS"]
CameraAngle = Literal[
    "EYE_LEVEL", "HIGH_ANGLE", "LOW_ANGLE", "BIRD_EYE", "DUTCH", "OVER_SHOULDER"
]
CameraMovement = Literal[
    "STATIC", "PAN", "TILT", "DOLLY_IN", "DOLLY_OUT", "TRACK", "CRANE", "HANDHELD", "STEADICAM", "ZOOM_IN", "ZOOM_OUT"
]
TransitionType = Literal["CUT", "DISSOLVE", "WIPE", "FADE_IN", "FADE_OUT", "MATCH_CUT", "J_CUT", "L_CUT"]
VFXType = Literal[
    "NONE",
    "PARTICLES",
    "VOLUMETRIC_FOG",
    "CG_DOUBLE",
    "DIGITAL_ENVIRONMENT",
    "MATTE_PAINTING",
    "FIRE_SMOKE",
    "WATER_SIM",
    "DESTRUCTION",
    "ENERGY_MAGIC",
    "COMPOSITING_CLEANUP",
    "SLOW_MOTION_TIME",
    "OTHER",
]
ComplexityLevel = Literal["LOW", "MEDIUM", "HIGH"]

# ---------- 英文枚举 → 中文映射（影视/分镜专业用语） ----------
DIALOGUE_LINE_MODE_ZH: dict[str, str] = {
    "DIALOGUE": "对白",
    "VOICE_OVER": "旁白",
    "OFF_SCREEN": "画外音",
    "PHONE": "电话声",
}

SCENE_TIME_ZH: dict[str, str] = {
    "DAY": "日",
    "NIGHT": "夜",
    "DAWN": "黎明",
    "DUSK": "黄昏",
    "UNKNOWN": "未知",
}

SCENE_INTERIOR_ZH: dict[str, str] = {
    "INT": "内景",
    "EXT": "外景",
    "INT_EXT": "内景兼外景",
    "UNKNOWN": "未知",
}

SHOT_TYPE_ZH: dict[str, str] = {
    "ECU": "大特写",
    "CU": "特写",
    "MCU": "中近景",
    "MS": "中景",
    "MLS": "中远景",
    "LS": "远景",
    "ELS": "大远景",
}

CAMERA_ANGLE_ZH: dict[str, str] = {
    "EYE_LEVEL": "平视",
    "HIGH_ANGLE": "俯拍",
    "LOW_ANGLE": "仰拍",
    "BIRD_EYE": "鸟瞰",
    "DUTCH": "荷兰角",
    "OVER_SHOULDER": "过肩",
}

CAMERA_MOVEMENT_ZH: dict[str, str] = {
    "STATIC": "固定",
    "PAN": "横摇",
    "TILT": "俯仰",
    "DOLLY_IN": "推轨",
    "DOLLY_OUT": "拉轨",
    "TRACK": "跟拍",
    "CRANE": "升降",
    "HANDHELD": "手持",
    "STEADICAM": "斯坦尼康",
    "ZOOM_IN": "变焦推进",
    "ZOOM_OUT": "变焦拉远",
}

TRANSITION_TYPE_ZH: dict[str, str] = {
    "CUT": "切",
    "DISSOLVE": "叠化",
    "WIPE": "划变",
    "FADE_IN": "淡入",
    "FADE_OUT": "淡出",
    "MATCH_CUT": "匹配剪辑",
    "J_CUT": "J 剪",
    "L_CUT": "L 剪",
}

VFX_TYPE_ZH: dict[str, str] = {
    "NONE": "无",
    "PARTICLES": "粒子",
    "VOLUMETRIC_FOG": "体积雾",
    "CG_DOUBLE": "数字替身",
    "DIGITAL_ENVIRONMENT": "数字场景",
    "MATTE_PAINTING": "绘景",
    "FIRE_SMOKE": "烟火",
    "WATER_SIM": "水效",
    "DESTRUCTION": "破碎/解算",
    "ENERGY_MAGIC": "能量/魔法",
    "COMPOSITING_CLEANUP": "合成/修脏",
    "SLOW_MOTION_TIME": "升格/慢动作",
    "OTHER": "其他",
}

COMPLEXITY_ZH: dict[str, str] = {
    "LOW": "低",
    "MEDIUM": "中",
    "HIGH": "高",
}

PROP_CATEGORY_ZH: dict[str, str] = {
    "weapon": "武器",
    "document": "文书/证件",
    "vehicle": "载具",
    "clothing": "服装",
    "device": "器械/设备",
    "magic_item": "魔法/特殊物品",
    "other": "其他",
}


class VFXNote(BaseModel):
    """单条视效说明：类型、描述、复杂度及原文依据。"""

    model_config = ConfigDict(extra="forbid")

    vfx_type: VFXType = "NONE"
    description: Optional[str] = Field(None, description="视效说明（简短、可执行）")
    complexity: Optional[ComplexityLevel] = Field(None, description="粗略复杂度")
    evidence: List[EvidenceSpan] = Field(default_factory=list, description="原文依据（若为忠实抽取）")


class Shot(BaseModel):
    """单镜头：景别/机位/运镜、时长与画面描述、对白列表、音效与视效、关联角色与道具。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="例如 shot_001_003（scene_001 第3镜）")
    scene_id: str = Field(..., description="所属 scene_xxx")
    order: int = Field(..., ge=1, description="场景内镜头序号，从1开始")

    shot_type: ShotType
    camera_angle: CameraAngle = "EYE_LEVEL"
    camera_movement: CameraMovement = "STATIC"

    # 可拍性/执行信息
    duration_sec: Optional[float] = Field(None, ge=0.5, le=30, description="建议时长（可选）")
    description: str = Field(..., description="镜头里发生的动作/画面（行业口吻，简短可拍）")

    character_ids: List[str] = Field(default_factory=list)
    prop_ids: List[str] = Field(default_factory=list)

    vfx: List[VFXNote] = Field(default_factory=list)
    sfx: List[str] = Field(default_factory=list, description="音效提示，如 footsteps, rain, explosion（可选）")
    dialogue_lines: List[DialogueLine] = Field(
        default_factory=list,
        description="该镜头内的对白列表（结构化：说话人、对象、情绪、旁白/电话等、时间点）",
    )
    dialogue: Optional[str] = Field(None, description="[兼容] 若该镜头承载关键对白，可摘录/概述（可选）")

    evidence: List[EvidenceSpan] = Field(default_factory=list, description="对应原文依据（可选）")


class Transition(BaseModel):
    """镜头间转场：从哪镜到哪镜、转场类型及可选说明。"""

    model_config = ConfigDict(extra="forbid")

    from_shot_id: str
    to_shot_id: str
    transition: TransitionType = "CUT"
    note: Optional[str] = Field(None, description="为何用该转场（可选）")


# ---------- Extraction metadata & uncertainties ----------
class Uncertainty(BaseModel):
    """结构化不确定项：字段路径、原因及可选证据，便于人工审核与回溯。"""

    model_config = ConfigDict(extra="forbid")

    field_path: str = Field(..., description="如 characters[0].name、scenes[2].location_id")
    reason: str = Field(..., description="不确定原因简述")
    evidence: List[EvidenceSpan] = Field(default_factory=list, description="相关原文依据（可选）")


class ProjectCinematicBreakdown(BaseModel):
    """从小说抽取的完整影视分镜：元信息、实体表、场景表、镜头表、转场表及不确定项。"""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="小说/章节标识，例如 novel_x_ch05")
    source_title: Optional[str] = Field(None, description="书名/章节名（从书名页或章节头抽取）")
    source_author: Optional[str] = Field(None, description="作者（若可从文本抽取）")
    language: Optional[str] = Field(None, description="如 zh、en，便于后续提示词与分词")
    extraction_version: Optional[str] = Field(None, description="本次抽取器版本，便于回溯差异")
    schema_version: Optional[str] = Field(None, description="本输出使用的 schema 版本")

    chunks: List[str] = Field(default_factory=list, description="本次处理的 chunk_id 列表")

    characters: List[Character] = Field(default_factory=list)
    locations: List[Location] = Field(default_factory=list)
    props: List[Prop] = Field(default_factory=list)

    scenes: List[Scene] = Field(default_factory=list)
    shots: List[Shot] = Field(default_factory=list)
    transitions: List[Transition] = Field(default_factory=list)

    notes: List[str] = Field(default_factory=list, description="全局备注/不确定点（可选）")
    uncertainties: List[Uncertainty] = Field(
        default_factory=list,
        description="结构化不确定项：field_path、reason、evidence",
    )