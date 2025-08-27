# 新教育智能平台研究项目

本项目是新教育智能平台（[www.xinjiaoyu.com](http://www.xinjiaoyu.com)）的相关研究工具集。

---

## 项目简介

### `src/GetAnswer` 模块

![界面截图1](https://github.com/user-attachments/assets/de189098-fb5c-4887-a990-5dd8a64c7c67)
![界面截图2](https://github.com/user-attachments/assets/e76a3029-935e-40cd-9140-9665a633d51a)
![界面截图3](https://github.com/user-attachments/assets/65b39489-48d3-4ca9-9bbe-068a85c0ab04)

该目录包含基于 PyWebIO 的工具，用于生成作业（智能题卡）答案的 HTML 页面。生成的 HTML 文件可以用于部署静态网站。

**生成效果示例网站：**
- https://xinjiaoyu.laoshui.top/

## 使用指南

### 1. 克隆仓库
```bash
git clone https://github.com/laoshuikaixue/xinjiaoyu.git
cd xinjiaoyu
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置变量
在 `src/GetAnswer/main.py` 文件的主函数中，填写你的用户名和密码，用于后续的请求验证。

> **部分过程：**
> - 2024年12月27日前后，新教育平台增加了登录时的验证码
> - 2024年12月31日晚间，获取 template_id 的API疑似增加了客户端验证，现已改为使用小程序/安卓端请求头
> - 2025年不知何时，新教育加入了动态safefcode，并对Encrypt字段进行验证（加了个寂寞，safefcode解密之后还是jbyxinjiaoyu）
> - 注意：由于设计原因，当前实现需要先通过提交作业接口获取templateCode对应的paperID，因此只能在允许提交作业的时间段内，并且你选修了该门学科的情况下才能获取paperID进行解析

### 4. 运行程序
运行 `main.py` 文件，打开提示的网站地址，访问并提交解码后的题卡二维码内容即可。

## 许可协议

本项目采用 [GPL-3.0](LICENSE) 许可证。

---

## 鸣谢

感谢 [ZhiNengTiKa](https://github.com/LFWQSP2641/ZhiNengTiKa) 项目，本项目的代码参考了其加密和鉴权部分的实现。

## 数据获取流程图

```mermaid
flowchart TD
    A[用户启动程序] --> B[初始化AccountManager]
    B --> C[用户登录]
    C --> D{登录成功?}
    D -->|否| E[显示错误信息]
    E --> C
    D -->|是| F[保存登录信息]
    F --> G[启动Web服务器]
    G --> H[用户输入模板编号]
    
    H --> I[检查文件是否存在]
    I -->|存在| J[直接提供下载]
    I -->|不存在| K[开始数据获取流程]
    
    K --> L[获取微课视频信息]
    L --> M[调用get_video_urls]
    M --> N[调用generic_api_request]
    N --> O[构建请求URL和头部]
    O --> P[发送API请求]
    P --> Q{统一响应检查}
    Q -->|code=200且有data| R[返回视频数据]
    Q -->|code=410或登录失效| S[自动重新登录]
    Q -->|其他错误| T[记录错误并返回None]
    
    S --> U[调用check_and_relogin]
    U --> V{重新登录成功?}
    V -->|是| W[重试API请求]
    V -->|否| X[返回失败]
    W --> P
    
    R --> Y[获取模板数据]
    T --> Y
    X --> Y
    Y --> Z[调用get_template_data]
    Z --> AA[调用generic_api_request]
    AA --> BB[构建模板请求URL]
    BB --> CC[发送API请求]
    CC --> DD{统一响应检查}
    DD -->|code=200且有data| EE[返回模板数据]
    DD -->|登录失效| FF[自动重新登录并重试]
    DD -->|其他错误| GG[返回失败]
    
    EE --> HH[解析模板信息]
    HH --> II[获取templateId和templateName]
    II --> JJ[获取作业答案]
    JJ --> KK[调用get_homework_answers]
    KK --> LL[调用generic_api_request]
    LL --> MM[构建答案请求URL]
    MM --> NN[发送API请求]
    NN --> OO{统一响应检查}
    OO -->|code=200| PP[返回答案数据]
    OO -->|登录失效| QQ[自动重新登录并重试]
    OO -->|其他错误| RR[返回失败]
    
    PP --> SS[生成HTML内容]
    SS --> TT[调用json_to_html]
    TT --> UU[保存HTML文件]
    UU --> VV[显示成功信息]
    VV --> WW[提供文件下载]
    WW --> XX[等待用户操作]
    XX --> H
    
    GG --> YY[显示错误信息]
    RR --> YY
    YY --> H
    
    subgraph "请求处理"
        ZZ[generic_api_request通用函数]
        ZZ --> AAA[统一错误处理]
        ZZ --> BBB[统一重试逻辑]
        ZZ --> CCC[统一登录失效检测]
        ZZ --> DDD[统一日志记录]
    end
    
    subgraph "加密组件"
        EEE[XinjiaoyuEncryptioner]
        EEE --> FFF[get_dynamic_encrypt]
        FFF --> GGG[AES解密safe_code]
        GGG --> HHH[生成MD5哈希]
        HHH --> III[返回加密字符串]
    end
    
    subgraph "账户管理"
        JJJ[AccountManager]
        JJJ --> KKK[login登录]
        JJJ --> LLL[get_dynamic_headers]
        JJJ --> MMM[check_current_account_valid]
        LLL --> EEE
    end
    
    subgraph "API客户端"
        NNN[api_client]
        NNN --> OOO[get_content]
        OOO --> PPP[发送HTTP请求]
        PPP --> QQQ[处理响应]
    end
    
    N --> ZZ
    AA --> ZZ
    LL --> ZZ
    O --> LLL
    LLL --> EEE
    P --> OOO
    CC --> OOO
    NN --> OOO
```