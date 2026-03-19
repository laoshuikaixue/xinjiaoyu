import json
import os
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

import requests
from loguru import logger
from pywebio.output import put_text


SENSITIVE_KEYS = {"authorization", "accesstoken", "token", "password", "cookie", "set-cookie"}
ENABLE_DEBUG_RECORD = True
DEBUG_RECORD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "debug_api_records"
)
DEBUG_RECORD_FILE = os.path.join(DEBUG_RECORD_DIR, "api_debug_records.jsonl")


def _mask_sensitive_data(data):
    """递归脱敏敏感字段，避免调试记录泄露凭证。"""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_str = str(key).lower()
            if key_str in SENSITIVE_KEYS:
                masked[key] = "***MASKED***"
            else:
                masked[key] = _mask_sensitive_data(value)
        return masked
    if isinstance(data, list):
        return [_mask_sensitive_data(item) for item in data]
    return data


def save_debug_http_record(method, url, request_headers=None, request_params=None, request_json=None,
                           status_code=None, response_headers=None, response_text=None, response_json=None,
                           error_type=None, error_message=None):
    """按行写入 HTTP 调试记录，便于后续分析接口结构。"""
    if not ENABLE_DEBUG_RECORD:
        return

    try:
        os.makedirs(DEBUG_RECORD_DIR, exist_ok=True)
        parsed_url = urlsplit(url)
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "method": method,
            "url": url,
            "path": parsed_url.path,
            "query": parse_qs(parsed_url.query),
            "request_headers": _mask_sensitive_data(request_headers or {}),
            "request_params": request_params,
            "request_json": _mask_sensitive_data(request_json),
            "status_code": status_code,
            "response_headers": dict(response_headers) if response_headers else {},
            "response_text": response_text,
            "response_json": response_json,
            "error_type": error_type,
            "error_message": error_message
        }
        with open(DEBUG_RECORD_FILE, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as save_error:
        logger.error(f"保存调试记录失败: {save_error}")


def get_content(url, headers=None, log_visual=True, enable_log=True):
    """
    发送 GET 请求并返回 JSON 数据。

    参数:
    - url: 请求地址。
    - headers: 请求头，可选。
    - log_visual: 是否在页面输出请求提示。
    - enable_log: 是否输出日志。

    返回:
    - dict: 解析成功后的 JSON 数据。
    - None: 请求失败或响应不可解析。
    """
    parsed_url = urlsplit(url)
    safe_url = parsed_url.path

    if enable_log:
        logger.info(f"请求地址: {safe_url}")
        if log_visual:
            put_text(f"请求地址: {safe_url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"请求失败: {safe_url}，状态码: {response.status_code}")
            save_debug_http_record(
                method="GET",
                url=url,
                request_headers=headers,
                status_code=response.status_code,
                response_headers=response.headers,
                response_text=response.text
            )
            put_text(f"获取数据失败，状态码：{response.status_code}")
            return None

        try:
            response_json = response.json()
            save_debug_http_record(
                method="GET",
                url=url,
                request_headers=headers,
                status_code=response.status_code,
                response_headers=response.headers,
                response_text=response.text,
                response_json=response_json
            )
            return response_json
        except ValueError:
            logger.error(f"响应解析失败: {safe_url}")
            save_debug_http_record(
                method="GET",
                url=url,
                request_headers=headers,
                status_code=response.status_code,
                response_headers=response.headers,
                response_text=response.text,
                error_type="ValueError",
                error_message="响应内容不是有效JSON"
            )
            put_text("获取数据时出现错误：无效的响应格式。")
            return None
    except requests.exceptions.RequestException as error:
        logger.error(f"网络请求异常: {safe_url}，错误: {error}")
        save_debug_http_record(
            method="GET",
            url=url,
            request_headers=headers,
            error_type=type(error).__name__,
            error_message=str(error)
        )
        put_text("网络请求失败，请检查您的网络连接。")
        return None
    except Exception as error:
        logger.error(f"未知异常: {safe_url}，错误: {error}")
        save_debug_http_record(
            method="GET",
            url=url,
            request_headers=headers,
            error_type=type(error).__name__,
            error_message=str(error)
        )
        put_text("发生未知错误。请稍后重试。")
        return None
