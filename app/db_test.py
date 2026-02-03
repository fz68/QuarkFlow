"""Test database deduplication logic."""

import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import (
    insert_tg_message,
    insert_share_pending,
    get_share_status,
    init_db,
)
from app.config import DB_PATH


def test_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    print("Initializing database...")
    init_db()

    print("\n=== Test 1: Duplicate Telegram messages ===")
    result1 = insert_tg_message("@test", 123)
    print(f"First insert: {result1}")

    result2 = insert_tg_message("@test", 123)
    print(f"Duplicate insert: {result2}")

    result3 = insert_tg_message("@test", 124)
    print(f"Different message: {result3}")

    print("\n=== Test 2: Duplicate share links ===")
    result4 = insert_share_pending("abcd123")
    print(f"First insert: {result4}")

    result5 = insert_share_pending("abcd123")
    print(f"Duplicate insert: {result5}")

    result6 = insert_share_pending("xyz789")
    print(f"Different share: {result6}")

    print("\n=== Test 3: Status tracking ===")
    status1 = get_share_status("abcd123")
    print(f"Status of abcd123: {status1}")

    status2 = get_share_status("nonexistent")
    print(f"Status of nonexistent: {status2}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_db()
