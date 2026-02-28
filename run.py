# -*- coding: utf-8 -*-
"""
Điểm khởi chạy ứng dụng - Phòng khám Đại Anh
Dùng cho triển khai LAN nội bộ
"""
import os

# Chọn môi trường: development | production
ENV = os.environ.get('FLASK_ENV', 'development')

# Bật HTTPS để tránh cảnh báo "Not secure" trên Chrome
USE_HTTPS = os.environ.get('USE_HTTPS', '1') == '1'

if __name__ == '__main__':
    from app import app, create_tables
    
    create_tables()
    
    # host='0.0.0.0' cho phép máy khác trong mạng LAN truy cập
    # ssl_context='adhoc' = HTTPS với chứng chỉ tự ký (tránh cảnh báo Not secure)
    debug = ENV == 'development'
    kwargs = {'host': '0.0.0.0', 'port': 5000, 'debug': debug}
    
    if USE_HTTPS:
        try:
            kwargs['ssl_context'] = 'adhoc'
            print('Chạy HTTPS: https://<IP_máy_chủ>:5000')
        except Exception as e:
            print('Không thể bật HTTPS:', e, '- Chạy HTTP')
    
    app.run(**kwargs)
