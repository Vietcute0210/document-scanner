"""
Gemini AI Vision OCR Engine.
Uses Google Gemini 2.5 Flash to extract text and reconstruct document content
from scanned images, producing structured output for Word document generation.
"""

import os
import io
import base64
import json
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _load_api_key() -> str:
    """Load Gemini API key from environment or .env file."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key and key != "your_api_key_here":
        return key

    # Try loading from .env file in project root
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "GEMINI_API_KEY":
                val = v.strip().strip('"').strip("'")
                if val and val != "your_api_key_here":
                    return val

    # Try loading from gemini_credentials.json
    cred_path = Path.home() / ".gemini" / "config" / "skills" / "gemini-4-api" / "gemini_credentials.json"
    if cred_path.exists():
        try:
            data = json.loads(cred_path.read_text(encoding="utf-8"))
            val = data.get("gemini_api_key", "")
            if val and val != "your_api_key_here":
                return val
        except Exception:
            pass

    return ""


def _image_to_base64(image: np.ndarray, quality: int = 90) -> str:
    """Convert a numpy image (BGR or grayscale) to a base64-encoded JPEG string."""
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf.tobytes()).decode("utf-8")


# ---------------------------------------------------------------------------
# Core OCR function
# ---------------------------------------------------------------------------

def extract_text_with_gemini(
    image: Union[np.ndarray, str, Path],
    lang: str = "vi",
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> str:
    """
    Send a scanned document image to Gemini Vision API and extract all text.

    Args:
        image: Image as numpy array (BGR/grayscale) or file path.
        lang: Target language hint ('vi' for Vietnamese, 'en' for English).
        api_key: Gemini API key. If None, auto-loaded from env/.env/credentials.
        model: Gemini model name to use.

    Returns:
        Extracted plain text string.

    Raises:
        RuntimeError: If API call fails or no key is available.
    """
    import urllib.request
    import urllib.error

    key = api_key or _load_api_key()
    if not key:
        raise RuntimeError(
            "Không tìm thấy GEMINI_API_KEY. Vui lòng cấu hình trong file .env "
            "hoặc biến môi trường GEMINI_API_KEY."
        )

    # Load image
    if isinstance(image, (str, Path)):
        cv_img = cv2.imread(str(image))
        if cv_img is None:
            raise FileNotFoundError(f"Cannot read image: {image}")
    else:
        cv_img = image.copy()

    img_b64 = _image_to_base64(cv_img)

    lang_name = "tiếng Việt" if lang.startswith("vi") else "English"

    prompt = (
        f"Bạn là chuyên gia OCR. Hãy trích xuất TOÀN BỘ nội dung chữ viết trong ảnh tài liệu này.\n"
        f"Ngôn ngữ chính: {lang_name}.\n"
        f"Quy tắc:\n"
        f"- Giữ nguyên cấu trúc văn bản gốc (tiêu đề, đoạn văn, danh sách, bảng).\n"
        f"- Nếu có bảng, dùng dấu | để ngăn cách cột.\n"
        f"- Nếu có tiêu đề/heading, đánh dấu bằng ## ở đầu dòng.\n"
        f"- Giữ nguyên số thứ tự, ký hiệu đặc biệt.\n"
        f"- Chỉ trả về nội dung text, KHÔNG thêm giải thích hay bình luận.\n"
    )

    # Build API request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_b64,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"Gemini API connection error: {e}")

    # Parse response
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini API response format: {e}\n{json.dumps(result, indent=2)}")


# ---------------------------------------------------------------------------
# Structured extraction for smart DOCX building
# ---------------------------------------------------------------------------

def extract_structured_content(
    image: Union[np.ndarray, str, Path],
    lang: str = "vi",
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Extract structured document content from a scanned image using Gemini Vision.

    Returns a dict with:
        - "title": str or None
        - "blocks": list of dicts, each with:
            - "type": "heading" | "paragraph" | "list" | "table" | "image_description"
            - "level": int (for headings, 1-3)
            - "content": str (text content)
            - "items": list of str (for lists)
            - "rows": list of list of str (for tables)

    This structured output is used by ai_docx_builder to create
    well-formatted Word documents.
    """
    import urllib.request
    import urllib.error

    key = api_key or _load_api_key()
    if not key:
        raise RuntimeError(
            "Không tìm thấy GEMINI_API_KEY. Vui lòng cấu hình trong file .env "
            "hoặc biến môi trường GEMINI_API_KEY."
        )

    if isinstance(image, (str, Path)):
        cv_img = cv2.imread(str(image))
        if cv_img is None:
            raise FileNotFoundError(f"Cannot read image: {image}")
    else:
        cv_img = image.copy()

    img_b64 = _image_to_base64(cv_img)

    lang_name = "tiếng Việt" if lang.startswith("vi") else "English"

    prompt = (
        f"Bạn là chuyên gia phân tích tài liệu. Hãy phân tích ảnh tài liệu này và trả về kết quả JSON.\n"
        f"Ngôn ngữ chính: {lang_name}.\n\n"
        f"Trả về JSON với cấu trúc sau (KHÔNG wrap trong markdown code block):\n"
        f'{{\n'
        f'  "title": "Tiêu đề tài liệu nếu có, hoặc null",\n'
        f'  "blocks": [\n'
        f'    {{\n'
        f'      "type": "heading",\n'
        f'      "level": 1,\n'
        f'      "content": "Nội dung tiêu đề"\n'
        f'    }},\n'
        f'    {{\n'
        f'      "type": "paragraph",\n'
        f'      "content": "Nội dung đoạn văn..."\n'
        f'    }},\n'
        f'    {{\n'
        f'      "type": "list",\n'
        f'      "items": ["Mục 1", "Mục 2", "Mục 3"]\n'
        f'    }},\n'
        f'    {{\n'
        f'      "type": "table",\n'
        f'      "rows": [["Header1", "Header2"], ["Cell1", "Cell2"]]\n'
        f'    }},\n'
        f'    {{\n'
        f'      "type": "image_description",\n'
        f'      "content": "Mô tả hình ảnh/biểu đồ/sơ đồ có trong tài liệu"\n'
        f'    }}\n'
        f'  ]\n'
        f'}}\n\n'
        f"Quy tắc:\n"
        f"- Trích xuất CHÍNH XÁC tất cả chữ viết.\n"
        f"- Phân loại đúng loại block (heading/paragraph/list/table/image_description).\n"
        f"- Nếu có hình vẽ, biểu đồ, sơ đồ → tạo block image_description mô tả chi tiết.\n"
        f"- Giữ nguyên thứ tự xuất hiện trong tài liệu gốc.\n"
        f"- CHỈ trả về JSON hợp lệ, không có text nào khác.\n"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_b64,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"Gemini API connection error: {e}")

    # Parse response
    try:
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini API response: {e}")

    # Clean up response - remove markdown code fences if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Remove ```json ... ``` wrapper
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        structured = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: wrap plain text into a simple structure
        structured = {
            "title": None,
            "blocks": [
                {"type": "paragraph", "content": raw_text.strip()}
            ],
        }

    return structured
