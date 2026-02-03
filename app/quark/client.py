"""Quark cloud drive client for saving shared links."""

import httpx
import logging
import re
from urllib.parse import urlencode

from app.config import QUARK_COOKIE

logger = logging.getLogger(__name__)


class QuarkClient:
    def __init__(self, bx_ua: str = "", bx_umidtoken: str = ""):
        self.cookie = QUARK_COOKIE
        self.base_url = "https://drive-h.quark.cn"
        self.share_url = "https://pan.quark.cn"
        self.headers = {
            "Content-Type": "application/json",
            "Origin": "https://pan.quark.cn",
            "Referer": "https://pan.quark.cn/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Cookie": self.cookie,
            "bx-ua": bx_ua,
            "bx-umidtoken": bx_umidtoken,
            "bx_et": "default_not_fun",
        }

    async def get_stoken(self, share_id: str) -> str:
        endpoint = "/1/clouddrive/share/sharepage/token"

        params = {
            "pr": "ucpro",
            "fr": "pc",
            "uc_param_str": "",
            "__dt": "597",
            "__t": str(int(__import__("time").time() * 1000)),
        }

        payload = {
            "pwd_id": share_id,
            "passcode": "",
            "support_visit_limit_private_share": "true",
        }

        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url, params=params, headers=self.headers, json=payload
                )
                response.raise_for_status()

                data = response.json()

                if data.get("status") == 200 and data.get("data", {}).get("stoken"):
                    stoken = data["data"]["stoken"]
                    logger.info(f"[QUARK] got stoken for share_id={share_id}")
                    return stoken
                else:
                    logger.error(f"[QUARK] failed to get stoken: {data}")
                    return ""

        except Exception as e:
            logger.error(f"[QUARK] exception getting stoken: {str(e)}")
            return ""

        except Exception as e:
            logger.error(
                f"[QUARK] failed to get stoken for share_id={share_id}: {str(e)}"
            )
            return ""

    async def save_share(self, share_id: str, to_pdir_fid: str = "0") -> dict:
        stoken = await self.get_stoken(share_id)

        if not stoken:
            return {
                "success": False,
                "error": "Failed to get stoken",
                "share_id": share_id,
            }

        endpoint = "/1/clouddrive/share/sharepage/save"

        params = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}

        payload = {
            "pwd_id": share_id,
            "stoken": stoken,
            "pdir_fid": "0",
            "to_pdir_fid": to_pdir_fid,
            "pdir_save_all": True,
            "scene": "link",
        }

        url = f"{self.base_url}{endpoint}?{urlencode(params)}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()

                data = response.json()

                if data.get("code") == 0:
                    logger.info(f"[QUARK] saved share_id={share_id}, task_id={data['data'].get('task_id')}")
                    return {
                        "success": True,
                        "task_id": data["data"].get("task_id"),
                        "share_id": share_id
                    }
                else:
                    error_msg = data.get("message", "Unknown error")
                    error_code = data.get("code", -1)

                    logger.error(f"[QUARK] failed for share_id={share_id}: {error_msg}")

                    is_cookie_expired = (
                        error_code == 401 or
                        error_code == 403 or
                        "登录" in error_msg or
                        "cookie" in error_msg.lower() or
                        "token" in error_msg.lower() and "invalid" in error_msg.lower()
                    )

                    return {
                        "success": False,
                        "error": error_msg,
                        "share_id": share_id,
                        "cookie_expired": is_cookie_expired
                    }
                else:
                    error_msg = data.get("message", "Unknown error")
                    logger.error(f"[QUARK] failed for share_id={share_id}: {error_msg}")
                    return {"success": False, "error": error_msg, "share_id": share_id}

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[QUARK] HTTP error for share_id={share_id}: {e.response.status_code}"
            )
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "share_id": share_id,
            }
        except Exception as e:
            logger.error(f"[QUARK] exception for share_id={share_id}: {str(e)}")
            return {"success": False, "error": str(e), "share_id": share_id}
