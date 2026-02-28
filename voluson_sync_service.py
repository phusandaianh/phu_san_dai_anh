"""
Service đồng bộ dữ liệu bệnh nhân với máy siêu âm Voluson E10
Sử dụng DICOM Worklist để gửi thông tin bệnh nhân đến máy siêu âm
"""

import pydicom
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import ModalityWorklistInformationFind as MWLFind
import logging
from datetime import datetime, timedelta
import json
import threading
import time
from typing import List, Dict, Optional
import sqlite3
import os

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VolusonSyncService:
    """Service đồng bộ với máy siêu âm Voluson E10"""
    
    def __init__(self, config_file: str = "voluson_config.json"):
        """
        Khởi tạo service đồng bộ
        
        Args:
            config_file: Đường dẫn file cấu hình
        """
        self.config = self._load_config(config_file)
        self.db_path = self.config.get('database_path', 'clinic.db')
        self.sync_enabled = self.config.get('sync_enabled', True)
        self.voluson_ip = self.config.get('voluson_ip', '192.168.1.100')
        self.voluson_port = self.config.get('voluson_port', 104)
        self.ae_title = self.config.get('ae_title', 'CLINIC_SYSTEM')
        self.voluson_ae_title = self.config.get('voluson_ae_title', 'VOLUSON_E10')
        
        # Thread cho đồng bộ định kỳ
        self.sync_thread = None
        self.sync_running = False
        
    def _load_config(self, config_file: str) -> Dict:
        """Tải cấu hình từ file JSON"""
        default_config = {
            "sync_enabled": True,
            "voluson_ip": "192.168.1.100",
            "voluson_port": 104,
            "ae_title": "CLINIC_SYSTEM",
            "voluson_ae_title": "VOLUSON_E10",
            "database_path": "clinic.db",
            "sync_interval": 300,  # 5 phút
            "retry_attempts": 3,
            "retry_delay": 10
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Không thể tải cấu hình từ {config_file}: {e}")
        else:
            # Tạo file cấu hình mặc định
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"Đã tạo file cấu hình mặc định: {config_file}")
            
        return default_config
    
    def start_sync_service(self):
        """Khởi động service đồng bộ định kỳ"""
        if not self.sync_enabled:
            logger.info("Đồng bộ với Voluson E10 đã bị tắt")
            return
            
        if self.sync_thread and self.sync_thread.is_alive():
            logger.warning("Service đồng bộ đã đang chạy")
            return
            
        self.sync_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info("Đã khởi động service đồng bộ với Voluson E10")
    
    def stop_sync_service(self):
        """Dừng service đồng bộ"""
        self.sync_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("Đã dừng service đồng bộ với Voluson E10")
    
    def _sync_loop(self):
        """Vòng lặp đồng bộ định kỳ"""
        while self.sync_running:
            try:
                self.sync_pending_appointments()
                time.sleep(self.config.get('sync_interval', 300))
            except Exception as e:
                logger.error(f"Lỗi trong vòng lặp đồng bộ: {e}")
                time.sleep(60)  # Chờ 1 phút trước khi thử lại
    
    def sync_pending_appointments(self):
        """Đồng bộ các cuộc hẹn chưa được gửi đến Voluson"""
        try:
            # Lấy danh sách cuộc hẹn chưa đồng bộ
            appointments = self._get_pending_appointments()
            
            if not appointments:
                logger.debug("Không có cuộc hẹn nào cần đồng bộ")
                return
                
            logger.info(f"Tìm thấy {len(appointments)} cuộc hẹn cần đồng bộ")
            
            # Gửi từng cuộc hẹn đến Voluson
            for appointment in appointments:
                try:
                    self._send_appointment_to_voluson(appointment)
                    self._mark_appointment_synced(appointment['id'])
                    logger.info(f"Đã đồng bộ cuộc hẹn ID {appointment['id']}")
                except Exception as e:
                    logger.error(f"Lỗi khi đồng bộ cuộc hẹn ID {appointment['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Lỗi khi đồng bộ cuộc hẹn: {e}")
    
    def _get_pending_appointments(self) -> List[Dict]:
        """Lấy danh sách cuộc hẹn chưa được đồng bộ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Lấy cuộc hẹn trong 7 ngày tới chưa được đồng bộ
            query = """
            SELECT 
                a.id,
                a.appointment_date,
                a.service_type,
                a.doctor_name,
                p.name,
                p.phone,
                p.date_of_birth,
                p.address
            FROM appointment a
            JOIN patient p ON a.patient_id = p.id
            WHERE a.appointment_date >= datetime('now')
            AND a.appointment_date <= datetime('now', '+7 days')
            AND a.voluson_synced = 0
            ORDER BY a.appointment_date
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                appointments.append({
                    'id': row[0],
                    'appointment_date': row[1],
                    'service_type': row[2],
                    'doctor_name': row[3],
                    'patient_name': row[4],
                    'patient_phone': row[5],
                    'patient_dob': row[6],
                    'patient_address': row[7]
                })
            
            conn.close()
            return appointments
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách cuộc hẹn: {e}")
            return []
    
    def _send_appointment_to_voluson(self, appointment: Dict):
        """Gửi thông tin cuộc hẹn đến máy siêu âm Voluson E10"""
        try:
            # Tạo DICOM dataset cho worklist
            dataset = self._create_worklist_dataset(appointment)
            
            # Kết nối và gửi đến Voluson
            ae = AE(ae_title=self.ae_title)
            ae.add_requested_context(MWLFind)
            
            # Kết nối đến Voluson E10
            assoc = ae.associate(self.voluson_ip, self.voluson_port, ae_title=self.voluson_ae_title)
            
            if assoc.is_established:
                logger.info(f"Đã kết nối đến Voluson E10 tại {self.voluson_ip}:{self.voluson_port}")
                
                # Gửi worklist item
                response = assoc.send_c_find(dataset, MWLFind)
                
                if response.Status == 0x0000:  # Success
                    logger.info(f"Đã gửi thành công cuộc hẹn {appointment['id']} đến Voluson")
                else:
                    logger.warning(f"Voluson trả về status: {response.Status}")
                
                assoc.release()
            else:
                logger.error(f"Không thể kết nối đến Voluson E10: {assoc.is_established}")
                
        except Exception as e:
            logger.error(f"Lỗi khi gửi cuộc hẹn đến Voluson: {e}")
            raise
    
    def _create_worklist_dataset(self, appointment: Dict) -> Dataset:
        """Tạo DICOM dataset cho worklist item"""
        dataset = Dataset()
        
        # Thông tin cơ bản
        dataset.ScheduledProcedureStepSequence = [Dataset()]
        sps = dataset.ScheduledProcedureStepSequence[0]
        
        # Thông tin bệnh nhân
        dataset.PatientName = appointment['patient_name']
        dataset.PatientID = f"PAT_{appointment['id']}"
        dataset.PatientBirthDate = appointment['patient_dob'].replace('-', '')
        dataset.PatientSex = 'O'  # Unknown, có thể cải thiện sau
        
        # Thông tin cuộc hẹn
        appointment_dt = datetime.fromisoformat(appointment['appointment_date'].replace('Z', '+00:00'))
        dataset.ScheduledProcedureStepStartDate = appointment_dt.strftime('%Y%m%d')
        dataset.ScheduledProcedureStepStartTime = appointment_dt.strftime('%H%M%S')
        
        # Thông tin dịch vụ
        sps.Modality = 'US'  # Ultrasound
        sps.ScheduledProcedureStepDescription = appointment['service_type']
        sps.ScheduledProcedureStepID = f"SP_{appointment['id']}"
        
        # Thông tin bác sĩ
        if appointment['doctor_name']:
            dataset.RequestingPhysician = appointment['doctor_name']
        
        # Thông tin cơ sở y tế
        dataset.InstitutionName = "Phòng khám chuyên khoa Phụ Sản Đại Anh"
        dataset.InstitutionAddress = "TDP Quán Trắng - Tân An - Bắc Ninh"
        
        return dataset
    
    def add_appointment_to_worklist(self, appointment_id: int, service_name: str, modality: str = 'US'):
        """
        Đánh dấu appointment đã sẵn sàng trong worklist
        (Voluson sẽ tự động query worklist từ DICOM MWL Server)
        
        Args:
            appointment_id: ID của appointment
            service_name: Tên dịch vụ siêu âm
            modality: Loại thiết bị (mặc định 'US' cho ultrasound)
        
        Returns:
            bool: True nếu thành công
        """
        try:
            # Chỉ cần đánh dấu appointment đã sẵn sàng trong worklist
            # Voluson sẽ tự động query từ DICOM MWL Server
            self._mark_appointment_synced(appointment_id)
            logger.info(f"Da danh dau appointment {appointment_id} san sang trong worklist (Voluson se tu dong query)")
            return True
                
        except Exception as e:
            logger.error(f"Loi khi danh dau appointment trong worklist: {e}")
            return False

    def test_connection(self, ip: str = None, port: int = None):
        """
        Test kết nối với máy Voluson E10
        
        Args:
            ip: IP address của máy Voluson (optional)
            port: Port của máy Voluson (optional)
        
        Returns:
            bool: True nếu kết nối thành công, False nếu thất bại
        """
        try:
            test_ip = ip or self.voluson_ip
            test_port = port or self.voluson_port
            
            logger.info(f"Testing connection to Voluson E10 at {test_ip}:{test_port}")
            
            # Tạo AE để test kết nối
            ae = AE(ae_title=self.ae_title)
            ae.add_requested_context(MWLFind)
            
            # Thử kết nối
            assoc = ae.associate(test_ip, test_port, ae_title=self.voluson_ae_title)
            
            if assoc.is_established:
                logger.info("Connection test successful")
                assoc.release()
                return True
            else:
                logger.error("Connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return False

    def _mark_appointment_synced(self, appointment_id: int):
        """Đánh dấu cuộc hẹn đã được đồng bộ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Kiểm tra xem cột voluson_synced đã tồn tại chưa
            cursor.execute("PRAGMA table_info(appointment)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'voluson_synced' not in columns:
                # Thêm cột voluson_synced nếu chưa có
                cursor.execute("""
                    ALTER TABLE appointment ADD COLUMN voluson_synced INTEGER DEFAULT 0
                """)
            
            # Cập nhật trạng thái đồng bộ
            cursor.execute("""
                UPDATE appointment 
                SET voluson_synced = 1, voluson_sync_time = datetime('now')
                WHERE id = ?
            """, (appointment_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Lỗi khi đánh dấu cuộc hẹn đã đồng bộ: {e}")
    
    def sync_single_appointment(self, appointment_id: int) -> bool:
        """Đồng bộ một cuộc hẹn cụ thể"""
        try:
            # Lấy thông tin cuộc hẹn
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
            SELECT 
                a.id,
                a.appointment_date,
                a.service_type,
                a.doctor_name,
                p.name,
                p.phone,
                p.date_of_birth,
                p.address
            FROM appointment a
            JOIN patient p ON a.patient_id = p.id
            WHERE a.id = ?
            """
            
            cursor.execute(query, (appointment_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                logger.error(f"Không tìm thấy cuộc hẹn ID {appointment_id}")
                return False
            
            appointment = {
                'id': row[0],
                'appointment_date': row[1],
                'service_type': row[2],
                'doctor_name': row[3],
                'patient_name': row[4],
                'patient_phone': row[5],
                'patient_dob': row[6],
                'patient_address': row[7]
            }
            
            # Gửi đến Voluson
            self._send_appointment_to_voluson(appointment)
            self._mark_appointment_synced(appointment_id)
            
            logger.info(f"Đã đồng bộ thành công cuộc hẹn ID {appointment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi đồng bộ cuộc hẹn ID {appointment_id}: {e}")
            return False
    
    def get_sync_status(self) -> Dict:
        """Lấy trạng thái đồng bộ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Thống kê đồng bộ
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN voluson_synced = 1 THEN 1 ELSE 0 END) as synced,
                    SUM(CASE WHEN voluson_synced = 0 THEN 1 ELSE 0 END) as pending
                FROM appointment 
                WHERE appointment_date >= datetime('now')
                AND appointment_date <= datetime('now', '+7 days')
            """)
            
            stats = cursor.fetchone()
            conn.close()
            
            return {
                'sync_enabled': self.sync_enabled,
                'voluson_ip': self.voluson_ip,
                'voluson_port': self.voluson_port,
                'total_appointments': stats[0] or 0,
                'synced_appointments': stats[1] or 0,
                'pending_appointments': stats[2] or 0,
                'sync_running': self.sync_running
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy trạng thái đồng bộ: {e}")
            return {'error': str(e)}

# Singleton instance
_voluson_sync_service = None

def get_voluson_sync_service() -> VolusonSyncService:
    """Lấy instance singleton của VolusonSyncService"""
    global _voluson_sync_service
    if _voluson_sync_service is None:
        _voluson_sync_service = VolusonSyncService()
    return _voluson_sync_service
