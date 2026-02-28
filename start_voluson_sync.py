#!/usr/bin/env python3
"""
Script khởi động service đồng bộ với máy siêu âm Voluson E10
Chạy độc lập hoặc tích hợp vào ứng dụng Flask chính
"""

import sys
import os
import time
import signal
import logging
from voluson_sync_service import get_voluson_sync_service

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voluson_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class VolusonSyncDaemon:
    """Daemon service cho đồng bộ Voluson E10"""
    
    def __init__(self):
        self.sync_service = get_voluson_sync_service()
        self.running = False
        
    def start(self):
        """Khởi động daemon"""
        logger.info("Đang khởi động Voluson Sync Daemon...")
        
        # Thiết lập signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Khởi động service đồng bộ
            self.sync_service.start_sync_service()
            self.running = True
            
            logger.info("Voluson Sync Daemon đã khởi động thành công")
            logger.info(f"Cấu hình: IP={self.sync_service.voluson_ip}, Port={self.sync_service.voluson_port}")
            
            # Vòng lặp chính
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Nhận tín hiệu dừng từ bàn phím")
        except Exception as e:
            logger.error(f"Lỗi trong daemon: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Dừng daemon"""
        if self.running:
            logger.info("Đang dừng Voluson Sync Daemon...")
            self.sync_service.stop_sync_service()
            self.running = False
            logger.info("Voluson Sync Daemon đã dừng")
    
    def _signal_handler(self, signum, frame):
        """Xử lý tín hiệu dừng"""
        logger.info(f"Nhận tín hiệu {signum}, đang dừng...")
        self.running = False

def main():
    """Hàm main"""
    print("=" * 60)
    print("    VOLUSON E10 SYNC DAEMON")
    print("    Phòng khám chuyên khoa Phụ Sản Đại Anh")
    print("=" * 60)
    
    # Kiểm tra file cấu hình
    if not os.path.exists('voluson_config.json'):
        print("Cảnh báo: File cấu hình voluson_config.json không tồn tại")
        print("Sẽ tạo file cấu hình mặc định...")
    
    # Kiểm tra database
    if not os.path.exists('clinic.db'):
        print("Lỗi: File database clinic.db không tồn tại")
        print("Vui lòng chạy ứng dụng Flask trước để tạo database")
        sys.exit(1)
    
    # Khởi động daemon
    daemon = VolusonSyncDaemon()
    
    try:
        daemon.start()
    except Exception as e:
        logger.error(f"Lỗi khởi động daemon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
