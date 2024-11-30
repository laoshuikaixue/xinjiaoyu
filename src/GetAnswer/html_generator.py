import logging

from pywebio.output import put_text

from src.GetAnswer.AccountManager import AccountManager
from src.GetAnswer.api_client import get_content

account_manager = AccountManager()


def json_to_html(json_data, template_name):
    if not json_data or "data" not in json_data:
        logging.error(f"Invalid or missing data in response for template: {template_name}")
        put_text("无效的作业数据，无法生成页面。")
        return ""

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
                font-family: Arial, sans-serif;
                background-color: #f4f7f9;
                color: #333;
                line-height: 1.8;
                padding: 40px 20px;
                margin: 0 auto;
                max-width: 900px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                background: #ffffff;
                overflow-x: hidden;
            }
            h1 {
                text-align: center;
                font-size: 3em;
                font-weight: bold;
                background: linear-gradient(90deg, #FF5733, #FFC300, #28B463, #3498DB);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 50px;
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
        </style>
           <script src="https://file.xinjiaoyu.com/pages/mathjax/MathJax.js?config=TeX-AMS-MML_SVG"></script>
           <script type=text/x-mathjax-config>MathJax.Hub.Config({
              showProcessingMessages: false, //关闭js加载过程信息
              messageStyle: "none", //不显示信息
              jax: ["input/TeX", "input/MathML", "output/SVG"],
              extensions: ["tex2jax.js", "TeX/mhchem.js", "TeX/autoload-all.js", "TeX/enclose.js", "TeX/cancel.js", "TeX/noErrors.js", "TeX/noUndefined.js"],
              tex2jax: {
                inlineMath: [["$", "$"], ["$$", "$$"]], //行内公式选择符
                skipTags: ["script", "noscript", "style", "textarea", "pre", "code", "a"] //避开某些标签
              },
              "HTML-CSS": {
                availableFonts: ["STIX","TeX"], //可选字体
                showMathMenu: false //关闭右击菜单显示
              }
            });
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);</script>
    </head>
    <body>
    """
    html_output += f"    <h1>{template_name}</h1>"

    #         <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    # 之前用https://cdn.bootcdn.net/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML

    last_parent_id = None

    try:
        for item in json_data["data"]:
            question = item["question"]
            answer = question['answer'].strip()  # Correct answer, e.g. 'A', 'B', etc.

            # Check if the question has a parentId and fetch parent content if needed
            parent_id = question.get('parentId')
            if parent_id and parent_id != "0":
                if parent_id != last_parent_id:
                    if last_parent_id:
                        # Close the previous parent block if a new parent starts
                        html_output += "</div><hr>"

                    # 获取题干
                    put_text("Start GET parent content")
                    fetch_parent_content = get_content(
                        f"https://www.xinjiaoyu.com/api/v3/server_questions/questions/{parent_id}",
                        account_manager.get_headers())
                    parent_content = fetch_parent_content['data']['content']
                    if parent_content:
                        html_output += f"<div class='parent'><p><b>题干: </b>{parent_content}</p>"

                last_parent_id = parent_id

            # Extract required fields from the JSON
            question_number = question.get('questionNumber', '未知')
            type_name = question.get('typeName', '未知类型')
            type_detail_name = question.get('typeDetailName', '未知题型')
            difficulty_name = question.get('difficultyName', '未知难度')

            # Determine whether to display type_detail_name
            if type_name == type_detail_name:
                header = f"第{question_number}题 ({type_name}) 难度 - {difficulty_name} ："
            else:
                header = f"第{question_number}题 ({type_name}) - {type_detail_name} 难度 - {difficulty_name} ："

            # Add the question container
            html_output += f"<div class='question'><div class='question-header'>{header}</div>"

            # Display the question content
            html_output += f"<p>{question['content']}</p>"

            # Add options for multiple-choice questions (including multi-select)
            if "options" in question and question['options']:
                # Check if all options are null or empty
                all_options_empty = all(
                    option['optionContent'] is None or option['optionContent'].strip() == '' for option in
                    question["options"])

                if all_options_empty:
                    # Display options horizontally without content, but highlight the correct ones
                    html_output += "<ul style='display: flex; justify-content: space-around; list-style-type: none;'>"
                    for option in question["options"]:
                        option_letter = option['option'].strip()

                        # Check if this option is part of the correct answer(s)
                        if option_letter in answer:
                            # Add 'correct-option' class for correct answers
                            html_output += f"<li class='correct-option' style='width: auto;'><b>{option_letter}</b></li>"
                        else:
                            html_output += f"<li style='width: auto;'><b>{option_letter}</b></li>"
                    html_output += "</ul>"
                else:
                    # Display options normally with their content
                    html_output += "<ul>"
                    for option in question["options"]:
                        option_letter = option['option'].strip()
                        option_content = option['optionContent']

                        # Check if this option is part of the correct answer(s)
                        if option_letter in answer:
                            # Add 'correct-option' class for correct answers
                            html_output += f"<li class='correct-option'><b>{option_letter}:</b> {option_content}</li>"
                        else:
                            html_output += f"<li><b>{option_letter}:</b> {option_content}</li>"
                    html_output += "</ul>"
            elif "answer" in question:  # Handle non-choice questions
                html_output += f"<p><b>答案: </b><span class='fill-blank-answer'>{answer}</span></p>"

            # Add explanation if available
            if question.get("answerExplanation"):
                html_output += f"<p class='explanation'><b>解析: </b>{question['answerExplanation']}</p>"

            # Close question container
            html_output += "</div>"

    except Exception as e:
        logging.error(f"Error while generating HTML: {e}")
        put_text("生成HTML时出错，请检查数据格式。")

    if last_parent_id:
        # Close the last parent block
        html_output += "</div><hr>"

    # Footer
    html_output += "<div class='footer'>https://github.com/laoshuikaixue/xinjiaoyu<br>温馨提示：仅供学习使用，请勿直接抄袭答案。</div>"

    # Close the body and html tags
    html_output += "</body></html>"
    return html_output
