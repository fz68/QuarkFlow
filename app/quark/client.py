"""Quark cloud drive client for saving shared links (Mobile API)."""

import httpx
import logging
import re
from urllib.parse import urlencode

from app.config import QUARK_COOKIE

logger = logging.getLogger(__name__)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)
httpx_logger.propagate = False


class QuarkClient:
    def __init__(self):
        self.cookie = QUARK_COOKIE
        self.base_url_pc = "https://drive-h.quark.cn"
        self.base_url_app = "https://drive-m.quark.cn"
        self.share_url = "https://pan.quark.cn"

        # Extract mparam from cookie (kps, sign, vcode)
        self.mparam = self._extract_mparam_from_cookie()

        self.headers = {
            "Content-Type": "application/json",
            "Origin": "https://pan.quark.cn",
            "Referer": "https://pan.quark.cn/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Cookie": self.cookie,
        }

    def reload_cookie(self):
        """Reload cookie from config and update headers."""
        from app.config import QUARK_COOKIE

        if QUARK_COOKIE != self.cookie:
            logger.info("[QUARK] Cookie changed, reloading...")
            self.cookie = QUARK_COOKIE
            self.mparam = self._extract_mparam_from_cookie()
            self.headers["Cookie"] = self.cookie
            logger.info("[QUARK] Cookie reloaded successfully")

    def _extract_mparam_from_cookie(self) -> dict:
        """Extract kps, sign, vcode from Quark cookie."""
        mparam = {}

        # Try to extract kps, sign, vcode from cookie
        kps_match = re.search(r"(?<!\w)kps=([a-zA-Z0-9%+/=]+)[;&]?", self.cookie)
        sign_match = re.search(r"(?<!\w)sign=([a-zA-Z0-9%+/=]+)[;&]?", self.cookie)
        vcode_match = re.search(r"(?<!\w)vcode=([a-zA-Z0-9%+/=]+)[;&]?", self.cookie)

        if kps_match and sign_match and vcode_match:
            mparam = {
                "kps": kps_match.group(1).replace("%25", "%"),
                "sign": sign_match.group(1).replace("%25", "%"),
                "vcode": vcode_match.group(1).replace("%25", "%"),
            }
            logger.info("[QUARK] Extracted mparam from cookie")
        else:
            logger.warning("[QUARK] No mparam found in cookie, will use PC API")

        return mparam

    async def get_stoken(self, share_id: str) -> str:
        # Use mobile API if mparam is available, otherwise use PC API
        if self.mparam:
            base_url = self.base_url_app
        else:
            base_url = self.base_url_pc

        endpoint = "/1/clouddrive/share/sharepage/token"

        params = {
            "pr": "ucpro",
            "fr": "pc",
            "uc_param_str": "",
            "__dt": "597",
            "__t": str(int(__import__("time").time() * 1000)),
        }

        # Add mobile-specific parameters if using mobile API
        if self.mparam:
            params.update(
                {
                    "kps": self.mparam.get("kps"),
                    "sign": self.mparam.get("sign"),
                    "vcode": self.mparam.get("vcode"),
                    "device_model": "M2011K2C",
                    "fr": "android",
                    "pf": "3300",
                }
            )

        payload = {
            "pwd_id": share_id,
            "passcode": "",
            "support_visit_limit_private_share": "true",
        }

        url = f"{base_url}{endpoint}"

        try:
            import warnings

            warnings.filterwarnings("ignore", category=Warning)

            event_hooks = {"request": [], "response": []}

            async with httpx.AsyncClient(
                timeout=30.0, event_hooks=event_hooks
            ) as client:
                response = await client.post(
                    url, params=params, headers=self.headers, json=payload
                )
                response.raise_for_status()

                # 手动解码避免 ASCII 编码错误
                import json

                text = response.content.decode("utf-8", errors="ignore")
                data = json.loads(text)

                if data.get("status") == 200 and data.get("data", {}).get("stoken"):
                    stoken = data["data"]["stoken"]
                    logger.info(f"[QUARK] got stoken for share_id={share_id}")
                    return stoken
                else:
                    logger.error(f"[QUARK] failed to get stoken: {data}")
                    return ""

        except Exception as e:
            import traceback

            logger.error("[QUARK] exception getting stoken")
            logger.error(f"[QUARK] error type: {type(e).__name__}")
            # 不记录异常详情，避免编码错误
            return ""

    async def save_share(self, share_id: str, to_pdir_fid: str = "0") -> dict:
        stoken = await self.get_stoken(share_id)

        if not stoken:
            return {
                "success": False,
                "error": "Failed to get stoken",
                "share_id": share_id,
            }

        # Use mobile API if mparam is available, otherwise use PC API
        if self.mparam:
            base_url = self.base_url_app
        else:
            base_url = self.base_url_pc

        endpoint = "/1/clouddrive/share/sharepage/save"

        params = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}

        # Add mobile-specific parameters if using mobile API
        if self.mparam:
            params.update(
                {
                    "kps": self.mparam.get("kps"),
                    "sign": self.mparam.get("sign"),
                    "vcode": self.mparam.get("vcode"),
                    "device_model": "M2011K2C",
                    "fr": "android",
                    "pf": "3300",
                }
            )

        payload = {
            "pwd_id": share_id,
            "stoken": stoken,
            "pdir_fid": "0",
            "to_pdir_fid": to_pdir_fid,
            "pdir_save_all": True,
            "scene": "link",
        }

        url = f"{base_url}{endpoint}?{urlencode(params)}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()

                import json

                text = response.content.decode("utf-8", errors="ignore")
                data = json.loads(text)

                if data.get("code") == 0:
                    logger.info(
                        f"[QUARK] saved share_id={share_id}, task_id={data['data'].get('task_id')}"
                    )
                    return {
                        "success": True,
                        "task_id": data["data"].get("task_id"),
                        "share_id": share_id,
                    }
                else:
                    error_msg = data.get("message", "Unknown error")
                    error_code = data.get("code", -1)

                    logger.error(f"[QUARK] failed for share_id={share_id}: {error_msg}")

                    is_cookie_expired = (
                        error_code == 401
                        or error_code == 403
                        or "登录" in error_msg
                        or "cookie" in error_msg.lower()
                        or "token" in error_msg.lower()
                        and "invalid" in error_msg.lower()
                    )

                    return {
                        "success": False,
                        "error": error_msg,
                        "share_id": share_id,
                        "cookie_expired": is_cookie_expired,
                    }

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
            logger.error(f"[QUARK] exception for share_id={share_id}")
            return {
                "success": False,
                "error": "HTTP request failed",
                "share_id": share_id,
            }

    async def get_file_list(self, pdir_fid: str = "0") -> dict:
        endpoint = "/1/clouddrive/file/sort"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "uc_param_str": "",
            "pdir_fid": pdir_fid,
            "_page": "1",
            "_size": "100",
            "__dt": "300",
            "__t": str(int(__import__("time").time() * 1000)),
        }

        url = f"{self.base_url_pc}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self.headers)
                response.raise_for_status()

                import json

                text = response.content.decode("utf-8", errors="ignore")
                data = json.loads(text)

                if data.get("status") == 200 and data.get("data", {}).get("list"):
                    return {"success": True, "files": data["data"]["list"]}
                else:
                    return {
                        "success": False,
                        "error": data.get("message", "Unknown error"),
                    }

        except Exception as e:
            logger.error("[QUARK] exception getting file list")
            return {"success": False, "error": "HTTP request failed"}

    async def find_folder_by_name(self, folder_name: str, pdir_fid: str = "0") -> str:
        result = await self.get_file_list(pdir_fid)

        if not result.get("success"):
            return ""

        for file in result.get("files", []):
            if file.get("file_name") == folder_name and file.get("dir") == True:
                return file.get("fid")

        return ""
