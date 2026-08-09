import os


def _load_sync_local_env() -> None:
    """Nạp sync_local.env trước khi import app (để bật vòng lặp đồng bộ)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_local.env")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_sync_local_env()

from werkzeug.serving import run_simple
from waitress import serve

from app import (
    app,
    db,
    ensure_appointment_doctor_column,
    ensure_appointment_sync_columns,
    ensure_clinic_summary_column,
    ensure_logo_position_column,
    ensure_user_status_column,
    ensure_user_security_columns,
    ensure_clinical_result_columns,
    ensure_gyn_ultrasound_schema,
    ensure_gyn_exam_schema,
    ensure_general_ultrasound_schema,
    ensure_obstetric_exam_schema,
    ensure_fertility_andrology_schema,
    ensure_infertility_couple_schema,
    initialize_default_doctors,
    initialize_default_medical_charts,
    initialize_default_templates,
    initialize_default_roles,
    initialize_default_admin,
    initialize_default_role_permissions,
    initialize_default_groups,
    initialize_user_management,
)


def initialize_app_data() -> None:
    """
    Khởi tạo cấu trúc CSDL và dữ liệu mặc định cho ứng dụng
    (dựa trên logic hiện có trong block if __name__ == '__main__' của app.py).
    """
    with app.app_context():
        db.create_all()
        ensure_appointment_doctor_column()
        ensure_appointment_sync_columns()
        ensure_clinic_summary_column()
        ensure_logo_position_column()
        ensure_user_status_column()
        ensure_user_security_columns()
        ensure_clinical_result_columns()
        ensure_gyn_ultrasound_schema()
        ensure_gyn_exam_schema()
        ensure_general_ultrasound_schema()
        ensure_obstetric_exam_schema()
        ensure_fertility_andrology_schema()
        ensure_infertility_couple_schema()
        initialize_default_doctors()
        initialize_default_medical_charts()
        initialize_default_templates()
        initialize_default_roles()
        initialize_default_admin()
        initialize_default_role_permissions()
        initialize_default_groups()
        initialize_user_management()


if __name__ == "__main__":
    # Sửa lỗi encoding tiếng Việt trong DB nếu phát hiện mojibake
    try:
        from fix_vietnamese_encoding import maybe_repair_on_startup
        maybe_repair_on_startup()
    except Exception as _vn_enc_err:
        print("Vietnamese encoding check skipped:", _vn_enc_err)

    # Khởi tạo dữ liệu / bảng trước khi chạy server
    initialize_app_data()

    port = int(os.environ.get("PORT", "5000"))
    use_https = os.environ.get("USE_HTTPS", "").strip().lower() in ("1", "true", "yes", "on")
    cert = os.environ.get("SSL_CERT", os.path.join("ssl", "dev.crt"))
    key = os.environ.get("SSL_KEY", os.path.join("ssl", "dev.key"))

    if use_https and os.path.isfile(cert) and os.path.isfile(key):
        # Waitress không hỗ trợ TLS trực tiếp — dùng Werkzeug (threaded) với SSL
        print(f"[HTTPS] https://0.0.0.0:{port}/ (cert={cert})")
        run_simple("0.0.0.0", port, app, threaded=True, ssl_context=(cert, key))
    else:
        if use_https:
            print(
                f"[HTTPS] Thiếu file chứng chỉ. Chạy: python generate_dev_ssl.py "
                f"(cần {cert}, {key}) — tạm dùng HTTP."
            )
        # Chạy ứng dụng bằng Waitress (production WSGI server)
        # 0.0.0.0 để các máy khác trong mạng nội bộ có thể truy cập
        print(f"[HTTP] http://0.0.0.0:{port}/")
        serve(app, host="0.0.0.0", port=port)

