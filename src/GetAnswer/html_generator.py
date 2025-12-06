import re
from pywebio.output import put_text
from src.GetAnswer.AccountManager import AccountManager
from src.GetAnswer.api_client import get_content
from src.GetAnswer.config import BASE_URL
from loguru import logger

account_manager = AccountManager()


def json_to_html(json_data, template_name, video_data=None):
    """
    将JSON格式的作业数据转换为HTML页面。
    对内容、解析、答案都相同的连续小问进行合并显示，合并后的题目仅显示主题号。

    Args:
        json_data (dict): 包含作业数据的字典。
        template_name (str): 作业的名称，用于HTML标题。
        video_data (list, optional): 包含视频信息的列表。 Defaults to None.

    Returns:
        str: 生成的HTML字符串。
    """
    # 校验数据是否有效
    if not json_data or "data" not in json_data or not json_data["data"]:
        logger.error(f"无效或缺失的作业数据，无法生成页面: {template_name}")
        put_text("无效的作业数据，无法生成页面。")
        return ""

    # --- HTML头部和CSS样式 ---
    html_output = """
    <html>
    <head>
        <meta charset='utf-8'>
        <meta name="referrer" content="no-referrer">
    """
    html_output += f"    <title>{template_name} | LaoShui</title>"
    html_output += """
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            /* 根元素，定义全局 CSS 变量 */
            :root {
                --bg-color: #f8f9fa;
                --text-color: #333;
                --card-bg: #ffffff;
                --border-color: #e0e0e0;
                --button-primary: #4361ee;
                --button-primary-hover: #3a56d4;
                --button-secondary: #6c757d;
                --button-secondary-hover: #5a6268;
                --option-bg: #f0f7ff;
                --option-hover: #e1efff;
                --correct-bg: #e3f5e9;
                --correct-border: #4cc38a;
                --explanation-bg: #f0f7ff;
                --explanation-border: #4361ee;
                --video-bg: #f8f9fa;
                --video-border: #e0e0e0;
                --video-button-bg: #4361ee;
                --video-button-hover: #3a56d4;
                --video-button-active: #3a56d4;
                --question-header-color: #4361ee;
                --question-header-bar-color: #4cc38a;
                --header-gradient: linear-gradient(90deg, #4361ee, #3a56d4, #4cc38a, #7209b7);
                --card-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
                --card-hover-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
                --card-hover-transform: translateY(-5px);
                --animation-timing: cubic-bezier(0.34, 1.56, 0.64, 1);
            }
            /* 暗色模式 */
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg-color: #121212;
                    --text-color: #e0e0e0;
                    --card-bg: #1e1e1e;
                    --border-color: #333333;
                    --button-primary: #4361ee;
                    --button-primary-hover: #3a56d4;
                    --button-secondary: #495057;
                    --button-secondary-hover: #343a40;
                    --option-bg: #252836;
                    --option-hover: #2a2e3f;
                    --correct-bg: #1a3329;
                    --correct-border: #4cc38a;
                    --explanation-bg: #252836;
                    --explanation-border: #4361ee;
                    --video-bg: #1e1e1e;
                    --video-border: #333333;
                    --video-button-bg: #4361ee;
                    --video-button-hover: #3a56d4;
                    --video-button-active: #3a56d4;
                    --question-header-color: #4cc38a;
                    --question-header-bar-color: #4361ee;
                    --header-gradient: linear-gradient(90deg, #4361ee, #3a56d4, #4cc38a, #7209b7);
                    --card-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
                    --card-hover-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
                }
            }
            /* 动画定义 */
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            /* 全局重置 */
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            /* 基础样式 */
            body {
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-color);
                line-height: 1.8;
                padding: 20px;
                margin: 0 auto;
                max-width: 900px;
                border-radius: 16px;
                overflow-x: hidden;
                scroll-behavior: smooth;
                font-size: 1.05em;
                transition: background-color 0.3s ease, color 0.3s ease;
            }
            /* 响应式布局 */
            @media screen and (max-width: 768px) {
                body {
                    font-size: 1em;
                    padding: 15px;
                }
                h1 {
                    font-size: 2em;
                    margin-bottom: 20px;
                }
                .video-section {
                    margin-bottom: 20px;
                }
                .video-selector {
                    padding: 8px 10px;
                    gap: 5px;
                }
                .video-selector button {
                    font-size: 12px;
                    padding: 6px 10px;
                }
                .parent, .question, .explanation-container, .video-card {
                    padding: 15px;
                    margin-bottom: 20px;
                }
                /* 调整移动端题干底部间距 */
                .parent {
                    margin-bottom: 30px;
                }
            }

            /* 页面主标题 */
            h1 {
                text-align: center;
                font-size: 2.5em;
                font-weight: 800;
                background: var(--header-gradient);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 30px;
                letter-spacing: -0.5px;
                position: relative;
                padding-bottom: 10px;
            }
            h1::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 50%;
                transform: translateX(-50%);
                width: 80px;
                height: 4px;
                background: var(--header-gradient);
                border-radius: 2px;
            }
            /* 题干容器样式，增大底部间距 */
            .parent {
                background-color: var(--card-bg);
                border-radius: 16px;
                padding: 25px;
                margin-bottom: 40px; /* 增大题干和下方题目的间距 */
                box-shadow: var(--card-shadow);
                transition: all 0.4s var(--animation-timing);
                border: 1px solid var(--border-color);
            }
            .parent p { /* 题干内容段落样式 */
                 margin-bottom: 0; /* 移除题干段落的默认下边距 */
            }
            .parent:hover {
                box-shadow: var(--card-hover-shadow);
                transform: var(--card-hover-transform);
            }
            /* 题目容器样式 */
            .question {
                background-color: var(--card-bg);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 30px;
                box-shadow: var(--card-shadow);
                transition: all 0.4s var(--animation-timing);
                border: 1px solid var(--border-color);
                opacity: 0; /* 初始不可见，配合JS动画 */
                transform: translateY(20px); /* 初始向下偏移，配合JS动画 */
                transition: opacity 0.5s ease-out, transform 0.5s ease-out, box-shadow 0.4s var(--animation-timing);
            }
            .question:hover {
                box-shadow: var(--card-hover-shadow);
                transform: var(--card-hover-transform) translateY(-5px); /* 悬停时稍微上移 */
            }
            /* 减少动画抖动 */
            @media (prefers-reduced-motion: reduce) {
                .question, .explanation-container {
                    opacity: 1 !important;
                    transform: translateY(0) !important;
                    transition: none !important;
                }
            }

            /* 题目标题样式 */
            .question-header {
                font-weight: 700;
                margin-bottom: 18px;
                font-size: 1.2em;
                color: var(--question-header-color);
                padding: 0;
                border-radius: 0;
                display: flex;
                align-items: flex-start;
                position: relative;
                margin-left: 16px; /* 为左侧竖条留出空间 */
            }
            /* 题目标题左侧竖条 */
            .question-header::before {
                content: '';
                display: inline-block;
                position: absolute;
                top: 0;
                left: -16px;
                width: 4px;
                height: 100%;
                margin-right: 12px; /* 原为16px，稍微减少*/
                background-color: var(--question-header-bar-color);
                border-radius: 2px;
            }

            /* 题目内容段落 */
            .question p {
                font-size: 1.1em;
                margin-bottom: 15px;
                line-height: 1.6;
            }
            /* 选项列表 */
            ul {
                list-style-type: none;
                padding: 0;
            }
            /* 选项 */
            li {
                background: var(--option-bg);
                padding: 12px 15px;
                margin-bottom: 12px;
                border-radius: 8px;
                font-size: 1em;
                transition: all 0.3s ease;
                border: 1px solid transparent;
            }
            li:hover {
                background: var(--option-hover);
                transform: translateX(5px);
            }
            /* 正确选项高亮 */
            li.correct-option {
                background: var(--correct-bg);
                border: 1px solid var(--correct-border);
                font-weight: bold;
            }
            
            /* 断句题选项样式 */
            .segmentation-options {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
                list-style-type: none;
                padding: 10px 0;
                gap: 10px;
            }
            .segmentation-options li {
                flex: 0 1 auto;
                margin: 5px;
                min-width: 30px;
                text-align: center;
                padding: 8px 12px;
            }
            /* 在小屏幕上调整断句题选项 */
            @media screen and (max-width: 480px) {
                .segmentation-options {
                    justify-content: center;
                }
                .segmentation-options li {
                    min-width: 25px;
                    padding: 6px 10px;
                    margin: 3px;
                }
            }

            /* 填空题答案样式 */
            .fill-blank-answer {
                font-weight: bold;
                text-decoration: none;
                border-bottom: 2px solid var(--explanation-border);
                padding-bottom: 2px;
                color: var(--explanation-border);
                /* 允许答案换行 */
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }

            /* 题目解析容器 */
            .explanation-container {
                background-color: var(--explanation-bg);
                border-left: 4px solid var(--explanation-border);
                padding: 15px;
                margin-top: 20px;
                border-radius: 8px;
                overflow-wrap: break-word; /* 长单词或URL换行 */
                opacity: 0; /* 初始不可见，配合JS动画 */
                transform: translateY(20px); /* 初始向下偏移，配合JS动画 */
                transition: opacity 0.5s ease-out 0.15s, transform 0.5s ease-out 0.15s; /* 添加延迟 */
            }
            .explanation-header {
                font-weight: bold;
                margin-bottom: 8px;
                color: var(--explanation-border);
            }
            .explanation-content {
                line-height: 1.6;
                /* 允许解析内容换行 */
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }

            /* 分割线 */
            hr {
                border: none;
                border-top: 1px solid var(--border-color);
                margin: 40px 0; /* 增大分割线上下的间距 */
                opacity: 0.5;
            }
            /* 链接 */
            a {
                color: var(--explanation-border);
                text-decoration: none;
                transition: color 0.3s ease;
            }
            a:hover {
                text-decoration: underline;
            }
            /* 页脚 */
            .footer {
                text-align: center;
                margin-top: 40px;
                color: #888;
                font-size: 0.9em;
                padding: 20px 0;
                border-top: 1px solid var(--border-color);
            }
            /* 图片 */
            img {
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                display: block;
                margin: 15px auto;
            }
            /* 下划线 (如填空题) */
            u {
                text-decoration: none;
                border-bottom: 1px solid var(--text-color);
                display: inline-block; /* 允许换行 */
                white-space: pre-wrap; /* 保留空格并换行 */
                word-wrap: break-word; /* 强制长单词换行 */
                overflow-wrap: break-word; /* 同上 */
            }
            /* 返回顶部按钮 */
            .back-to-top {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: var(--button-primary);
                color: white;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                opacity: 0; /* 初始隐藏 */
                visibility: hidden; /* 初始隐藏 */
                transition: opacity 0.3s ease, transform 0.3s ease, visibility 0.3s ease;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                z-index: 1000;
                transform: translateY(20px); /* 初始向下偏移 */
            }
            .back-to-top.visible {
                opacity: 1;
                visibility: visible; /* 可见 */
                transform: translateY(0); /* 回到原位 */
            }
            .back-to-top:hover {
                background-color: var(--button-primary-hover);
                transform: translateY(-5px); /* 悬停上移 */
            }
        </style>
        <script src="https://file.xinjiaoyu.com/pages/mathjax/MathJax.js?config=TeX-AMS-MML_SVG"></script>
    </head>
    <body>
    """
    html_output += f"    <h1>{template_name}</h1>"

    # --- 题目处理逻辑 ---
    last_parent_id = None
    data = json_data["data"]
    i = 0
    processed_indices = set()

    try:
        while i < len(data):
            if i in processed_indices:
                i += 1
                continue

            item = data[i]
            current_question_data = item["question"]
            current_parent_id = current_question_data.get('parentId')

            # --- 题干处理 ---
            if current_parent_id and current_parent_id != "0":
                if current_parent_id != last_parent_id:
                    if last_parent_id:
                        html_output += "</div><hr>"
                    put_text(f"🕒 开始获取题干 {current_parent_id} 内容...")
                    try:
                        fetch_parent_content = get_content(
                            f"{BASE_URL}/api/v3/server_questions/questions/{current_parent_id}",
                            account_manager.get_dynamic_headers())
                        parent_content = fetch_parent_content.get('data', {}).get('content', '')
                        if parent_content:
                            html_output += f"<div class='parent'><p><b>题干: </b>{parent_content}</p>"
                        else:
                            logger.warning(f"题干 {current_parent_id} 内容为空或获取失败。")
                            html_output += f"<div class='parent'><p><b>题干 (ID: {current_parent_id}): </b> 内容为空或获取失败</p>"
                        last_parent_id = current_parent_id
                    except Exception as fetch_error:
                        logger.error(f"获取题干 {current_parent_id} 内容失败: {fetch_error}")
                        html_output += f"<div class='parent'><p><b>题干 (ID: {current_parent_id}): </b> 获取时发生错误</p>"
                        last_parent_id = current_parent_id
            elif last_parent_id:
                html_output += "</div><hr>"
                last_parent_id = None

            # --- 提取当前题目信息 ---
            current_question_number = current_question_data.get('questionNumber', '未知')
            current_content = str(current_question_data.get('content', ''))
            current_explanation = current_question_data.get('answerExplanation')
            current_answer = str(current_question_data.get('answer', '')).strip()

            # --- 尝试分组 ---
            is_groupable_type = "options" not in current_question_data or not current_question_data['options']
            match_current = re.match(r'(\d+)\((\d+)\)', str(current_question_number))

            group_end_index = i
            start_sub_num = -1  # 用于记录起始小问号，即使不显示范围，也用于判断是否成功分组
            main_num_str = ""  # 用于存储主题号

            if is_groupable_type and match_current:
                main_num_str = match_current.group(1)  # 获取主题号
                try:
                    start_sub_num = int(match_current.group(2))  # 尝试获取起始小问号

                    j = i + 1
                    while j < len(data):
                        next_item = data[j]
                        next_question_data = next_item["question"]
                        next_question_number = next_question_data.get('questionNumber', '')
                        next_content = str(next_question_data.get('content', ''))
                        next_explanation = next_question_data.get('answerExplanation')
                        next_answer = str(next_question_data.get('answer', '')).strip()
                        next_is_groupable = "options" not in next_question_data or not next_question_data['options']
                        match_next = re.match(r'(\d+)\((\d+)\)', str(next_question_number))

                        # 检查合并条件
                        if (next_is_groupable and match_next and
                                match_next.group(1) == main_num_str and  # 主题号相同
                                next_content == current_content and
                                next_explanation == current_explanation and
                                next_answer == current_answer):
                            try:
                                # 仍然需要解析下一个小问号以确认分组，但不用于显示
                                int(match_next.group(2))
                                group_end_index = j  # 更新分组结束索引
                                j += 1
                            except ValueError:
                                break  # 下一个小问号格式不对，停止分组
                        else:
                            break  # 条件不满足，停止查找
                except ValueError:
                    logger.warning(f"无法解析当前小问号: {current_question_number}，不进行分组。")
                    start_sub_num = -1  # 标记分组尝试失败

            # --- 根据是否分组成功生成HTML ---
            # 条件: group_end_index > i (至少合并了两个题目) 且 start_sub_num != -1 (第一个题目格式正确)
            if group_end_index > i and start_sub_num != -1:
                # --- 生成合并后的题目 (仅显示主题号) ---
                display_question_number_str = main_num_str  # 直接使用主题号
                logger.info(
                    f"主题号 {main_num_str} 下的多个小问内容、解析和答案均相同，合并显示为 第{display_question_number_str}题。")

                # 获取元数据 (从第一个题目获取)
                group_type_name = current_question_data.get('typeName', '未知类型')
                group_type_detail_name = current_question_data.get('typeDetailName', '')
                group_difficulty_name = current_question_data.get('difficultyName', '未知难度')

                # 构建合并后的题目标题 (仅用主题号)
                header_parts = [f"第{display_question_number_str}题", f"({group_type_name})"]
                if group_type_detail_name and group_type_name != group_type_detail_name:
                    header_parts.append(f"- {group_type_detail_name}")
                header_parts.append(f"难度 - {group_difficulty_name}")
                header = f"{' '.join(header_parts)} ："

                # 生成合并后的HTML块
                html_output += f"<div class='question' style='--index: {i};'><div class='question-header'>{header}</div>"
                html_output += f"<p>{current_content}</p>"
                html_output += f"<p><b>答案: </b><span class='fill-blank-answer'>{current_answer}</span></p>"
                if current_explanation:
                    html_output += f"""
                            <div class='explanation-container' style='--index: {i};'>
                                <div class='explanation-header'>解析:</div>
                                <div class='explanation-content'>{current_explanation}</div>
                            </div>
                            """
                html_output += "</div>"

                # 标记所有被合并的题目为已处理
                for k in range(i, group_end_index + 1):
                    processed_indices.add(k)
                i = group_end_index + 1  # 更新主循环索引

            else:
                # --- 生成单个题目 (保持原始题号) ---
                logger.debug(f"处理单个题目: {current_question_number}")

                single_type_name = current_question_data.get('typeName', '未知类型')
                single_type_detail_name = current_question_data.get('typeDetailName', '')
                single_difficulty_name = current_question_data.get('difficultyName', '未知难度')

                # 构建单个题目的标题 (使用原始题号 current_question_number)
                header_parts_single = [f"第{current_question_number}题", f"({single_type_name})"]
                if single_type_detail_name and single_type_name != single_type_detail_name:
                    header_parts_single.append(f"- {single_type_detail_name}")
                header_parts_single.append(f"难度 - {single_difficulty_name}")
                header_single = f"{' '.join(header_parts_single)} ："

                # 生成单个题目的HTML块
                html_output += f"<div class='question' style='--index: {i};'><div class='question-header'>{header_single}</div>"
                html_output += f"<p>{current_content}</p>"

                # 处理选项或答案
                if "options" in current_question_data and current_question_data['options']:
                    all_options_empty = all(
                        option.get('optionContent') is None or str(option.get('optionContent', '')).strip() == ''
                        for option in current_question_data["options"]
                    )
                    if all_options_empty:
                        html_output += "<ul class='segmentation-options'>"
                        for option in current_question_data["options"]:
                            option_letter = option.get('option', '').strip()
                            is_correct = option_letter in current_answer.replace(',', '').replace(' ', '')
                            css_class = 'correct-option' if is_correct else ''
                            html_output += f"<li class='{css_class}'><b>{option_letter}</b></li>"
                        html_output += "</ul>"
                    else:
                        html_output += "<ul>"
                        for option in current_question_data["options"]:
                            option_letter = option.get('option', '').strip()
                            option_content = option.get('optionContent', '')
                            is_correct = option_letter in current_answer.replace(',', '').replace(' ', '')
                            css_class = 'correct-option' if is_correct else ''
                            html_output += f"<li class='{css_class}'><b>{option_letter}:</b> {option_content}</li>"
                        html_output += "</ul>"
                elif current_answer:
                    html_output += f"<p><b>答案: </b><span class='fill-blank-answer'>{current_answer}</span></p>"
                else:
                    html_output += f"<p><b>答案: </b>暂无</p>"

                # 处理解析
                if current_explanation:
                    html_output += f"""
                            <div class='explanation-container' style='--index: {i};'>
                                <div class='explanation-header'>解析:</div>
                                <div class='explanation-content'>{current_explanation}</div>
                            </div>
                            """
                html_output += "</div>"

                processed_indices.add(i)
                i += 1  # 处理下一个

    except IndexError:
        logger.error("处理题目数据时发生索引越界错误，可能数据不完整。")
        put_text("处理题目数据时出错，请检查数据完整性。")
    except Exception as e:
        logger.error(f"生成HTML时发生未预料的错误: {e}", exc_info=True)
        put_text(f"生成HTML时出错: {e}")

    # --- HTML收尾和JS ---
    if last_parent_id:
        html_output += "</div><hr>"

    html_output += """
    <div class="back-to-top" id="backToTop" aria-label="返回顶部" title="返回顶部">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 19V5M5 12l7-7 7 7"/>
        </svg>
    </div>
    """
    html_output += """
    <div class="footer">
    <p>Powered By LaoShui @ 2025 | <a href="https://github.com/laoshuikaixue/xinjiaoyu" target="_blank" rel="noopener noreferrer">Github</a><br>
    温馨提示：仅供学习使用，请勿直接抄袭答案。</p>
    </div>
    """
    html_output += """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // --- 返回顶部按钮功能 ---
            const backToTopButton = document.getElementById('backToTop');
            if (backToTopButton) {
                const scrollThreshold = 300;
                let isButtonVisible = false;
                let scrollTimeout;
                const toggleBackToTopButton = () => {
                    const shouldBeVisible = window.scrollY > scrollThreshold;
                    if (shouldBeVisible !== isButtonVisible) {
                        backToTopButton.classList.toggle('visible', shouldBeVisible);
                        isButtonVisible = shouldBeVisible;
                    }
                };
                window.addEventListener('scroll', () => {
                    clearTimeout(scrollTimeout);
                    scrollTimeout = setTimeout(toggleBackToTopButton, 100);
                }, { passive: true });
                toggleBackToTopButton(); // Initial check
                backToTopButton.addEventListener('click', () => {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });
            }

            // --- 卡片悬停效果 (仅非触摸设备) ---
            const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0 || window.matchMedia("(pointer: coarse)").matches;
            if (!isTouchDevice) {
                document.querySelectorAll('.question, .parent').forEach(card => {
                    card.addEventListener('mouseenter', function() {
                        this.style.transform = 'var(--card-hover-transform)';
                        this.style.boxShadow = 'var(--card-hover-shadow)';
                    });
                    card.addEventListener('mouseleave', function() {
                        this.style.transform = '';
                        this.style.boxShadow = '';
                    });
                });
            }

            // --- 题目加载动画 (Intersection Observer) ---
            if ('IntersectionObserver' in window) {
                const observerOptions = { root: null, rootMargin: '0px', threshold: 0.1 };
                const intersectionCallback = (entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const target = entry.target;
                            target.style.opacity = '1';
                            target.style.transform = 'translateY(0)';
                            const explanation = target.querySelector('.explanation-container');
                            if (explanation) {
                                explanation.style.opacity = '1';
                                explanation.style.transform = 'translateY(0)';
                            }
                            observer.unobserve(target);
                        }
                    });
                };
                const questionObserver = new IntersectionObserver(intersectionCallback, observerOptions);
                document.querySelectorAll('.question').forEach(question => {
                    // Initial styles are set in CSS (opacity: 0, transform: translateY(20px))
                    questionObserver.observe(question);
                });
            } else {
                console.warn("浏览器不支持 IntersectionObserver，题目加载动画未启用。");
                document.querySelectorAll('.question, .explanation-container').forEach(el => {
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                });
            }

            // --- MathJax 排版 ---
             if (typeof MathJax !== 'undefined') {
                 // Delay typesetting slightly to allow elements to become visible
                 setTimeout(() => {
                      MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
                 }, 100); // Adjust delay if needed
             }
        });
    </script>
    """

    html_output += "</body></html>"
    return html_output
