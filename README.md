# xinjiaoyu

本项目是新教育智能平台（[www.xinjiaoyu.com](http://www.xinjiaoyu.com)）的相关研究

---

# 项目简介

## `src/GetAnswer`:

![image](https://github.com/user-attachments/assets/e76a3029-935e-40cd-9140-9665a633d51a)

![image](https://github.com/user-attachments/assets/65b39489-48d3-4ca9-9bbe-068a85c0ab04)

动画演示：

https://github.com/user-attachments/assets/4d81bc74-dde7-45bc-b525-a2598f3e58b0

该目录包含基于 PyWebIO 的工具，用于生成作业（智能题卡）答案的 HTML 页面。

生成的HTML文件可以用于部署静态网站 | Example：

https://gitlab-xinjiaoyu.lao-shui.top/

https://xinjiaoyu.laoshui.top/

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

   在 `src/GetAnswer/main.py` 文件的主函数中，填写你的用户名和密码，用于后续的请求验证。
   * **2024.12.27前后 新教育平台增加了登录时的验证码 ~~如果遇到验证码 请手动输入返回的数据（请求URL为: `https://www.xinjiaoyu.com/api/v3/server_system/auth/login` 需压缩成一行）~~**
   * **2024/12/31晚间 对于用于获取 template_id 的API疑似增加了客户端验证？现在网页端的请求头已经不能获取数据了 改为使用安卓端请求头 安卓端暂时没有验证码验证 移除了上述内容**
   * 注意：由于设计的原因，现思路为首先通过提交作业的接口 获取templateCode对应的paperID 再发送一遍请求解析 所以只能在允许提交作业时间段 以及你选修了该门学科才可以获取到paperID进行解析

4. 运行程序：
   运行 `main.py` 文件，打开提示网站，访问并提交解码后的二维码内容即可。

## 许可协议

本项目采用 [MIT License](LICENSE) 许可证。

---

# 鸣谢
https://github.com/LFWQSP2641/ZhiNengTiKa 本项目登录部分代码参考了此项目的加密、鉴权部分代码

---

### 写的比较粗糙 还有很多可以改进的地方
### 作者目前为高中在读 住校 只有周末有些许时间进行开发 故开源本项目

## PRs Welcome
