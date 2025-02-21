import os

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


def get_video_urls(template_code):
    """
    获取微课视频 URLs
    """
    video_url_api = f"{BASE_URL}/api/v3/server_homework/homework/point/videos/list?homeworkId=&templateCode={template_code}"
    try:
        response_data = get_content(video_url_api, account_manager.get_headers())
        if response_data and response_data['code'] == 200 and response_data['data']:
            return response_data['data']
        else:
            logger.warning(f"未获取到微课视频数据, 模板编号: {template_code}")
            return None
    except Exception as e:
        logger.error(f"获取微课视频URL时出错: {e}")
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
            response_data = get_content(
                f"{BASE_URL}/api/v3/server_homework/homework/template/question/list?templateCode={template_code}"
                f"&studentId={account_manager.get_studentId()}&isEncrypted=false",
                account_manager.get_headers()
            )

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
            homework_response = get_content(
                f"{BASE_URL}/api/v3/server_homework/homework/answer/sheet/student/questions/answer?templateId="
                f"{template_id}",
                account_manager.get_headers(),
                False
            )

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
            toast("处理过程中出现错误，请检查日志", color='error')
            clear()


if __name__ == '__main__':
    logger.add("log/GetAnswer_main_{time}.log", rotation="1 MB", encoding="utf-8", retention="1 minute")
    account_manager = AccountManager()
    account_manager.login("username", "password")  # 在这里填写你的用户名和密码
    # 手机端目前没有验证码验证，当遇到登录遇到验证码验证，手动输入数据时请先压缩成一行

    start_server(main, port=8080, debug=True)
