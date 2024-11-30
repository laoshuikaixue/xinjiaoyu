import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

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
        生成请求的 MD5 加密字符串
        """
        raw_data = "jbyxinjiaoyu" + t_value + client_session_value + "front"
        return hashlib.md5(raw_data.encode('utf-8')).hexdigest()
