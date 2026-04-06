import os

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
        initialize_default_doctors()
        initialize_default_medical_charts()
        initialize_default_templates()
        initialize_default_roles()
        initialize_default_admin()
        initialize_default_role_permissions()
        initialize_default_groups()
        initialize_user_management()


if __name__ == "__main__":
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

