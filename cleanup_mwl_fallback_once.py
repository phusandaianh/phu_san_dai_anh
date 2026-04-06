import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "mwl.db"


def main():
    if not DB_PATH.exists():
        print(f"mwl.db not found: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT id, accession_number
        FROM worklist_entries
        WHERE accession_number IS NOT NULL
        ORDER BY id
        """
    ).fetchall()

    accessions = {acc for _id, acc in rows if acc}
    to_delete_ids = []

    for row_id, acc in rows:
        if not acc:
            continue
        if "-svc" in acc:
            continue
        # Fallback accession: ACC000123
        # Delete only if at least one service-specific accession exists: ACC000123-svcX
        has_specific = any(
            other.startswith(acc + "-svc") for other in accessions
        )
        if has_specific:
            to_delete_ids.append(row_id)

    deleted = 0
    if to_delete_ids:
        placeholders = ",".join(["?"] * len(to_delete_ids))
        cur.execute(
            f"DELETE FROM worklist_entries WHERE id IN ({placeholders})",
            to_delete_ids,
        )
        deleted = cur.rowcount
        conn.commit()

    remaining = cur.execute("SELECT COUNT(1) FROM worklist_entries").fetchone()[0]
    conn.close()

    print(f"Deleted fallback rows: {deleted}")
    print(f"Remaining rows: {remaining}")


if __name__ == "__main__":
    main()
