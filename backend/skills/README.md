# 影视类 Skills 说明文档

本目录仅存放 **skill 的说明文档**（`.md`），便于产品、策划与开发统一查阅。

## 文档列表

| 文档 | 说明 |
|------|------|
| [film_entity_extractor.md](film_entity_extractor.md) | 信息抽取：从小说文本抽取人物、地点、道具，忠实原文、可追溯证据 |
| [film_shotlist_storyboarder.md](film_shotlist_storyboarder.md) | 分镜师：将小说片段转为可拍镜头表（景别/机位/运镜/转场/VFX） |

## 代码与调用

- **数据结构与枚举**：`app.core.skills_runtime.schemas`
- **技能实现**（Prompt + 输出模型）：`app.core.skills_runtime`
  - 信息抽取：`film_entity_extractor` → `FILM_ENTITY_EXTRACTION_PROMPT`、`FilmEntityExtractionResult`
  - 分镜师：`film_shotlist_storyboarder` → `FILM_SHOTLIST_PROMPT`、`FilmShotlistResult`

从应用层引用示例：

```python
from app.core.skills_runtime import (
    FILM_ENTITY_EXTRACTION_PROMPT,
    FilmEntityExtractionResult,
    FILM_SHOTLIST_PROMPT,
    FilmShotlistResult,
)
```
