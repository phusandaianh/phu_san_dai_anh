"""Chuẩn hóa họ tên hiển thị: chữ cái đầu mỗi từ viết hoa, còn lại viết thường (tiếng Việt)."""

import unicodedata


def strip_accents_for_dicom_modality(text: str) -> str:
    """
    Bỏ dấu tiếng Việt → chỉ còn ký tự ASCII để máy siêu âm / DICOM cũ
    hiển thị đúng (nhiều máy xử lý kém UTF-8 / ISO_IR 192 trong trường PN).
    Web và mwl.db vẫn có thể lưu tên có dấu; chỉ dùng hàm này lúc gửi MWL SCP.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    s = text.replace("Đ", "D").replace("đ", "d")
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def patient_name_title_vi(name: str) -> str:
    if not name or not isinstance(name, str):
        return (name or "").strip() if isinstance(name, str) else ""
    parts = []
    for part in name.split():
        if not part:
            continue
        lower = part.lower()
        if not lower:
            continue
        parts.append(lower[0].upper() + lower[1:] if len(lower) > 1 else lower.upper())
    return " ".join(parts)
