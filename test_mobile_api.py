"""Test mobile API for Quark auto-save."""

import asyncio
import sys
from app.quark.client import QuarkClient


async def test_mobile_api():
    """Test the mobile API with a share link."""

    share_id = "05b8f8dbb297"

    print(f"[TEST] Testing mobile API with share_id: {share_id}\n")

    client = QuarkClient()

    if client.mparam:
        print(f"[TEST] ✓ Mobile API available (mparam found)")
        print(f"[TEST]   - kps: {client.mparam.get('kps', '')[:20]}...")
        print(f"[TEST]   - sign: {client.mparam.get('sign', '')[:20]}...")
        print(f"[TEST]   - vcode: {client.mparam.get('vcode', '')[:20]}...")
    else:
        print(f"[TEST] ⚠ Mobile API not available (mparam not found)")
        print(f"[TEST]   Will use PC API as fallback\n")

    print(f"[TEST] Getting stoken...\n")
    stoken = await client.get_stoken(share_id)

    if stoken:
        print(f"[TEST] ✓ Successfully got stoken: {stoken[:30]}...\n")

        print(f"[TEST] Saving share to Quark...\n")
        result = await client.save_share(share_id)

        if result.get("success"):
            print(f"[TEST] ✓ Successfully saved!")
            print(f"[TEST]   - Share ID: {result.get('share_id')}")
            print(f"[TEST]   - Task ID: {result.get('task_id')}")
        else:
            print(f"[TEST] ✗ Failed to save")
            print(f"[TEST]   - Error: {result.get('error')}")
            if result.get("cookie_expired"):
                print(f"[TEST]   - Cookie expired: {result.get('cookie_expired')}")
    else:
        print(f"[TEST] ✗ Failed to get stoken")


if __name__ == "__main__":
    asyncio.run(test_mobile_api())
