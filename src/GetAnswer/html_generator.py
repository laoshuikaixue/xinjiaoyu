from pywebio.output import put_text
from src.GetAnswer.AccountManager import AccountManager
from src.GetAnswer.api_client import get_content
from src.GetAnswer.config import BASE_URL
from loguru import logger

account_manager = AccountManager()


def json_to_html(json_data, template_name, video_data=None):
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
            /* 根元素，定义全局 CSS 变量 */
            :root {
                --bg-color: #ffffff;
                --text-color: #333;
                --card-bg: #ffffff;
                --border-color: #ddd;
                --button-primary: #4CAF50;
                --button-primary-hover: #45a049;
                --button-secondary: #6c757d; /* 次按钮颜色 (未使用，保留定义) */
                --button-secondary-hover: #5a6268;
                --option-bg: #f0f0f0;
                --correct-bg: #dff0d8;
                --explanation-bg: #e8f4f8;
                --explanation-border: #007BFF;
                --video-bg: #f9f9f9; /* 视频容器背景色 */
                --video-border: #eee; /* 视频容器边框颜色 */
                --video-button-bg: #007bff; /* 视频按钮背景色 */
                --video-button-hover: #0056b3; /* 视频按钮悬停色 */
                --video-button-active: #0056b3; /* 视频按钮激活色 */
                --question-header-color: #388e3c;
                --question-header-bar-color: #0a93fc; /* 题目标题横条颜色 */


            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg-color: #1a1a1a;
                    --text-color: #e0e0e0;
                    --card-bg: #2d2d2d;
                    --border-color: #404040;
                    --button-primary: #2d7d32;
                    --button-primary-hover: #245d28;
                    --button-secondary: #495057; /* 深色模式次按钮颜色 (未使用，保留定义) */
                    --button-secondary-hover: #343a40;
                    --option-bg: #404040;
                    --correct-bg: #1a331a;
                    --explanation-bg: #1a2d3d;
                    --explanation-border: #0056b3;
                    --video-bg: #252525; /* 深色模式视频容器背景色 */
                    --video-border: #333; /* 深色模式视频容器边框颜色 */
                    --video-button-bg: #1e88e5; /* 深色模式视频按钮背景色 */
                    --video-button-hover: #1565c0; /* 深色模式视频按钮悬停色 */
                    --video-button-active: #1565c0; /* 深色模式视频按钮激活色 */
                    --question-header-color: #66bb6a; /* 深色模式下题目标题颜色 */
                    --question-header-bar-color: #0a93fc;
                }
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--bg-color); /*  页面背景色，使用 CSS 变量 */
                color: var(--text-color); /*  文本颜色，使用 CSS 变量 */
                line-height: 1.8;
                padding: 20px;
                margin: 0 auto; /*  页面主体水平居中 */
                max-width: 900px; /*  页面最大宽度 */
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); /*  页面主体阴影 */
                border-radius: 10px;
                overflow-x: hidden; /*  防止水平滚动条 */
                scroll-behavior: smooth; /*  平滑滚动效果 */
                font-size: 1.05em;
            }
            @media screen and (max-width: 768px) {
                body {
                    font-size: 1em; /* 小屏幕下body字体大小恢复默认 */
                    padding: 15px; /* 减小内边距 */
                }
                h1 {
                    font-size: 2em; /* 小屏幕下标题字体大小 */
                    margin-bottom: 20px;
                }
                .video-section {
                    margin-bottom: 20px; /* 视频区域下边距 */
                }
                .video-selector {
                    padding: 8px 10px; /* 视频按钮选择器内边距 */
                    gap: 5px; /* 视频按钮间距 */
                }
                .video-selector button {
                    font-size: 12px; /* 视频按钮字体大小 */
                    padding: 6px 10px;
                }
                .parent, .question, .explanation-container, .video-card {
                    padding: 15px; /* 卡片内边距 */
                    margin-bottom: 20px; /* 卡片下边距 */
                }

            }


            h1 {
                text-align: center; /*  居中对齐 */
                font-size: 2.5em;
                font-weight: bold;
                background: linear-gradient(90deg, #FF5733, #FFC300, #28B463, #3498DB); /*  彩色渐变背景 */
                -webkit-background-clip: text; /*  背景剪裁为文字 */
                -webkit-text-fill-color: transparent; /*  文字颜色透明，显示背景 */
                margin-bottom: 30px;
            }
            .parent {
                background-color: var(--card-bg); /*  背景色，使用 CSS 变量 */
                border: 1px solid var(--border-color); /*  边框，使用 CSS 变量 */
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 30px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease; /*  过渡效果 */
            }
            .question {
                background-color: var(--card-bg); /*  背景色，使用 CSS 变量 */
                border: 1px solid var(--border-color); /*  边框，使用 CSS 变量 */
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 30px; /* 题目间距增加一倍 */
                box-shadow: 0 1px 6px rgba(0, 0, 0, 0.1);
                animation-duration: 0.8s;
                animation-delay: calc(var(--index) * 50ms);
                opacity: 1; /* 确保初始状态可见，避免闪烁 */
            }
             @media (prefers-reduced-motion: reduce) { /*  针对 reduce motion 的用户偏好设置 */
                .question {
                    animation: none; /*  禁用动画 */
                }
            }

            /* 题目标题样式 */
            .question-header {
                font-weight: bold;
                margin-bottom: 15px;
                font-size: 1.2em;
                color: var(--question-header-color); /*  标题颜色，使用 CSS 变量 */
                padding: 0 0;
                border-radius: 0;
                display: flex;
                align-items: flex-start; /* 修改为 flex-start，使标题和蓝色条顶部对齐 */
                position: relative; /*  添加相对定位，使伪元素可以相对于它定位 */
                margin-left: 16px; /* 横条与题号的距离增加一倍 */
            }
            /* 蓝色题目标题横条 */
            .question-header::before {
                content: '';
                display: inline-block;
                position: absolute; /*  改为绝对定位 */
                top: 0; /*  顶部对齐 */
                left: -16px; /*  调整横条位置，使其紧贴题目左侧, 距离增加一倍 */
                width: 4px; /* 横条宽度 */
                height: 100%; /* 高度设置为 100%，自适应父元素高度 */
                margin-right: 16px; /* 横条与题号的间距, 距离增加一倍 */
                background-color: var(--question-header-bar-color); /*  横条背景色，使用 CSS 变量 */
                border-radius: 2px; /* 横条圆角 */
            }


            .question p {
                font-size: 1.1em;
                margin-bottom: 10px;
            }
            ul {
                list-style-type: none; /*  去除默认列表样式 */
                padding: 0;
            }
            li {
                background: var(--option-bg); /*  选项背景色，使用 CSS 变量 */
                padding: 10px;
                margin-bottom: 12px;
                border-radius: 6px;
                font-size: 1em;
                transition: background 0.3s ease; /*  背景色过渡效果 */
            }
            li.correct-option {
                background: var(--correct-bg); /*  正确答案选项背景色，使用 CSS 变量 */
                border: 1px solid var(--button-primary); /*  正确答案选项边框，使用 CSS 变量 */
                font-weight: bold;
            }

            .fill-blank-answer {
                font-weight: bold;
                text-decoration: none; /*  去除默认的 text-decoration */
                border-bottom: 1px solid var(--explanation-border); /* 使用 border-bottom 模拟下划线，颜色使用 CSS 变量 */
                padding-bottom: 1px; /*  可以根据需要调整下划线与文字的间距 */
            }

            /* 题目解析容器 */
            .explanation-container {
                background-color: var(--explanation-bg); /*  背景色，使用 CSS 变量 */
                border-left: 4px solid var(--explanation-border); /*  左边框，使用 CSS 变量 */
                padding: 10px;
                margin-top: 15px;
                border-radius: 5px;
                overflow-wrap: break-word; /*  添加 overflow-wrap: break-word; 解决内容超出边框问题 */
                animation-duration: 0.8s;
                animation-delay: calc(var(--index) * 100ms);
                animation-fill-mode: backwards; /* 保持初始状态直到动画开始 */
                opacity: 0; /* 初始状态透明 */
                transform: translateY(20px); /* 初始位置下方 */
                transition: opacity 0.8s ease-out, transform 0.8s ease-out; /* 平滑过渡 */
            }
             @media (prefers-reduced-motion: reduce) {
                .explanation-container {
                    animation: none; /* 禁用动画 */
                    opacity: 1; /* 确保在无动画时可见 */
                    transform: translateY(0); /* 移除位移 */
                }
            }
            .explanation-container[data-aos="fade-up"].aos-animate { /* 覆盖 aos 动画效果 */
                opacity: 1;
                transform: translateY(0);
            }


            hr {
                border: none;
                border-top: 1px solid var(--border-color); /*  分割线颜色，使用 CSS 变量 */
                margin: 20px 0;
            }
            a {
                color: var(--explanation-border); /*  链接颜色，使用 CSS 变量 */
            }
            hr {
                border: none;
                border-top: 1px solid #ddd;
                margin: 20px 0;
            }
            .footer {
                text-align: center; /*  居中对齐 */
                margin-top: 30px;
                color: #aaa;
                font-size: 0.9em;
            }
            img {
                max-width: 100%; /*  图片最大宽度 100% */
                height: auto; /*  高度自适应 */
            }
            /*  下划线  */
            u {
                text-decoration: none;
                border-bottom: 1px solid black;
                display: inline-block;
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }

            /* 视频样式 */
            .video-section {
                margin-bottom: 30px; /* 视频区域与下方题目的距离 */
            }
            /* 视频卡片容器 */
            .video-card {
                background-color: var(--card-bg); /* 使用卡片背景色 */
                border: 1px solid var(--border-color); /* 使用通用边框颜色 */
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px; /* 视频卡片与下方按钮的距离 */
            }
            .video-title {
                text-align: center;
                padding: 15px 20px; /* 保持内边距 */
                font-weight: bold;
                font-size: 1.2em;
                border-bottom: 1px solid var(--border-color);
                margin-bottom: 10px;
            }

            /* 视频框容器 */
            .video-wrapper {
                background-color: var(--video-bg); /* 视频背景色 */
                overflow: hidden;
                margin: 0 auto; /* 水平居中 */
                max-width: 800px; /* 限制视频最大宽度 */
            }
            .video-container {
                position: relative;
                padding-top: 56.25%; /* 16:9 Aspect Ratio */
                height: 0;
                overflow: hidden;
            }
            .video-container iframe,
            .video-container video {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border: none; /* 移除iframe/video的边框 */
            }
            .video-selector {
                display: flex;
                justify-content: flex-start; /* 修改为 flex-start 左对齐按钮 */
                gap: 10px;
                padding: 10px 20px; /* 按钮区域内边距 */
                background-color: var(--card-bg); /* 按钮选择器背景色，与题目卡片一致 */
                border-radius: 0 0 10px 10px; /* 按钮选择器下圆角 */
                overflow-x: auto; /*  增加水平滚动条 */
                white-space: nowrap; /*  防止按钮换行 */
            }
            .video-selector button {
                background-color: var(--video-button-bg); /* 视频按钮背景色 */
                color: white;
                border: none;
                padding: 8px 15px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
                transition: background-color 0.3s ease;
                white-space: nowrap;
            }
            .video-selector button:hover {
                background-color: var(--video-button-hover); /* 视频按钮悬停色 */
            }
            .video-selector button.active {
                background-color: var(--video-button-active); /* 视频按钮激活色 */
                font-weight: bold;
            }


        </style>
        <script src="https://file.xinjiaoyu.com/pages/mathjax/MathJax.js?config=TeX-AMS-MML_SVG"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css" rel="stylesheet">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"></script>
    </head>
    <body>
    <script>
        AOS.init({
            duration: 800, // 缩短动画持续时间 - 优化点 1
            once: true, //  仅触发一次动画
            easing: 'ease-out-quart',
        });
    </script>
    """

    html_output += f"    <h1>{template_name}</h1>"

    # 添加微课视频播放部分
    if video_data:
        html_output += "<div class='video-section'>"
        html_output += "<div class='video-card'>"  # 视频卡片容器开始
        html_output += f"<div class='video-title'>对点微课视频</div>"  # 视频标题

        html_output += "<div class='video-wrapper'>"  # 视频框容器开始

        # 视频播放器
        first_video_url = video_data[0]['videoUrl']
        html_output += f"""
        <div class="video-container" data-aos='fade-up'>
            <video id="videoPlayer" controls src="{first_video_url}"></video>
        </div>
        """

        if len(video_data) > 1:
            html_output += "<div class='video-selector'>"
            for index, video in enumerate(video_data):
                video_name = video['videoName']
                video_url = video['videoUrl']
                html_output += f"""<button onclick="document.getElementById('videoPlayer').src='{video_url}';
                                                setActiveButton(this);">{video_name}</button>"""
            html_output += "</div>"
        html_output += "</div>"  #  视频框容器结束
        html_output += "</div>"  # 视频卡片容器结束 - 新增
        html_output += "</div>"  # .video-section 结束

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
                    put_text("🕒 开始获取题干内容...")
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
            html_output += f"<div class='question' data-aos='fade-up' data-aos-delay='{index * 100}' style='--index: {index};'><div class='question-header'>{header}</div>"  #  添加 data-aos-delay - 优化点 1
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
                        <div class='explanation-container' data-aos='fade-up' data-aos-delay='{index * 150}' style='--index: {index};'>
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

    html_output += """
    <script>
        function setActiveButton(button) {
            var buttons = document.querySelectorAll('.video-selector button');
            buttons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        }

        document.addEventListener('DOMContentLoaded', function() {
            var firstButton = document.querySelector('.video-selector button');
            if (firstButton) {
                firstButton.classList.add('active');
            }
        });
    </script>
    """

    # 关闭HTML标签
    html_output += "</body></html>"
    return html_output
