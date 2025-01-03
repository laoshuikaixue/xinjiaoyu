import os

from loguru import logger
from pywebio import start_server, session
from pywebio.input import input
from pywebio.output import put_text, clear, put_file, put_buttons, toast

from src.GetAnswer.AccountManager import AccountManager
from src.GetAnswer.api_client import get_content
from src.GetAnswer.config import BASE_URL
from src.GetAnswer.html_generator import json_to_html


def main():
    session.run_js('document.title="Get Answer Application | LaoShui"')  # 设置浏览器标题

    while True:
        # 提示用户输入作业模板编号
        template_code = input("请输入作业模板编号：")

        # 检查输入是否为空
        if not template_code.strip():
            toast("模板编号不能为空，请重新输入", color='error')
            clear()
            continue  # 重新提示输入

        try:
            # 设置输出文件路径
            template_file = os.path.join(output_folder, f"output-{template_code}.html")

            # 检查该模板编号是否已经生成过HTML文件
            if os.path.exists(template_file):
                # 显示已生成的HTML文件提示
                toast('页面已经生成过', color='error')

                # 提供文件下载链接
                with open(template_file, "rb") as f:
                    put_file(template_file, f.read(), "点击下载生成后的文件")
                put_buttons(['重新查询'], onclick=[lambda: clear() or main()])  # 点击重新查询按钮清空页面并重新执行
                return

            # 如果文件不存在，则请求服务器获取作业模板内容
            response_data = get_content(
                f"{BASE_URL}/api/v3/server_homework/homework/template/question/list?templateCode={template_code}&studentId={account_manager.get_studentId()}&isEncrypted=false",
                account_manager.get_headers())  # 获取作业模板

            # 如果没有返回数据，记录警告并退出
            if not response_data:
                logger.warning("No data returned for the provided template code.")
                return

            # 获取模板信息并输出
            template_id = response_data["data"]["templateId"]
            template_name = response_data["data"]["templateName"].replace('　', ' ')  # 去除多余的空格

            put_text("https://github.com/laoshuikaixue/xinjiaoyu")
            toast(f"开始处理：{template_name}", color='info')

            # 根据模板ID获取作业答案内容
            homework_response = get_content(
                f"{BASE_URL}/api/v3/server_homework/homework/answer/sheet/student/questions/answer?templateId={template_id}",
                account_manager.get_headers(), False)  # 获取作业答案数据

            # 将数据转化为HTML
            html_result = json_to_html(homework_response, template_name)

            # 将生成的HTML保存到文件
            with open(template_file, "w", encoding="utf-8") as f:
                f.write(html_result)

            logger.info(f"HTML文件已保存到 {template_file}")

            clear()  # 清空页面内容
            # 显示成功提示并提供文件下载链接
            toast('HTML文件已成功生成并保存！', color='success')

            with open(template_file, "rb") as f:
                put_file(template_file, f.read(), "点击下载生成后的文件")

            # 提供重新查询按钮
            put_buttons(['重新查询'], onclick=[lambda: clear() or main()])

        except Exception as e:
            # 捕获并记录错误
            logger.error(f"程序执行过程中发生错误: {e}")
            toast("主程序执行过程出现错误，请检查报错内容。", color='error')
            clear()


if __name__ == '__main__':
    logger.add("log/GetAnswer_main_{time}.log", rotation="1 MB", encoding="utf-8", retention="1 minute")

    # 初始化账户管理器
    account_manager = AccountManager()

    # 如果没有找到用户数据文件，则进行登录
    account_manager.login("username", "password")  # 在这里填写你的用户名和密码
    # 手机端目前没有验证码验证，当遇到登录遇到验证码验证，手动输入数据时请先压缩成一行

    # 确保输出目录存在
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 启动PyWebIO服务器并执行主函数
    start_server(main, port=8080)
