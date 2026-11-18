"""Session state lifecycle and invalidation helpers."""
import hashlib
import streamlit as st

IMAGE_KEYS = (
    "raw_cv_img", "source_name", "current_img_hash", "detection",
    "last_detect_params", "active_corners", "is_manual_mode", "final_img",
    "ai_text", "ai_docx", "ai_data", "ai_result_hash", "pdf_output",
    "docx_output", "final_image_hash", "webcam_photo_bytes"
)


def init_session() -> None:
    defaults = {
        "raw_cv_img": None,
        "source_name": "document",
        "current_img_hash": None,
        "detection": None,
        "last_detect_params": None,
        "active_corners": None,
        "is_manual_mode": False,
        "needs_detection": False,
        "webcam_photo_bytes": None,
        "gemini_api_key_input": "",
        "filter_mode": "Màu thông minh",
        "contrast_boost": 2.2,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def image_digest(image) -> str:
    return hashlib.sha256(image.shape.__repr__().encode() + image.tobytes()).hexdigest()


def set_image(image, source_name: str) -> bool:
    """Set image and invalidate derived state only when source content changes."""
    if image is None:
        return False
    digest = image_digest(image)
    if digest == st.session_state.get("current_img_hash"):
        return False
    for key in (
        "detection", "last_detect_params", "active_corners", "final_img",
        "ai_text", "ai_docx", "ai_data", "ai_result_hash", "pdf_output",
        "docx_output", "final_image_hash"
    ):
        st.session_state.pop(key, None)
    st.session_state["raw_cv_img"] = image
    st.session_state["source_name"] = source_name
    st.session_state["current_img_hash"] = digest
    st.session_state["needs_detection"] = True
    st.session_state["is_manual_mode"] = False
    return True


def clear_image() -> None:
    for key in IMAGE_KEYS:
        st.session_state.pop(key, None)
    st.session_state["raw_cv_img"] = None
    st.session_state["needs_detection"] = False
