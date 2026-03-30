"""
EchoMie AI Pipeline — VLM scene understanding + LLM healing text + Edge TTS voice.

Uses DashScope (Qwen) via the OpenAI-compatible SDK.
Env vars:
  DASHSCOPE_API_KEY  — required for VLM/LLM
"""

import asyncio
import base64
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import edge_tts
from openai import OpenAI

from .logging_config import get_logger

logger = get_logger("app.ai_service")

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
VLM_MODEL = "qwen-vl-plus"
LLM_MODEL = "qwen-plus"
TTS_VOICE = "zh-CN-XiaoyiNeural"


def _get_client() -> OpenAI:
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY not set")
    return OpenAI(api_key=api_key, base_url=DASHSCOPE_BASE_URL)


def _image_to_data_url(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp", "gif": "image/gif"}.get(ext.lstrip("."), "image/jpeg")
    return f"data:{mime};base64,{data}"


# ─────────────────────────────────────────────
# 1. Key-frame extraction (video → images)
# ─────────────────────────────────────────────

def extract_key_frames(video_path: str, n: int = 3, out_dir: Optional[str] = None) -> List[str]:
    """Extract n evenly-spaced frames from a video. Returns list of saved image paths."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    indices = [int(i * total / (n + 1)) for i in range(1, n + 1)]

    if out_dir is None:
        out_dir = str(Path(video_path).parent / "frames")
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    paths: List[str] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        out_path = str(Path(out_dir) / f"frame_{idx}.jpg")
        cv2.imwrite(out_path, frame)
        paths.append(out_path)

    cap.release()
    return paths


# ─────────────────────────────────────────────
# 2. VLM scene analysis
# ─────────────────────────────────────────────

_VLM_SYSTEM = """你是 EchoMie 的情绪感知 AI。分析用户上传的图片，理解场景、氛围和情绪。
请用 JSON 格式返回分析结果，字段如下：
{
  "scene": "对画面内容的简洁描述（1-2句）",
  "emotion": "识别的主要情绪，从以下选择: happy, calm, sad, lonely, tired, anxious, hopeful, nostalgic, peaceful, excited",
  "mood_score": 1到10的数字，10为最积极,
  "atmosphere": "画面氛围描述（如：温暖的、宁静的、忧郁的）",
  "objects": ["画面中的主要物体列表"],
  "colors": "画面的主色调描述"
}
只返回 JSON，不要其他文字。"""


def analyze_scene(image_path: str, user_context: str = "") -> Dict[str, Any]:
    """Call VLM to understand scene and emotion from an image."""
    client = _get_client()
    data_url = _image_to_data_url(image_path)

    user_parts: list = [
        {"type": "image_url", "image_url": {"url": data_url}},
        {"type": "text", "text": "请分析这张图片的场景和情绪。"},
    ]
    if user_context:
        user_parts.append({"type": "text", "text": f"用户补充说明：{user_context}"})

    try:
        resp = client.chat.completions.create(
            model=VLM_MODEL,
            messages=[
                {"role": "system", "content": _VLM_SYSTEM},
                {"role": "user", "content": user_parts},
            ],
            temperature=0.3,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
        logger.info("VLM analysis: emotion=%s, scene=%s", result.get("emotion"), result.get("scene", "")[:60])
        return result
    except Exception as e:
        logger.error("VLM analyze_scene failed: %s", e)
        return {
            "scene": "一段温暖的日常画面",
            "emotion": "calm",
            "mood_score": 5,
            "atmosphere": "平静的",
            "objects": [],
            "colors": "自然色调",
        }


# ─────────────────────────────────────────────
# 3. LLM healing text generation
# ─────────────────────────────────────────────

_LLM_SYSTEM = """你是 EchoMie 的治愈文案生成师。根据场景分析结果，为用户创作温暖、治愈、有诗意的回应。
请用 JSON 格式返回：
{
  "title": "一个简短的标题（4-8个字）",
  "healing_text": "治愈文案（80-150字，温暖、有共鸣、略带诗意，像一个温柔的朋友在对用户说话）",
  "tags": ["3-5个关键词标签"],
  "emotion_emoji": "一个最匹配情绪的 emoji"
}
只返回 JSON，不要其他文字。"""


def generate_emotion_card(analysis: Dict[str, Any], user_context: str = "") -> Dict[str, Any]:
    """Call LLM to generate healing text based on scene analysis."""
    client = _get_client()

    prompt_parts = [f"场景分析：{json.dumps(analysis, ensure_ascii=False)}"]
    if user_context:
        prompt_parts.append(f"用户的故事：{user_context}")

    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _LLM_SYSTEM},
                {"role": "user", "content": "\n".join(prompt_parts)},
            ],
            temperature=0.7,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
        logger.info("LLM card: title=%s", result.get("title"))
        return result
    except Exception as e:
        logger.error("LLM generate_emotion_card failed: %s", e)
        return {
            "title": "温柔的此刻",
            "healing_text": "每一个平凡的瞬间都值得被温柔以待。感谢你记录下了这一刻，它会成为未来某天回忆里的暖光。",
            "tags": ["日常", "温暖"],
            "emotion_emoji": "🌸",
        }


# ─────────────────────────────────────────────
# 4. Edge TTS voice generation
# ─────────────────────────────────────────────

def generate_voice(text: str, output_path: str, voice: str = TTS_VOICE) -> str:
    """Generate MP3 voice from text using Edge TTS. Returns output path."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    async def _run():
        communicate = edge_tts.Communicate(text, voice, rate="-10%", pitch="-5Hz")
        await communicate.save(output_path)

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()
        logger.info("TTS generated: %s (%d chars)", output_path, len(text))
        return output_path
    except Exception as e:
        logger.error("TTS generation failed: %s", e)
        return ""


# ─────────────────────────────────────────────
# 5. Weekly summary generation
# ─────────────────────────────────────────────

_WEEKLY_SYSTEM = """你是 EchoMie 的每周情绪回顾生成师。根据用户一周的情绪记录，生成温暖的周报总结。
请用 JSON 格式返回：
{
  "summary_text": "200-300字的周总结文案，回顾这一周的情绪变化，给予肯定和鼓励",
  "mood_trend": "情绪趋势描述（如：从疲惫到平静，整体向好）",
  "highlight_tags": ["本周出现最多的3-5个标签"],
  "encouragement": "一句简短的鼓励语（15-25字）"
}
只返回 JSON，不要其他文字。"""


def generate_weekly_summary(cards_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a weekly summary from a list of emotion card data."""
    client = _get_client()

    entries = []
    for c in cards_data:
        entries.append({
            "date": c.get("date", ""),
            "emotion": c.get("emotion", ""),
            "title": c.get("title", ""),
            "tags": c.get("tags", []),
            "scene": c.get("scene", ""),
        })

    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _WEEKLY_SYSTEM},
                {"role": "user", "content": f"本周情绪记录：\n{json.dumps(entries, ensure_ascii=False)}"},
            ],
            temperature=0.7,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        logger.error("Weekly summary generation failed: %s", e)
        return {
            "summary_text": "这一周你记录了生活中的点点滴滴，每一次记录都是对自己的温柔关照。继续保持这份觉察吧。",
            "mood_trend": "平稳",
            "highlight_tags": [],
            "encouragement": "你做得很好，继续温柔地对待自己 🌸",
        }
