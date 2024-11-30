import logging
import time
import uuid
import os
import json
import requests

from src.GetAnswer.XinjiaoyuEncryptioner import XinjiaoyuEncryptioner
from src.GetAnswer.config import BASE_URL

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class AccountManager:
    AUTH_URL = BASE_URL + "/api/v3/server_system"
    DATA_FILE = "user_data.json"  # 文件保存用户数据
    MAX_RETRIES = 3  # 最大重试次数

    def __init__(self):
        self.user_data = {}
        self.public_user_data = {}
        self.HEADERS = {}
        self.load_user_data()

    def save_user_data(self, data):
        """
        保存用户数据到文件
        """
        try:
            with open(self.DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to save user data: {e}")

    def load_user_data(self):
        """
        从文件加载用户数据
        """
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    self.user_data = data.get('user_info', {})
                    self.public_user_data = data.get('tokens', {})
                    self.HEADERS = data.get('headers', {})
            except Exception as e:
                print(f"Failed to load user data: {e}")

    def login(self, username: str, password: str):
        """
        用户登录主方法
        """
        try:
            encoded_username = XinjiaoyuEncryptioner.encrypt(username, "6f0c5ba452b24fa28989e9524d77407a")
            encoded_password = XinjiaoyuEncryptioner.encrypt(password, "6f0c5ba452b24fa28989e9524d77407a")

            t_val = str(int(time.time() * 1000))
            client_session_val = uuid.uuid4().hex
            encrypt_val = XinjiaoyuEncryptioner.get_md5(t_val, client_session_val)

            headers = {
                "client": "front",
                "clientSession": client_session_val,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/4.9.3",
                "encrypt": encrypt_val,
                "t": t_val
            }

            login_data = {
                "password": encoded_password,
                "t": int(t_val),
                "username": encoded_username
            }

            response = self._make_request(
                f"{self.AUTH_URL}/auth/login",
                headers=headers,
                json_data=login_data
            )

            if response and response.get("code") == 200:
                user_info = response.get("data", {}).get("info", {})
                tokens = {
                    "accessToken": response["data"].get("accessToken"),
                    "token": response["data"].get("token"),
                }
                logging.info("Login Successful")
                self.user_data = user_info
                self.public_user_data = tokens

                # 获取身份数据并保存
                self.HEADERS = {
                    'Accept': 'application/json, text/plain, */*',
                    'Authorization': f'JBY {tokens.get("token", "")}',
                    'accessToken': f'{tokens.get("accessToken", "")}',
                    'client': 'front',
                    'clientSession': f'{client_session_val}',
                    'encrypt': f'{encrypt_val}',
                    't': f'{t_val}'
                }

                # Save user data and headers
                self.save_user_data({
                    "user_info": user_info,
                    "tokens": tokens,
                    "headers": self.HEADERS
                })
                logging.info("User data and headers saved successfully.")

            else:
                error_message = response.get("message", "Unknown error") if response else "No response received"
                logging.error(f"Login failed: {error_message}")

        except Exception as e:
            logging.error(f"An error occurred during login: {e}")

    def get_headers(self):
        """
        获取保存的headers
        """
        if not self.HEADERS:
            logging.warning("No headers found, please log in first.")
            return None
        return self.HEADERS

    def _make_request(self, url, headers, json_data):
        """
        通用请求方法，带重试机制
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(url, headers=headers, json=json_data)
                if response.ok:
                    return response.json()
                else:
                    logging.error(f"Request failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {response.text}")
            except requests.RequestException as e:
                logging.error(f"Network error (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
            time.sleep(1)  # 等待重试
        logging.info("Max retries reached. Request failed.")
        return None
