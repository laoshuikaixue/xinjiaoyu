import base64
import hashlib
import random
import time
from typing import Optional

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from loguru import logger


class XinjiaoyuEncryptioner:
    @staticmethod
    def encrypt(raw_text: str, key: str) -> str:
        """
        AES-256 ECB PKCS7 加密
        """
        try:
            cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
            encrypted = cipher.encrypt(pad(raw_text.encode('utf-8'), AES.block_size))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")

    @staticmethod
    def decrypt(encrypted_text: str, key: str) -> str:
        """
        AES-256 ECB PKCS7 解密
        """
        try:
            cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
            decrypted = unpad(cipher.decrypt(base64.b64decode(encrypted_text)), AES.block_size)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    @staticmethod
    def get_md5(t_value: str, client_session_value: str) -> str:
        """
        生成请求的 MD5 加密字符串（旧版本，兼容性保留）
        """
        raw_data = "jbyxinjiaoyu" + t_value + client_session_value + "applet"
        return hashlib.md5(raw_data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def get_dynamic_encrypt(safe_code: str, timestamp: int, client_session_id: str, client: str = "applet") -> str:
        """
        生成动态加密字符串
        """
        try:
            # 使用ENCRYPTION_KEY对safe_code进行AES解密
            ENCRYPTION_KEY = "6f0c5ba452b24fa28989e9524d77407a"
            decrypted_safe_code = XinjiaoyuEncryptioner.decrypt(safe_code, ENCRYPTION_KEY)
            
            # 使用解密后的safe_code生成MD5哈希
            raw_data = decrypted_safe_code + str(timestamp) + client_session_id + client
            return hashlib.md5(raw_data.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"生成动态加密字符串失败: {e}")
            raise ValueError(f"Failed to generate dynamic encrypt: {e}")
    
    @staticmethod
    def generate_client_session_id() -> str:
        """
        生成客户端会话ID
        基于时间戳 + 10位随机字符串
        """
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        t = int(time.time() * 1000)  # 获取时间戳
        
        # 在时间戳后面追加10个随机字符
        for i in range(10):
            t = str(t) + chars[random.randint(0, len(chars) - 1)]

        # 小程序使用的应该是uuid.uuid4().hex 这里是网页端JS的实现方式 但也可以使用
        
        return str(t)
    
    @staticmethod
    def get_safe_code(client_session_id: str, base_url: str = "https://www.xinjiaoyu.com") -> Optional[str]:
        """
        获取SafeCode
        """
        try:
            timestamp = int(time.time() * 1000)
            client = "applet"
            
            # 准备请求参数
            params = {
                "clientSessionId": client_session_id,
                "t": timestamp,
                "client": client
            }
            
            # 生成encrypt参数
            encrypt_data = client + client_session_id + str(timestamp)
            params["encrypt"] = hashlib.md5(encrypt_data.encode('utf-8')).hexdigest()
            
            # 发送请求
            url = f"{base_url}/api/v3/server_system/system/code"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    safe_code = result.get("data")
                    logger.info("SafeCode获取成功")
                    return safe_code
                else:
                    logger.error(f"获取SafeCode失败: {result.get('msg', '未知错误')}")
            else:
                logger.error(f"请求SafeCode失败，状态码: {response.status_code}")
                
        except Exception as e:
            logger.error(f"获取SafeCode时发生错误: {e}")
            
        return None
