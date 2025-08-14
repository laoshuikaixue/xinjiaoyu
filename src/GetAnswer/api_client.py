import requests

from urllib.parse import urlsplit
from pywebio.output import put_text
from loguru import logger


def get_content(url, headers=None, log_visual=True, enable_log=True):
    """
    Fetch content from the provided URL while protecting privacy by omitting the query parameters in logs.

    Parameters:
    - url: The URL to send the request to.
    - headers: Optional. The headers to include in the request. If None, no headers will be sent.

    Returns:
    - The content if the request is successful, or None if it fails.
    """
    # Extract the URL without the query parameters for logger
    parsed_url = urlsplit(url)
    safe_url = f"{parsed_url.path}"

    if enable_log:
        logger.info(f"Fetching content from URL: {safe_url}")
        logger.debug(f"[调试] 完整请求URL: {url}")
        logger.debug(f"[调试] 请求头: {headers}")
        if log_visual:
            put_text(f"Fetching content from URL: {safe_url}")

    try:
        # Send the request with or without headers
        response = requests.get(url, headers=headers) if headers else requests.get(url)
        
        # 调试信息：记录HTTP响应详情
        logger.debug(f"[调试] HTTP响应状态码: {response.status_code}")
        logger.debug(f"[调试] HTTP响应头: {dict(response.headers)}")
        
        # 记录响应内容（截取前1000字符避免日志过长）
        response_text = response.text
        if len(response_text) > 1000:
            logger.debug(f"[调试] HTTP响应内容(前1000字符): {response_text[:1000]}...")
        else:
            logger.debug(f"[调试] HTTP响应内容: {response_text}")

        # Check for successful response and return data
        if response.status_code == 200:
            try:
                json_data = response.json()  # Try parsing JSON
                logger.debug(f"[调试] JSON解析成功，数据类型: {type(json_data)}")
                return json_data
            except ValueError as json_error:
                logger.error(f"[调试] JSON解析失败 - URL: {safe_url}, 错误: {json_error}")
                logger.error(f"[调试] 原始响应内容: {response_text}")
                put_text("获取数据时出现错误：无效的响应格式。")
                return None
        else:
            logger.warning(f"[调试] HTTP请求失败 - URL: {safe_url}, 状态码: {response.status_code}")
            logger.warning(f"[调试] 错误响应内容: {response_text}")
            put_text(f"获取数据失败，状态码：{response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"[调试] 网络请求异常 - URL: {safe_url}")
        logger.error(f"[调试] 异常类型: {type(e).__name__}")
        logger.error(f"[调试] 异常详情: {str(e)}")
        put_text("网络请求失败，请检查您的网络连接。")
        return None
    except Exception as e:
        logger.error(f"[调试] 未知异常 - URL: {safe_url}")
        logger.error(f"[调试] 异常类型: {type(e).__name__}")
        logger.error(f"[调试] 异常详情: {str(e)}")
        import traceback
        logger.error(f"[调试] 异常堆栈: {traceback.format_exc()}")
        put_text("发生未知错误。请稍后重试。")
        return None
