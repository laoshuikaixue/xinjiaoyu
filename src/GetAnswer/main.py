import logging
import os

from pywebio import start_server, session
from pywebio.input import input
from pywebio.output import put_html, put_text, clear, put_file, put_buttons

from src.GetAnswer.AccountManager import AccountManager
from src.GetAnswer.api_client import get_content
from src.GetAnswer.config import BASE_URL
from src.GetAnswer.html_generator import json_to_html

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    session.run_js('document.title="Get Answer Application | LaoShui"')  # 设置浏览器标题

    # 提示用户输入作业模板编号
    template_code = input("请输入作业模板编号：")

    try:
        # 设置输出文件路径
        template_file = os.path.join(output_folder, f"output-{template_code}.html")

        # 检查该模板编号是否已经生成过HTML文件
        if os.path.exists(template_file):
            # 如果文件已存在，直接读取并展示
            with open(template_file, "r", encoding="utf-8") as f:
                html_result = f.read()

            # 显示已生成的HTML文件提示
            put_html('<div style="margin: 20px;">'
                     '<h3 style="color: red;">页面已经生成过</h3></div>')

            # 提供文件下载链接
            with open(template_file, "rb") as f:
                put_file(template_file, f.read(), "点击下载生成后的文件")
            put_buttons(['重新查询'], onclick=[lambda: clear() or main()])  # 点击重新查询按钮清空页面并重新执行
            put_html(html_result)
            return

        # 如果文件不存在，则请求服务器获取作业模板内容
        response_data = get_content(
            f"{BASE_URL}/api/v3/server_homework/homework/template/question/list?templateCode={template_code}&studentId={account_manager.get_studentId()}",
            account_manager.get_headers())  # 获取作业模板

        # 如果没有返回数据，记录警告并退出
        if not response_data:
            logging.warning("No data returned for the provided template code.")
            return

        # 获取模板信息并输出
        template_id = response_data["data"]["templateId"]
        template_name = response_data["data"]["templateName"].replace('　', ' ')  # 去除多余的空格

        put_text("https://github.com/laoshuikaixue/xinjiaoyu")
        put_text(f"开始处理：{template_name}")

        # 根据模板ID获取作业答案内容
        homework_response = get_content(
            f"{BASE_URL}/api/v3/server_homework/homework/answer/sheet/student/questions/answer?templateId={template_id}",
            account_manager.get_headers(), False)  # 获取作业答案数据

        # 使用自定义的json_to_html函数将数据转化为HTML
        html_result = json_to_html(homework_response, template_name)

        # 将生成的HTML保存到文件
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(html_result)

        logging.info(f"HTML文件已保存到 {template_file}")

        clear()  # 清空页面内容
        # 显示成功提示并提供文件下载链接
        put_html('<div style="margin: 20px;">'
                 '<h3 style="color: blue;">HTML文件已成功生成并保存！</h3></div>')

        with open(template_file, "rb") as f:
            put_file(template_file, f.read(), "点击下载生成后的文件")

        # 提供重新查询按钮
        put_buttons(['重新查询'], onclick=[lambda: clear() or main()])

        # 显示生成的HTML结果
        put_html(html_result)
        put_buttons(['重新查询'], onclick=[lambda: clear() or main()])

    except Exception as e:
        # 捕获并记录错误
        logging.error(f"程序执行过程中发生错误: {e}")
        put_text("主程序执行过程出现错误，请检查报错内容。")


if __name__ == '__main__':
    # 初始化账户管理器
    account_manager = AccountManager()

    # 如果没有找到用户数据文件，则进行登录
    account_manager.login("username", "password")  # 在这里填写你的用户名和密码

    # 确保输出目录存在
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 启动PyWebIO服务器并执行主函数
    start_server(main, port=8080)
