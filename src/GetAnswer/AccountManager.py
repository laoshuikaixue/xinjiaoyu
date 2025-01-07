import sys
import time
import uuid
import os
import json
from datetime import timedelta
from typing import Optional

import requests
import jwt

from src.GetAnswer.XinjiaoyuEncryptioner import XinjiaoyuEncryptioner
from src.GetAnswer.api_client import get_content
from src.GetAnswer.config import BASE_URL

from loguru import logger


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
            logger.info("用户数据保存成功")
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")

    def load_user_data(self) -> None:
        """从文件加载用户数据"""
        if not os.path.exists(self.DATA_FILE):
            logger.warning("用户数据文件不存在")
            return

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.user_data = data.get("user_info", {})
                self.public_user_data = data.get("tokens", {})
                self.HEADERS = data.get("headers", {})
                self.studentId = data.get("user_info", {}).get("school", {}).get("studentId", {})
            logger.info("用户数据加载成功")
        except Exception as e:
            logger.error(f"加载用户数据失败: {e}")

    def login(self, username: str, password: str) -> bool:
        """用户登录主方法，如果 Token 未过期且账号有效则直接返回成功"""
        if self.is_token_valid(self.public_user_data.get("token")) and self.check_current_account_valid():
            return True

        logger.info("Token 无效或账号无效，正在执行登录")
        try:
            encoded_username = self._encrypt_data(username)
            encoded_password = self._encrypt_data(password)
            headers, login_data = self._prepare_login_request(encoded_username, encoded_password)
            response = self._make_request(self.AUTH_URL, headers, login_data)

            if response and response.get("code") == 200:
                self._process_login_response(response, headers)
                logger.info("登录成功")
                self.load_user_data()  # 登录成功后重新加载用户数据
                return True

            logger.error(f"登录失败: {response.get('message', '未知错误') if response else '无响应'}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"登录过程中发生错误: {e}")
            sys.exit(1)

    # 手机端暂时没有验证码验证
    # def login(self, username: str, password: str) -> bool:
    #     """用户登录主方法，如果 Token 未过期则直接返回成功"""
    #     if self.is_token_valid(self.public_user_data.get("token")):
    #         return True
    #
    #     logger.info("Token 无效或不存在，正在执行登录")
    #     try:
    #         encoded_username = self._encrypt_data(username)
    #         encoded_password = self._encrypt_data(password)
    #         headers, login_data = self._prepare_login_request(encoded_username, encoded_password)
    #         response = self._make_request(self.AUTH_URL, headers, login_data)
    #
    #         if response:
    #             if response.get("code") == 200:
    #                 self._process_login_response(response, headers)
    #                 logger.info("登录成功")
    #                 return True
    #
    #             elif response.get("code") == 400 and response.get("msg") == '验证码为空':
    #                 logger.info("触发验证码验证")
    #                 user_data = input("触发验证码验证，请手动输入官网正确登录后的数据（请先压缩成一行）: ")
    #                 try:
    #                     parsed_data = self._parse_login_data(user_data)
    #                     self._process_login_response(parsed_data, headers)
    #                     logger.info("手动登录数据解析成功")
    #                     return True
    #                 except Exception as e:
    #                     logger.error(f"手动登录数据解析失败: {e}")
    #                     sys.exit(1)
    #
    #             logger.error(f"登录失败: {response.get('message', '未知错误')}")
    #             sys.exit(1)
    #         else:
    #             logger.error("无响应")
    #             sys.exit(1)
    #
    #     except Exception as e:
    #         logger.error(f"登录过程中发生错误: {e}")
    #         sys.exit(1)
    #
    # @staticmethod
    # def _parse_login_data(data: str) -> dict:
    #     """解析用户手动输入的数据"""
    #     return json.loads(data)

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
            logger.warning("Token 已过期")
        except jwt.DecodeError:
            logger.error("Token 解码失败")
        return False

    def check_current_account_valid(self):
        url = "https://www.xinjiaoyu.com/api/v3/server_questions/category/tree/list"
        response = get_content(url, self.get_headers(), False)
        return response.get("code") == 200

    @staticmethod
    def _log_remaining_time(remaining_time: int) -> None:
        """记录 Token 剩余时间"""
        remaining_td = timedelta(seconds=remaining_time)
        days, seconds = divmod(remaining_td.total_seconds(), 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        logger.info(f"Token 有效，剩余时间：{int(days)} 天 {int(hours)} 小时 {int(minutes)} 分钟 {int(seconds)} 秒")

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
            "client": "android",
            "clientSession": client_session_val,
            "Content-Type": "application/json",
            "User-Agent": "okhttp/4.9.3",
            "encrypt": encrypt_val,
            "t": t_val,
            "app": "student"
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
        self.studentId = self.user_data.get("school", {}).get("studentId", {})
        self.save_user_data({"user_info": self.user_data, "tokens": self.public_user_data, "headers": self.HEADERS})

    def get_headers(self) -> dict | None:
        """
        获取保存的 headers
        """
        if not self.HEADERS:
            logger.warning("未找到 headers，请先登录")
        return self.HEADERS

    def get_studentId(self) -> dict | None:
        """
        获取保存的 studentId
        """
        if not self.studentId:
            logger.warning("未找到 studentId，请先登录")
        return self.studentId

    def _make_request(self, url: str, headers: dict, json_data: dict) -> Optional[dict]:
        """通用 POST 请求方法，带重试机制"""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = requests.post(url, headers=headers, json=json_data, timeout=10)
                if response.ok:
                    logger.info(f"请求成功 (尝试 {attempt}/{self.MAX_RETRIES})")
                    return response.json()
                logger.error(f"请求失败 (尝试 {attempt}/{self.MAX_RETRIES}): {response.text}")
            except requests.RequestException as e:
                logger.error(f"网络错误 (尝试 {attempt}/{self.MAX_RETRIES}): {e}")
            time.sleep(1)
        logger.error("达到最大重试次数，请求失败")
        return None
