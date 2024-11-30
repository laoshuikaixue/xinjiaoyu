# xinjiaoyu

本项目是新教育智能平台（[www.xinjiaoyu.com](http://www.xinjiaoyu.com)）的相关研究

---

# 项目简介

## `src/GetAnswer`:

该目录包含基于 PyWebIO 的工具，用于生成作业（智能题卡）答案的 HTML 页面。

## 使用指南

1. 克隆仓库：
   ```bash
   git clone https://github.com/laoshuikaixue/xinjiaoyu.git
   cd xinjiaoyu
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置变量：
   在 `src/GetAnswer/main.py` 文件的主函数中，填写您的用户名和密码，用于后续的请求验证。

4. 运行程序：
   运行 `main.py` 文件，打开提示网站，访问并提交解码后的二维码内容即可。

## 许可协议

本项目采用 [MIT License](LICENSE) 许可证。

---
