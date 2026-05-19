import requests
import sqlite3

CLOUD_URL = "https://phong-kham-booking.onrender.com/api/pending-appointments"

conn = sqlite3.connect("clinic.db")
cursor = conn.cursor()

try:
    response = requests.get(CLOUD_URL, timeout=20)

    data = response.json()

    print("Cloud appointments:", len(data))

    for item in data:

        patient_name = item.get("patient_name", "")
        phone = item.get("phone", "")
        appointment_date = item.get("appointment_date", "")
        service = item.get("service", "")

        cursor.execute("""
            INSERT INTO appointments
            (
                patient_name,
                phone,
                appointment_date,
                service
            )
            VALUES (?, ?, ?, ?)
        """, (
            patient_name,
            phone,
            appointment_date,
            service
        ))

    conn.commit()

    print("Sync completed")

except Exception as e:
    print("SYNC ERROR:", e)

finally:
    conn.close()