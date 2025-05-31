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

            /* 视频区域 */
            .video-section {
                margin-bottom: 50px;
                /* 初始动画状态 */
                opacity: 1; /* 改为默认可见 */
                transform: translateY(0); /* 移除初始偏移 */
                animation: fadeInUp 0.6s var(--animation-timing) forwards;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            /* 视频播放区域和列表的布局容器 */
            @media screen and (min-width: 768px) {
                .video-layout {
                    display: grid;
                    grid-template-columns: 70% 30%;
                    gap: 20px;
                }
            }
            /* 视频卡片容器 */
            .video-card {
                background-color: var(--card-bg);
                border-radius: 20px;
                overflow: hidden;
                box-shadow: var(--card-shadow);
                border: 1px solid var(--border-color);
                transition: all 0.4s var(--animation-timing);
                display: flex;
                flex-direction: column;
            }
            .video-card:hover {
                box-shadow: var(--card-hover-shadow);
                transform: var(--card-hover-transform);
            }
            .video-title {
                text-align: center;
                padding: 20px;
                font-weight: 700;
                font-size: 1.3em;
                border-bottom: 1px solid var(--border-color);
                margin-bottom: 0;
                background: var(--explanation-bg);
                color: var(--question-header-color);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            .video-title svg {
                width: 24px;
                height: 24px;
                fill: currentColor;
            }

            /* 视频播放器外部包裹 */
            .video-wrapper {
                background-color: var(--video-bg);
                overflow: hidden;
                margin: 0 auto;
                max-width: 100%;
                flex-grow: 1;
                position: relative;
            }
            /* 视频播放器容器 (保持16:9) */
            .video-container {
                position: relative;
                padding-top: 56.25%; /* 16:9 Aspect Ratio */
                height: 0;
                overflow: hidden;
                background-color: #000; /* 视频加载时背景 */
                border-radius: 0;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                z-index: 1; /* 确保视频在前面 */
            }
            .video-container iframe,
            .video-container video {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border: none;
                object-fit: contain;
                background-color: #000;
                z-index: 1;
            }
            /* 视频控制栏 */
            .video-controls {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
                padding: 30px 20px 15px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                opacity: 1; /* 改为默认可见 */
                transition: opacity 0.3s ease;
                z-index: 2; /* 确保控制栏在视频上方 */
            }
            .video-wrapper:hover .video-controls {
                opacity: 1;
            }
            .video-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: rgba(255,255,255,0.2);
                cursor: pointer;
                z-index: 3; /* 确保进度条在最上方 */
            }
            .video-progress-filled {
                background: var(--video-button-bg);
                width: 0;
                height: 100%;
                position: absolute;
                transition: width 0.1s linear;
            }
            
            /* 视频列表区域 */
            .video-list {
                background-color: var(--card-bg);
                border-radius: 20px;
                overflow: hidden;
                box-shadow: var(--card-shadow);
                border: 1px solid var(--border-color);
                display: flex;
                flex-direction: column;
                max-height: 400px;
                z-index: 1; /* 确保列表在前面 */
                position: relative; /* 确保z-index生效 */
            }
            .video-list-header {
                padding: 15px 20px;
                font-weight: 600;
                font-size: 1.1em;
                background: var(--explanation-bg);
                color: var(--question-header-color);
                border-bottom: 1px solid var(--border-color);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .video-list-header svg {
                width: 18px;
                height: 18px;
                fill: currentColor;
            }
            .video-list-container {
                overflow-y: auto;
                padding: 10px;
                flex-grow: 1;
                scrollbar-width: thin;
                scrollbar-color: var(--border-color) transparent;
            }
            .video-list-container::-webkit-scrollbar {
                width: 6px;
            }
            .video-list-container::-webkit-scrollbar-track {
                background: transparent;
            }
            .video-list-container::-webkit-scrollbar-thumb {
                background-color: var(--border-color);
                border-radius: 6px;
            }
            
            /* 视频列表项 */
            .video-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 15px;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.2s ease;
                margin-bottom: 8px;
                background: var(--option-bg);
                border: 1px solid transparent;
            }
            .video-item:hover {
                background: var(--option-hover);
                transform: translateX(5px);
            }
            .video-item.active {
                background: var(--explanation-bg);
                border-color: var(--explanation-border);
                font-weight: 500;
            }
            .video-item-thumbnail {
                width: 80px;
                height: 45px;
                background-color: #000;
                border-radius: 6px;
                overflow: hidden;
                flex-shrink: 0;
                position: relative;
            }
            .video-item-thumbnail::before {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 0;
                height: 0;
                border-style: solid;
                border-width: 8px 0 8px 16px;
                border-color: transparent transparent transparent white;
                z-index: 1;
                opacity: 0.8;
            }
            .video-item-thumbnail::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.3);
            }
            .video-item.active .video-item-thumbnail::before {
                border-width: 0 0 0 0;
                border-style: double;
                border-color: transparent transparent transparent transparent;
                width: 12px;
                height: 12px;
                background: white;
            }
            .video-item-info {
                flex-grow: 1;
                overflow: hidden;
            }
            .video-item-title {
                font-size: 0.9em;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                margin-bottom: 4px;
            }
            .video-item-duration {
                font-size: 0.75em;
                color: var(--button-secondary);
            }
            
            /* 响应式调整 */
            @media screen and (max-width: 767px) {
                .video-layout {
                    display: flex !important;
                    flex-direction: column !important;
                    gap: 20px !important;
                }
                .video-list {
                    max-height: 300px !important;
                }
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

    # --- 视频处理 - 现代设计 ---
    if video_data:
        html_output += "<div class='video-section' style='margin-bottom:50px; opacity:1; display:flex; flex-direction:column; gap:20px;'>"
        html_output += "<div class='video-layout' style='display:grid; grid-template-columns:70% 30%; gap:20px;'>"
        
        # 视频播放器卡片
        html_output += "<div class='video-card' style='background-color:var(--card-bg); border-radius:20px; overflow:hidden; box-shadow:var(--card-shadow); border:1px solid var(--border-color); display:flex; flex-direction:column;'>"
        html_output += f"""
        <div class='video-title' style='text-align:center; padding:20px; font-weight:700; font-size:1.3em; border-bottom:1px solid var(--border-color); margin-bottom:0; background:var(--explanation-bg); color:var(--question-header-color); display:flex; align-items:center; justify-content:center; gap:10px;'>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style='width:24px; height:24px; fill:currentColor;'><path d="M8 5v14l11-7z"/></svg>
            对点微课视频
        </div>
        """
        html_output += "<div class='video-wrapper' style='background-color:var(--video-bg); overflow:hidden; margin:0 auto; max-width:100%; flex-grow:1; position:relative;'>"
        first_video_url = video_data[0]['videoUrl']
        html_output += f"""
        <div class="video-container" style="position:relative; padding-top:56.25%; height:0; overflow:hidden; background-color:#000; border-radius:0; box-shadow:0 10px 30px rgba(0,0,0,0.1); z-index:1;">
            <video id="videoPlayer" controls="controls" autoplay="false" preload="auto" src="{first_video_url}" style="display:block !important; visibility:visible !important; width:100% !important; height:100% !important; position:absolute !important; top:0 !important; left:0 !important; object-fit:contain !important; background-color:#000 !important; z-index:10 !important;"></video>
            <!-- 备用iframe方案 -->
            <iframe id="videoIframe" src="{first_video_url}" style="display:none; width:100%; height:100%; position:absolute; top:0; left:0; border:none; z-index:9;"></iframe>
        </div>
        <div class="video-controls" style="position:absolute; bottom:0; left:0; right:0; background:linear-gradient(to top, rgba(0,0,0,0.7), transparent); padding:30px 20px 15px; display:flex; align-items:center; justify-content:space-between; opacity:1; z-index:2;">
            <div class="video-progress" style="position:absolute; bottom:0; left:0; width:100%; height:4px; background:rgba(255,255,255,0.2); cursor:pointer; z-index:3;">
                <div class="video-progress-filled" style="background:var(--video-button-bg); width:0; height:100%; position:absolute; transition:width 0.1s linear;"></div>
            </div>
        </div>
        """
        html_output += "</div>"
        html_output += "</div>"
        
        # 视频列表卡片
        html_output += "<div class='video-list' style='background-color:var(--card-bg); border-radius:20px; overflow:hidden; box-shadow:var(--card-shadow); border:1px solid var(--border-color); display:flex; flex-direction:column; max-height:400px; z-index:1; position:relative;'>"
        html_output += f"""
        <div class='video-list-header' style='padding:15px 20px; font-weight:600; font-size:1.1em; background:var(--explanation-bg); color:var(--question-header-color); border-bottom:1px solid var(--border-color); display:flex; align-items:center; gap:8px;'>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style='width:18px; height:18px; fill:currentColor;'><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/></svg>
            视频列表
        </div>
        """
        html_output += "<div class='video-list-container' style='overflow-y:auto; padding:10px; flex-grow:1;'>"
        
        # 生成视频列表项
        for index, video in enumerate(video_data):
            video_name = video['videoName']
            video_url = video['videoUrl']
            active_class = " active" if index == 0 else ""
            # 假设每个视频5分钟，实际项目中可以从视频数据中获取
            duration = "05:00"
            
            html_output += f"""
            <div class="video-item{active_class}" data-video-url="{video_url}" style="display:flex; align-items:center; gap:12px; padding:12px 15px; border-radius:10px; cursor:pointer; margin-bottom:8px; background:var(--option-bg);">
                <div class="video-item-thumbnail" style="width:80px; height:45px; background-color:#000; border-radius:6px; flex-shrink:0;"></div>
                <div class="video-item-info" style="flex-grow:1; overflow:hidden;">
                    <div class="video-item-title" style="font-size:0.9em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{video_name}</div>
                    <div class="video-item-duration" style="font-size:0.75em;">{duration}</div>
                </div>
            </div>
            """
        
        html_output += "</div>"
        html_output += "</div>"
        
        html_output += "</div>"
        html_output += "</div>"

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
                            account_manager.get_headers())
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
                        html_output += "<ul style='display: flex; justify-content: space-around; list-style-type: none; padding: 10px 0;'>"
                        for option in current_question_data["options"]:
                            option_letter = option.get('option', '').strip()
                            is_correct = option_letter in current_answer.replace(',', '').replace(' ', '')
                            css_class = 'correct-option' if is_correct else ''
                            # 移除背景样式覆盖，使用CSS类中定义的样式
                            html_output += f"<li class='{css_class}' style='width: auto; margin: 0 5px;'><b>{option_letter}</b></li>"
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
    <p>GitHub: <a href="https://github.com/laoshuikaixue/xinjiaoyu" target="_blank" rel="noopener noreferrer">https://github.com/laoshuikaixue/xinjiaoyu</a><br>
    温馨提示：仅供学习使用，请勿直接抄袭答案。</p>
    </div>
    """
    html_output += """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // 检测视频格式并选择合适的播放方式
            function detectVideoFormat(url) {
                // 检查是否是m3u8格式
                if (url && url.includes('.m3u8')) {
                    return 'hls';
                }
                // 检查是否是mp4格式
                else if (url && url.includes('.mp4')) {
                    return 'mp4';
                }
                // 其他格式可能需要特殊处理
                else {
                    return 'other';
                }
            }
            
            // 根据视频格式选择播放方式
            function playVideoByFormat(url, videoPlayer, videoIframe) {
                const format = detectVideoFormat(url);
                console.log('检测到视频格式:', format, '视频URL:', url);
                
                if (format === 'mp4') {
                    // MP4格式使用video标签播放
                    videoPlayer.style.display = 'block';
                    videoIframe.style.display = 'none';
                    videoPlayer.src = url;
                    videoPlayer.load();
                    return 'video';
                } else {
                    // 其他格式使用iframe播放
                    videoPlayer.style.display = 'none';
                    videoIframe.style.display = 'block';
                    videoIframe.src = url;
                    return 'iframe';
                }
            }
            // --- 现代视频播放器功能 ---
            const videoPlayer = document.getElementById('videoPlayer');
            const videoListContainer = document.querySelector('.video-list-container');
            const videoProgress = document.querySelector('.video-progress');
            const videoProgressFilled = document.querySelector('.video-progress-filled');
            
            // 确保视频元素正确显示
            if (videoPlayer) {
                const videoIframe = document.getElementById('videoIframe');
                
                // 强制设置视频元素样式
                videoPlayer.style.display = 'block';
                videoPlayer.style.visibility = 'visible';
                videoPlayer.style.width = '100%';
                videoPlayer.style.height = '100%';
                videoPlayer.style.position = 'absolute';
                videoPlayer.style.top = '0';
                videoPlayer.style.left = '0';
                videoPlayer.style.zIndex = '10';
                videoPlayer.style.backgroundColor = '#000';
                
                // 根据视频格式选择播放方式
                if (videoPlayer.src) {
                    playVideoByFormat(videoPlayer.src, videoPlayer, videoIframe);
                }
                
                // 监听视频加载事件
                videoPlayer.addEventListener('loadeddata', function() {
                    console.log('视频已加载');
                });
                
                // 监听视频错误事件
                videoPlayer.addEventListener('error', function(e) {
                    console.error('视频加载错误:', e);
                    // 尝试使用iframe作为备用方案
                    if (videoIframe && videoPlayer.src) {
                        console.log('视频加载错误，切换到iframe模式');
                        videoPlayer.style.display = 'none';
                        videoIframe.style.display = 'block';
                        videoIframe.src = videoPlayer.src;
                    }
                });
                
                // 检查视频是否可以播放
                setTimeout(() => {
                    if (videoPlayer.readyState === 0 && videoPlayer.style.display !== 'none') {
                        console.log('视频未能加载，尝试备用方案');
                        if (videoIframe && videoPlayer.src) {
                            videoPlayer.style.display = 'none';
                            videoIframe.style.display = 'block';
                            videoIframe.src = videoPlayer.src;
                        }
                    }
                }, 2000);
            }
            
            // 视频列表点击事件
            if (videoPlayer && videoListContainer) {
                videoListContainer.addEventListener('click', function(event) {
                    const videoItem = event.target.closest('.video-item');
                    if (!videoItem) return;
                    
                    const videoUrl = videoItem.getAttribute('data-video-url');
                    if (videoUrl && videoPlayer.src !== videoUrl) {
                        const videoIframe = document.getElementById('videoIframe');
                        
                        // 根据视频格式选择播放方式
                        const playerType = playVideoByFormat(videoUrl, videoPlayer, videoIframe);
                        console.log('切换视频，使用播放器类型:', playerType);
                        
                        // 尝试自动播放
                        setTimeout(() => {
                            if (playerType === 'video') {
                                videoPlayer.play().catch(e => {
                                    console.warn("自动播放失败:", e);
                                    // 如果播放失败，尝试使用iframe
                                    if (videoIframe) {
                                        videoPlayer.style.display = 'none';
                                        videoIframe.style.display = 'block';
                                    }
                                });
                                
                                // 检查视频是否可以播放
                                setTimeout(() => {
                                    if (videoPlayer.readyState === 0 && videoPlayer.style.display !== 'none') {
                                        console.log('视频未能加载，尝试备用方案');
                                        if (videoIframe) {
                                            videoPlayer.style.display = 'none';
                                            videoIframe.style.display = 'block';
                                        }
                                    }
                                }, 1000);
                            }
                        }, 100);
                        
                        // 更新激活状态
                        videoListContainer.querySelectorAll('.video-item').forEach(item => {
                            item.classList.remove('active');
                        });
                        videoItem.classList.add('active');
                        
                        // 滚动到可视区域
                        videoItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                });
            }
            
            // 视频进度条功能
            if (videoPlayer && videoProgress && videoProgressFilled) {
                // 更新进度条
                videoPlayer.addEventListener('timeupdate', function() {
                    const percent = (videoPlayer.currentTime / videoPlayer.duration) * 100;
                    videoProgressFilled.style.width = `${percent}%`;
                });
                
                // 点击进度条跳转
                videoProgress.addEventListener('click', function(e) {
                    const progressTime = (e.offsetX / videoProgress.offsetWidth) * videoPlayer.duration;
                    videoPlayer.currentTime = progressTime;
                });
            }
            
            // 视频缩略图预加载（实际项目中可以使用真实缩略图）
            document.querySelectorAll('.video-item-thumbnail').forEach((thumbnail, index) => {
                // 这里可以设置真实的缩略图，如果有的话
                // 示例：thumbnail.style.backgroundImage = `url(${thumbnailUrls[index]})`;
            });
            
            // 视频播放时间格式化函数
            function formatTime(seconds) {
                const minutes = Math.floor(seconds / 60);
                const remainingSeconds = Math.floor(seconds % 60);
                return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
            }
            
            // 如果有视频时长数据，可以在这里设置
            if (videoPlayer.readyState > 0) {
                updateVideoDurations();
            } else {
                videoPlayer.addEventListener('loadedmetadata', updateVideoDurations);
            }
            
            function updateVideoDurations() {
                // 实际项目中，这里可以从视频元数据中获取真实时长
                // 示例代码，实际使用时可能需要调整
                const duration = formatTime(videoPlayer.duration);
                document.querySelector('.video-item.active .video-item-duration').textContent = duration;
            }

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
                document.querySelectorAll('.question, .parent, .video-card').forEach(card => {
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
