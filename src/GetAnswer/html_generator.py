from pywebio.output import put_text
from src.GetAnswer.AccountManager import AccountManager
from src.GetAnswer.api_client import get_content
from src.GetAnswer.config import BASE_URL
from loguru import logger

account_manager = AccountManager()


def json_to_html(json_data, template_name):
    # 校验数据是否有效
    if not json_data or "data" not in json_data:
        logger.error(f"Invalid or missing data in response for template: {template_name}")
        put_text("无效的作业数据，无法生成页面。")
        return ""

    # 初始化HTML结构
    html_output = """
    <html>
    <head>
        <meta charset='utf-8'>
    """
    html_output += f"    <title>{template_name} | LaoShui</title>"
    html_output += """
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #eef2f5;
                color: #333;
                line-height: 1.8;
                padding: 20px;
                margin: 0 auto;
                max-width: 900px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                background: #ffffff;
                overflow-x: hidden;
                scroll-behavior: smooth;
            }
            h1 {
                text-align: center;
                font-size: 2.5em;
                font-weight: bold;
                background: linear-gradient(90deg, #FF5733, #FFC300, #28B463, #3498DB);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 30px;
            }
            .parent {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 30px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }
            .parent:hover {
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            .question {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 1px 6px rgba(0, 0, 0, 0.1);
            }
            .question-header {
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 1.2em;
                color: #4CAF50;
            }
            .question p {
                font-size: 1.1em;
                margin-bottom: 10px;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background: #f0f0f0;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 6px;
                font-size: 1em;
                transition: background 0.3s ease;
            }
            li.correct-option {
                background: #dff0d8;
                border: 1px solid #4CAF50;
                font-weight: bold;
            }
            li:hover {
                background: #e0e0e0;
            }
            .fill-blank-answer {
                font-weight: bold;
                color: #007BFF;
            }
            .fill-blank {
                border-bottom: 1px solid black;
                display: inline-block;
                width: 80px;
                margin-left: 5px;
                margin-right: 5px;
            }
            hr {
                border: none;
                border-top: 1px solid #ddd;
                margin: 20px 0;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                color: #aaa;
                font-size: 0.9em;
            }
            img {
                max-width: 100%;
                height: auto;
            }
            .explanation-container {
                background-color: #e8f4f8;
                border-left: 4px solid #007BFF;
                padding: 10px;
                margin-top: 15px;
                border-radius: 5px;
            }
            .explanation-header {
                font-weight: bold;
                margin-bottom: 5px;
            }
            .explanation-content {
                padding-left: 10px;
            }
            u {
                text-decoration: none;
                border-bottom: 1px solid black;
                display: inline-block;
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }
        </style>
        <script src="https://file.xinjiaoyu.com/pages/mathjax/MathJax.js?config=TeX-AMS-MML_SVG"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css" rel="stylesheet">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"></script>
    </head>
    <body>
    <script>
        AOS.init({
            duration: 1200, // 动画持续时间
        });
    </script>
    """

    html_output += f"    <h1>{template_name}</h1>"

    last_parent_id = None  # 用于跟踪题干的ID
    index = 0  # 用于计算动画延迟

    try:
        for item in json_data["data"]:
            question = item["question"]
            answer = question['answer'].strip()  # 获取正确答案

            # 判断题目是否有parentId并处理
            parent_id = question.get('parentId')
            if parent_id and parent_id != "0":  # 如果有题干且不为0
                if parent_id != last_parent_id:
                    if last_parent_id:  # 如果上一题有题干，先关闭上一组
                        html_output += "</div><hr>"

                    # 获取题干内容
                    put_text("开始获取题干内容")
                    fetch_parent_content = get_content(
                        f"{BASE_URL}/api/v3/server_questions/questions/{parent_id}",
                        account_manager.get_headers())
                    parent_content = fetch_parent_content['data']['content']
                    if parent_content:
                        html_output += f"<div class='parent' data-aos='fade-up'><p><b>题干: </b>{parent_content}</p>"

                last_parent_id = parent_id  # 更新题干ID

            # 提取题目的其他信息
            question_number = question.get('questionNumber', '未知')
            type_name = question.get('typeName', '未知类型')
            type_detail_name = question.get('typeDetailName', '未知题型')
            difficulty_name = question.get('difficultyName', '未知难度')

            # 根据题目类型和难度格式化题目标题
            header = f"第{question_number}题 ({type_name}) 难度 - {difficulty_name} ："
            if type_name != type_detail_name:
                header = f"第{question_number}题 ({type_name}) - {type_detail_name} 难度 - {difficulty_name} ："

            # 添加问题内容
            html_output += f"<div class='question' data-aos='fade-up' style='--index: {index};'><div class='question-header'>{header}</div>"
            html_output += f"<p>{question['content']}</p>"

            # 判断并展示选项（多选题或单选题）
            if "options" in question and question['options']:
                # 判断选项是否为空
                all_options_empty = all(
                    option['optionContent'] is None or option['optionContent'].strip() == '' for option in
                    question["options"])

                if all_options_empty:
                    # 如果选项为空，仅展示选项字母（这部分是为语文的文言文断句/判断题 写的 横向排列）
                    html_output += "<ul style='display: flex; justify-content: space-around; list-style-type: none;'>"
                    for option in question["options"]:
                        option_letter = option['option'].strip()
                        # 高亮显示正确答案
                        if option_letter in answer:
                            html_output += f"<li class='correct-option' style='width: auto;'><b>{option_letter}</b></li>"
                        else:
                            html_output += f"<li style='width: auto;'><b>{option_letter}</b></li>"
                    html_output += "</ul>"
                else:
                    # 正常展示选项内容
                    html_output += "<ul>"
                    for option in question["options"]:
                        option_letter = option['option'].strip()
                        option_content = option['optionContent']
                        # 高亮显示正确答案
                        if option_letter in answer:
                            html_output += f"<li class='correct-option'><b>{option_letter}:</b> {option_content}</li>"
                        else:
                            html_output += f"<li><b>{option_letter}:</b> {option_content}</li>"
                    html_output += "</ul>"
            elif "answer" in question:  # 非选择题显示答案
                html_output += f"<p><b>答案: </b><span class='fill-blank-answer'>{answer}</span></p>"

            # 如果有解析，展示解析
            if question.get("answerExplanation"):
                html_output += f"""
                <div class='explanation-container' data-aos='fade-up'>
                    <div class='explanation-header'>解析:</div>
                    <div class='explanation-content'>{question['answerExplanation']}</div>
                </div>
                """

            # 结束当前问题的HTML结构
            html_output += "</div>"
            index += 1

    except Exception as e:
        logger.error(f"Error while generating HTML: {e}")
        put_text("生成HTML时出错，请检查数据格式。")

    # 关闭最后一个题干的HTML块
    if last_parent_id:
        html_output += "</div><hr>"

    # 添加页脚
    html_output += """
    <div class="footer">
    <p>GitHub: <a href="https://github.com/laoshuikaixue/xinjiaoyu" target="_blank" style="color: #3498DB;">https://github.com/laoshuikaixue/xinjiaoyu</a><br>
    温馨提示：仅供学习使用，请勿直接抄袭答案。</p>
    </div>
    """

    # 关闭HTML标签
    html_output += "</body></html>"
    return html_output
