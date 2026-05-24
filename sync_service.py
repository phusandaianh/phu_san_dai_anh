import json
import os
import sqlite3
import time

import requests

_BASE = os.path.dirname(os.path.abspath(__file__))
LOCAL_DB = os.environ.get("CLINIC_DB", os.path.join(_BASE, "clinic.db"))
_REMOTE = (os.environ.get("SYNC_REMOTE_URL") or "https://phusandaianh.io.vn").rstrip("/")
CLOUD_API = f"{_REMOTE}/api/sync/appointment"
SYNC_TOKEN = os.environ.get("SYNC_TOKEN", "phongkham_2026_secure_sync")


def get_pending_sync():
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM sync_queue
        WHERE status='pending'
        ORDER BY created_at ASC
        LIMIT 20
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def mark_done(sync_id):
    conn = sqlite3.connect(LOCAL_DB)

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sync_queue
        SET status='done',
            processed_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (sync_id,))

    conn.commit()
    conn.close()


def mark_failed(sync_id):
    conn = sqlite3.connect(LOCAL_DB)

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sync_queue
        SET retry_count = retry_count + 1
        WHERE id=?
    """, (sync_id,))

    conn.commit()
    conn.close()


def sync_to_cloud(row):

    data = json.loads(row["payload"])

    if row["table_name"] == "appointment":

        payload = {
            "token": SYNC_TOKEN,
            "table_name": row["table_name"],
            "record_id": row["record_id"],
            "action": row["action"],
            "payload": data,
        }

        response = requests.post(
            CLOUD_API,
            json=payload,
            timeout=20,
        )

        return response.status_code == 200

    elif row["table_name"] == "work_schedule":

        if row["action"] == "insert":

            response = requests.post(
                f"{_REMOTE}/api/sync/work_schedule",
                json=data,
                timeout=20,
            )

        elif row["action"] == "update":

            response = requests.put(
                f"{_REMOTE}/api/sync/work_schedule",
                json=data,
                timeout=20,
            )

        elif row["action"] == "delete":

            response = requests.delete(
                f"{_REMOTE}/api/sync/work_schedule",
                json=data,
                timeout=20,
            )

        else:
            return False

        return response.status_code == 200

    return False


def run_sync():

    while True:

        try:

            rows = get_pending_sync()

            if rows:

                print(f"Found {len(rows)} pending sync items")

            for row in rows:

                try:

                    ok = sync_to_cloud(row)

                    if ok:
                        mark_done(row["id"])
                        print("SYNC OK", row["record_id"])

                    else:
                        mark_failed(row["id"])
                        print("SYNC FAILED", row["record_id"])

                except Exception as e:

                    mark_failed(row["id"])

                    print("ERROR:", e)

        except Exception as e:

            print("MAIN LOOP ERROR:", e)

        time.sleep(5)


if __name__ == "__main__":
    run_sync()
