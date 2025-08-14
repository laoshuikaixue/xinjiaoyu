import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from loguru import logger
from pywebio import start_server, session
from pywebio.input import input
from pywebio.output import put_text, clear, put_file, put_buttons, toast, put_processbar, set_processbar

from src.GetAnswer.AccountManager import AccountManager
from src.GetAnswer.api_client import get_content
from src.GetAnswer.config import BASE_URL
from src.GetAnswer.html_generator import json_to_html


def update_progress(progress, message):
    """更新进度条和状态信息"""
    set_processbar('bar', progress / 100)
    put_text(f'🕒 {message}')


def check_and_relogin():
    """
    检查用户登录状态，如果失效则尝试重新登录
    
    Returns:
        bool: 重新登录是否成功
    """
    logger.info("检测到可能的登录失效，尝试重新登录")
    toast("检测到登录状态可能已失效，正在尝试重新登录...", color='warning')

    # 从用户数据文件中获取用户名和密码
    try:
        import json
        if os.path.exists(account_manager.DATA_FILE):
            with open(account_manager.DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                username = data.get("username", "")
                password = data.get("password", "")

                if username and password:
                    # 尝试重新登录
                    return account_manager.login(username, password)
                else:
                    logger.error("未找到保存的用户名和密码")
                    toast("未找到保存的用户名和密码，请重启程序并重新登录", color='error')
                    return False
        else:
            logger.error("未找到用户数据文件")
            toast("未找到用户数据文件，请重启程序并重新登录", color='error')
            return False
    except Exception as e:
        logger.error(f"重新登录过程中出错: {e}")
        toast("重新登录失败，请重启程序", color='error')
        return False


def get_video_urls(template_code):
    """
    获取微课视频 URLs
    
    Args:
        template_code: 模板编号
        
    Returns:
        dict or None: 视频数据或None
    """
    video_url_api = (f"{BASE_URL}/api/v3/server_homework/homework/point/videos/list?homeworkId=&templateCode="
                     f"{template_code}")
    try:
        response_data = get_content(video_url_api, account_manager.get_dynamic_headers())

        # 检查是否获取成功
        if response_data and response_data.get('code') == 200 and response_data.get('data'):
            return response_data['data']
        else:
            logger.warning(f"未获取到微课视频数据, 模板编号: {template_code}")
            return None
    except Exception as e:
        logger.error(f"获取微课视频URL时出错: {e}")
        return None


def get_template_data(template_code, retry=True):
    """
    获取模板数据
    
    Args:
        template_code: 模板编号
        retry: 是否在失败时尝试重新登录并重试
        
    Returns:
        dict or None: 模板数据或None
    """
    try:
        # 构建请求URL
        request_url = f"{BASE_URL}/api/v3/server_homework/homework/template/question/list?templateCode={template_code}&studentId={account_manager.get_studentId()}&isEncrypted=false"
        request_headers = account_manager.get_dynamic_headers()
        
        # 调试信息：记录请求详情
        logger.debug(f"[调试] 发送模板数据请求 - 模板编号: {template_code}")
        logger.debug(f"[调试] 请求URL: {request_url}")
        logger.debug(f"[调试] 请求头信息: {request_headers}")
        
        response_data = get_content(request_url, request_headers)
        
        # 调试信息：记录响应详情
        if response_data is None:
            logger.warning(f"[调试] 响应数据为None - 模板编号: {template_code}")
            logger.warning(f"[调试] 可能的原因: 网络请求失败、服务器无响应或解析JSON失败")
        else:
            logger.debug(f"[调试] 响应数据类型: {type(response_data)}")
            logger.debug(f"[调试] 响应数据内容: {response_data}")
            
            # 详细检查响应结构
            response_code = response_data.get('code')
            response_msg = response_data.get('msg')
            response_data_field = response_data.get('data')
            
            logger.debug(f"[调试] 响应code: {response_code}")
            logger.debug(f"[调试] 响应msg: {response_msg}")
            logger.debug(f"[调试] 响应data字段类型: {type(response_data_field)}")
            
            if response_data_field:
                logger.debug(f"[调试] 响应data字段内容: {response_data_field}")
            else:
                logger.warning(f"[调试] 响应data字段为空或None - 模板编号: {template_code}")

        # 检查是否获取成功
        if response_data and response_data.get('code') == 200 and response_data.get('data'):
            logger.info(f"[调试] 成功获取模板数据 - 模板编号: {template_code}")
            return response_data
        # 检查是否是登录失效 - code为410或msg包含"请先登录"
        elif response_data and (
            response_data.get('code') == 410 or
            (isinstance(response_data.get('msg'), str) and '请先登录' in response_data.get('msg'))
        ):
            logger.warning(f"[调试] 检测到登录失效 - 模板编号: {template_code}, code: {response_data.get('code')}, msg: {response_data.get('msg')}")
            if retry and check_and_relogin():
                logger.info("重新登录成功，重试获取模板数据")
                toast("重新登录成功，正在重试获取数据...", color='info')
                return get_template_data(template_code, False)  # 重试一次，防止无限循环
            else:
                logger.error("自动重新登录失败，请检查账号信息")
                toast("自动重新登录失败，请检查账号信息", color='error')
                return None
        else:
            # 详细记录失败原因
            if response_data is None:
                logger.warning(f"[调试] 获取模板数据失败: 响应数据为None - 模板编号: {template_code}")
            elif response_data.get('code') != 200:
                logger.warning(f"[调试] 获取模板数据失败: 错误码 {response_data.get('code')}, 错误信息: {response_data.get('msg')} - 模板编号: {template_code}")
            elif not response_data.get('data'):
                logger.warning(f"[调试] 获取模板数据失败: data字段为空 - 模板编号: {template_code}")
            else:
                logger.warning(f"[调试] 获取模板数据失败: 未知原因 - 模板编号: {template_code}")
            
            logger.warning(f"未获取到有效模板数据, 模板编号: {template_code}")
            return None
    except Exception as e:
        logger.error(f"[调试] 获取模板数据时发生异常 - 模板编号: {template_code}")
        logger.error(f"[调试] 异常类型: {type(e).__name__}")
        logger.error(f"[调试] 异常详情: {str(e)}")
        import traceback
        logger.error(f"[调试] 异常堆栈: {traceback.format_exc()}")

        # 如果是网络错误或其他异常，也尝试重新登录
        if retry and check_and_relogin():
            logger.info("重新登录成功，重试获取模板数据")
            toast("重新登录成功，正在重试获取数据...", color='info')
            return get_template_data(template_code, False)  # 重试一次，防止无限循环
        return None


def get_homework_answers(template_id, retry=True):
    """
    获取作业答案数据
    
    Args:
        template_id: 模板ID
        retry: 是否在失败时尝试重新登录并重试
        
    Returns:
        dict or None: 答案数据或None
    """
    try:
        homework_response = get_content(
            f"{BASE_URL}/api/v3/server_homework/homework/answer/sheet/student/questions/answer?templateId="
            f"{template_id}",
            account_manager.get_dynamic_headers(),
            False
        )

        # 检查是否获取成功
        if homework_response and homework_response.get('code') == 200:
            return homework_response
        # 检查是否是登录失效 - 根据用户提供的信息，登录失效时code为410且msg为"请先登录！
        else:
            logger.warning(f"未获取到有效答案数据, 模板ID: {template_id}")
            return None
    except Exception as e:
        logger.error(f"获取答案数据时出错: {e}")

        # 如果是网络错误或其他异常，也尝试重新登录
        if retry and check_and_relogin():
            logger.info("重新登录成功，重试获取答案数据")
            toast("重新登录成功，正在重试获取数据...", color='info')
            return get_homework_answers(template_id, False)  # 重试一次，防止无限循环
        return None


def main():
    session.run_js('document.title="Get Answer Application | LaoShui"')  # 设置浏览器标题

    while True:
        template_code = input("请输入作业模板编号：").strip()

        # 检查输入是否为空
        if not template_code:
            toast("模板编号不能为空，请重新输入", color='error')
            continue  # 重新提示输入

        # 去掉最后的&及其后面的部分（适用于自助题卡 获取答案时不需要此参数）
        template_code = template_code.split('&')[0]

        output_folder = "output"
        os.makedirs(output_folder, exist_ok=True)

        try:
            # 设置输出文件路径
            template_file = os.path.join(output_folder, f"output-{template_code}.html")

            # 检查该模板编号是否已经生成过HTML文件
            if os.path.exists(template_file):
                toast('页面已经生成过', color='error')
                with open(template_file, "rb") as f:
                    put_file(template_file, f.read(), "点击下载生成后的文件")
                put_buttons(['重新查询'], onclick=[lambda: clear() or main()])
                return

            # 开始处理流程
            clear()
            put_text("GitHub: https://github.com/laoshuikaixue/xinjiaoyu")
            put_processbar('bar')  # 创建进度条容器
            update_progress(5, '开始处理请求...')

            # 获取微课视频数据
            update_progress(10, '正在获取微课视频信息...')
            video_data = get_video_urls(template_code)
            if video_data:
                logger.info(f"存在微课视频数据")
                toast("已获取到微课视频信息", color='info')

            # 获取模板数据
            update_progress(15, '正在获取模板基本信息...')
            response_data = get_template_data(template_code)

            if not response_data:
                logger.warning("未获取到有效数据")
                toast("获取模板数据失败", color='error')
                return

            # 解析模板信息
            update_progress(35, '正在解析模板信息...')
            template_id = response_data["data"]["templateId"]
            template_name = response_data["data"]["templateName"].replace('　', ' ')
            toast(f"开始处理：{template_name}", color='info')

            # 获取答案数据
            update_progress(55, '正在获取作业答案数据...')
            homework_response = get_homework_answers(template_id)

            # 生成HTML内容
            update_progress(75, '正在生成HTML内容...')
            html_result = json_to_html(homework_response, template_name, video_data)

            # 保存文件
            update_progress(90, '正在保存文件...')
            with open(template_file, "w", encoding="utf-8") as f:
                f.write(html_result)

            # 处理完成
            update_progress(100, '处理完成！')
            # clear()

            # 显示结果
            toast('🎉 HTML文件已成功生成！', color='success')
            with open(template_file, "rb") as f:
                put_file(template_file, f.read(), "点击下载生成后的文件")
            put_buttons(['再次查询'], onclick=[lambda: clear() or main()])

        except Exception as e:
            logger.error(f"程序执行错误: {e}")
            toast("处理过程中出现错误，正在尝试恢复...", color='warning')

            # 尝试检查是否是登录失效导致的错误
            if "认证" in str(e) or "登录" in str(e) or "token" in str(e).lower() or "授权" in str(e):
                logger.info("可能是登录状态失效导致的错误，尝试重新登录")
                if check_and_relogin():
                    logger.info("重新登录成功，重试当前操作")
                    toast("重新登录成功，正在重试...", color='info')
                    # 不清除界面，继续尝试当前操作
                    continue

            # 如果不是登录问题或重新登录失败，则显示错误并清除界面
            toast("处理过程中出现错误，请检查日志", color='error')
            clear()


if __name__ == '__main__':
    logger.add("log/GetAnswer_main_{time}.log", rotation="1 MB", encoding="utf-8", retention="1 minute")
    account_manager = AccountManager()

    # 在这里填写你的用户名和密码
    username = "username"
    password = "password"

    # 登录并检查结果
    login_success = account_manager.login(username, password)
    if not login_success:
        logger.error("初始登录失败，请检查用户名和密码")
        import sys

        sys.exit(1)

    start_server(main, port=8080, debug=True)
