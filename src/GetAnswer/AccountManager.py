import logging
import time
import uuid
import os
import json
from datetime import timedelta
from typing import Optional

import requests
import jwt

from src.GetAnswer.XinjiaoyuEncryptioner import XinjiaoyuEncryptioner
from src.GetAnswer.config import BASE_URL

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class AccountManager:
    AUTH_URL = f"{BASE_URL}/api/v3/server_system/auth/login"
    DATA_FILE = "user_data.json"  # 保存用户数据的文件
    MAX_RETRIES = 3  # 最大重试次数
    ENCRYPTION_KEY = "6f0c5ba452b24fa28989e9524d77407a"

    def __init__(self):
        self.user_data = {}
        self.public_user_data = {}
        self.HEADERS = {}
        self.studentId = {}
        self.load_user_data()

    def save_user_data(self, data: dict) -> None:
        """保存用户数据到文件"""
        try:
            with open(self.DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            logging.info("用户数据保存成功")
        except Exception as e:
            logging.error(f"保存用户数据失败: {e}")

    def load_user_data(self) -> None:
        """从文件加载用户数据"""
        if not os.path.exists(self.DATA_FILE):
            logging.warning("用户数据文件不存在")
            return

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.user_data = data.get("user_info", {})
                self.public_user_data = data.get("tokens", {})
                self.HEADERS = data.get("headers", {})
                self.studentId = data.get("user_info", {}).get("school", {}).get("studentId", {})
            logging.info("用户数据加载成功")
        except Exception as e:
            logging.error(f"加载用户数据失败: {e}")

    def login(self, username: str, password: str) -> bool:
        """用户登录主方法，如果 Token 未过期则直接返回成功"""
        if self.is_token_valid(self.public_user_data.get("token")):
            return True

        logging.info("Token 无效或不存在，正在执行登录")
        try:
            encoded_username = self._encrypt_data(username)
            encoded_password = self._encrypt_data(password)
            headers, login_data = self._prepare_login_request(encoded_username, encoded_password)
            response = self._make_request(self.AUTH_URL, headers, login_data)

            if response and response.get("code") == 200:
                self._process_login_response(response, headers)
                logging.info("登录成功")
                return True

            logging.error(f"登录失败: {response.get('message', '未知错误') if response else '无响应'}")
        except Exception as e:
            logging.error(f"登录过程中发生错误: {e}")
        return False

    @staticmethod
    def is_token_valid(token: Optional[str]) -> bool:
        """检查 Token 是否有效"""
        if not token:
            return False
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            exp = decoded_token.get("exp", 0)
            remaining_time = exp - int(time.time())
            if remaining_time > 0:
                AccountManager._log_remaining_time(remaining_time)
                return True
            logging.warning("Token 已过期")
        except jwt.DecodeError:
            logging.error("Token 解码失败")
        return False

    @staticmethod
    def _log_remaining_time(remaining_time: int) -> None:
        """记录 Token 剩余时间"""
        remaining_td = timedelta(seconds=remaining_time)
        days, seconds = divmod(remaining_td.total_seconds(), 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        logging.info(f"Token 有效，剩余时间：{int(days)} 天 {int(hours)} 小时 {int(minutes)} 分钟 {int(seconds)} 秒")

    def _encrypt_data(self, data: str) -> str:
        """对数据进行加密"""
        return XinjiaoyuEncryptioner.encrypt(data, self.ENCRYPTION_KEY)

    @staticmethod
    def _prepare_login_request(username: str, password: str) -> tuple[dict, dict]:
        """准备登录请求所需数据"""
        t_val = str(int(time.time() * 1000))
        client_session_val = uuid.uuid4().hex
        encrypt_val = XinjiaoyuEncryptioner.get_md5(t_val, client_session_val)
        headers = {
            "client": "front",
            "clientSession": client_session_val,
            "Content-Type": "application/json",
            "User-Agent": "okhttp/4.9.3",
            "encrypt": encrypt_val,
            "t": t_val,
        }
        login_data = {"password": password, "t": int(t_val), "username": username}
        return headers, login_data

    def _process_login_response(self, response: dict, headers: dict) -> None:
        """处理登录响应数据"""
        tokens = response["data"]
        self.user_data = response.get("data", {}).get("info", {})
        self.public_user_data = {"accessToken": tokens.get("accessToken"), "token": tokens.get("token")}
        self.HEADERS.update(headers)
        self.HEADERS.update({
            "Authorization": f'JBY {self.public_user_data["token"]}',
            "accessToken": self.public_user_data["accessToken"],
        })
        self.save_user_data({"user_info": self.user_data, "tokens": self.public_user_data, "headers": self.HEADERS})

    def get_headers(self) -> dict | None:
        """
        获取保存的 headers
        """
        if not self.HEADERS:
            logging.warning("未找到 headers，请先登录")
        return self.HEADERS

    def get_studentId(self) -> dict | None:
        """
        获取保存的 studentId
        """
        if not self.studentId:
            logging.warning("未找到 studentId，请先登录")
        return self.studentId

    def _make_request(self, url: str, headers: dict, json_data: dict) -> Optional[dict]:
        """通用 POST 请求方法，带重试机制"""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = requests.post(url, headers=headers, json=json_data, timeout=10)
                if response.ok:
                    logging.info(f"请求成功 (尝试 {attempt}/{self.MAX_RETRIES})")
                    return response.json()
                logging.error(f"请求失败 (尝试 {attempt}/{self.MAX_RETRIES}): {response.text}")
            except requests.RequestException as e:
                logging.error(f"网络错误 (尝试 {attempt}/{self.MAX_RETRIES}): {e}")
            time.sleep(1)
        logging.error("达到最大重试次数，请求失败")
        return None
