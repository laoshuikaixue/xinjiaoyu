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
        if log_visual:
            put_text(f"Fetching content from URL: {safe_url}")

    try:
        # Send the request with or without headers
        response = requests.get(url, headers=headers) if headers else requests.get(url)

        # Check for successful response and return data
        if response.status_code == 200:
            try:
                return response.json()  # Try parsing JSON
            except ValueError:
                logger.error(f"Failed to parse JSON from {safe_url}")
                put_text("获取数据时出现错误：无效的响应格式。")
                return None
        else:
            logger.warning(f"Request to {safe_url} failed with status code {response.status_code}")
            put_text(f"获取数据失败，状态码：{response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error occurred while fetching {safe_url}: {e}")
        put_text("网络请求失败，请检查您的网络连接。")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        put_text("发生未知错误。请稍后重试。")
        return None
