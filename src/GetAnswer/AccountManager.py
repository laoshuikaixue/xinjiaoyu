import json
import os
import time
import uuid
from datetime import timedelta
from typing import Optional, Dict

import jwt
import requests
from loguru import logger

from src.GetAnswer.XinjiaoyuEncryptioner import XinjiaoyuEncryptioner
from src.GetAnswer.api_client import get_content
from src.GetAnswer.config import BASE_URL


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
        self.safe_code = None
        self.client_session_id = None
        self.load_user_data()

    def save_user_data(self, data: dict) -> None:
        """保存用户数据到文件"""
        try:
            # 如果已有用户名和密码，确保它们被保留
            if os.path.exists(self.DATA_FILE):
                try:
                    with open(self.DATA_FILE, "r", encoding="utf-8") as file:
                        existing_data = json.load(file)
                        if "username" in existing_data and "password" in existing_data:
                            data["username"] = existing_data["username"]
                            data["password"] = existing_data["password"]
                except Exception:
                    pass  # 如果读取失败，继续使用新数据
                    
            with open(self.DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            logger.info("用户数据保存成功")
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")
            
    def _save_credentials(self, username: str, password: str) -> None:
        """保存用户名和密码到用户数据文件"""
        try:
            data = {}
            if os.path.exists(self.DATA_FILE):
                try:
                    with open(self.DATA_FILE, "r", encoding="utf-8") as file:
                        data = json.load(file)
                except Exception:
                    pass  # 如果读取失败，使用空字典
            
            # 更新用户名和密码
            data["username"] = username
            data["password"] = password
            
            with open(self.DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            logger.info("用户凭据保存成功")
        except Exception as e:
            logger.error(f"保存用户凭据失败: {e}")

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
                
                # 恢复保存的clientSession和safeCode
                session_data = data.get("session_data", {})
                self.client_session_id = session_data.get("client_session_id")
                self.safe_code = session_data.get("safe_code")
                
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
                # 保存用户名和密码，用于自动重新登录
                self._save_credentials(username, password)
                logger.info("登录成功")
                self.load_user_data()  # 登录成功后重新加载用户数据
                return True

            logger.error(f"登录失败: {response.get('msg', '未知错误') if response else '无响应'}")
            return False  # 返回False而不是退出程序，允许调用者处理登录失败
        except Exception as e:
            logger.error(f"登录过程中发生错误: {e}")
            return False  # 返回False而不是退出程序，允许调用者处理登录失败

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
        """检查当前账户是否有效（使用动态加密）"""
        try:
            # 准备动态加密头部
            headers = self._prepare_dynamic_headers()
            if not headers:
                return False
                
            # 添加认证信息
            if self.public_user_data.get("token") and self.public_user_data.get("accessToken"):
                headers.update({
                    "authorization": f"JBY {self.public_user_data['token']}",
                    "accesstoken": self.public_user_data["accessToken"]
                })
            
            url = "https://www.xinjiaoyu.com/api/v3/server_system/member/user/vip"
            response = get_content(url, headers, False, False)
            return response.get("code") == 200
            
        except Exception as e:
            logger.error(f"检查账户有效性时发生错误: {e}")
            return False
    
    def _prepare_dynamic_headers(self) -> Optional[Dict[str, str]]:
        """准备动态加密的请求头部"""
        try:
            # 如果没有客户端会话ID，生成一个新的
            if not self.client_session_id:
                self.client_session_id = XinjiaoyuEncryptioner.generate_client_session_id() if hasattr(XinjiaoyuEncryptioner, 'generate_client_session_id') else uuid.uuid4().hex
            
            # 如果没有SafeCode，获取一个新的
            if not self.safe_code and hasattr(XinjiaoyuEncryptioner, 'get_safe_code'):
                self.safe_code = XinjiaoyuEncryptioner.get_safe_code(self.client_session_id)
                if not self.safe_code:
                    logger.warning("无法获取SafeCode，使用旧版加密")
                    return self.get_headers()
            
            # 生成动态加密头部
            timestamp = int(time.time() * 1000)
            if hasattr(XinjiaoyuEncryptioner, 'get_dynamic_encrypt') and self.safe_code:
                encrypt_val = XinjiaoyuEncryptioner.get_dynamic_encrypt(
                    self.safe_code, timestamp, self.client_session_id, "applet"
                )
            else:
                encrypt_val = XinjiaoyuEncryptioner.get_md5(str(timestamp), self.client_session_id)
            
            headers = {
                "encrypt": encrypt_val,
                "xweb_xhr": "1",
                "clientsession": self.client_session_id,
                "client": "applet",
                "app": "student",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2540621) XWEB/16203",
                "t": str(timestamp)
            }
            
            return headers
            
        except Exception as e:
            logger.error(f"准备动态头部时发生错误: {e}")
            return self.get_headers()
    
    def get_dynamic_headers(self) -> Optional[Dict[str, str]]:
        """获取动态加密的请求头部（供外部调用）"""
        headers = self._prepare_dynamic_headers()
        if headers and self.public_user_data.get("token") and self.public_user_data.get("accessToken"):
            headers.update({
                "authorization": f"JBY {self.public_user_data['token']}",
                "accesstoken": self.public_user_data["accessToken"]
            })
        return headers

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

    def _prepare_login_request(self, username: str, password: str) -> tuple[dict, dict]:
        """准备登录请求所需数据（使用动态加密）"""
        # 生成客户端会话ID
        self.client_session_id = XinjiaoyuEncryptioner.generate_client_session_id() if hasattr(XinjiaoyuEncryptioner, 'generate_client_session_id') else uuid.uuid4().hex
        
        # 获取SafeCode
        if hasattr(XinjiaoyuEncryptioner, 'get_safe_code'):
            self.safe_code = XinjiaoyuEncryptioner.get_safe_code(self.client_session_id)
        else:
            self.safe_code = None
            
        if not self.safe_code:
            logger.warning("无法获取SafeCode，使用旧版加密方式")
            # 回退到旧版加密方式
            t_val = str(int(time.time() * 1000))
            client_session_val = uuid.uuid4().hex
            encrypt_val = XinjiaoyuEncryptioner.get_md5(t_val, client_session_val)
            headers = {
                'Content-Type': "application/json",
                'accesstoken': "",
                'authorization': "",
                'encrypt': encrypt_val,
                'xweb_xhr': "1",
                'clientsession': client_session_val,
                'client': "applet",
                'app': "student",
                'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2540621) XWEB/16203",
                't': t_val
            }
            login_data = {"username": username, "password": password, "t": int(t_val)}
            return headers, login_data
        
        # 使用动态加密
        timestamp = int(time.time() * 1000)
        if hasattr(XinjiaoyuEncryptioner, 'get_dynamic_encrypt'):
            encrypt_val = XinjiaoyuEncryptioner.get_dynamic_encrypt(
                self.safe_code, timestamp, self.client_session_id, "applet"
            )
        else:
            encrypt_val = XinjiaoyuEncryptioner.get_md5(str(timestamp), self.client_session_id)
        
        headers = {
            'Content-Type': "application/json",
            'accesstoken': "",
            'authorization': "",
            'encrypt': encrypt_val,
            'xweb_xhr': "1",
            'clientsession': self.client_session_id,
            'client': "applet",
            'app': "student",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2540621) XWEB/16203",
            't': str(timestamp)
        }
        
        login_data = {"username": username, "password": password, "t": timestamp}
        return headers, login_data

    def _process_login_response(self, response: dict, headers: dict) -> None:
        """处理登录响应数据"""
        tokens = response["data"]
        self.user_data = response.get("data", {}).get("info", {})
        self.public_user_data = {"accessToken": tokens.get("accessToken"), "token": tokens.get("token")}
        self.HEADERS.update(headers)
        self.HEADERS.update({
            "authorization": f'JBY {self.public_user_data["token"]}',
            "accesstoken": self.public_user_data["accessToken"],
        })
        self.studentId = self.user_data.get("school", {}).get("studentId", {})
        
        # 保存clientSession和safeCode到用户数据中，确保后续请求时能够重用
        session_data = {
            "client_session_id": self.client_session_id,
            "safe_code": self.safe_code
        }
        
        self.save_user_data({
            "user_info": self.user_data, 
            "tokens": self.public_user_data, 
            "headers": self.HEADERS,
            "session_data": session_data
        })

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
