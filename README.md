Takway.AI
=========

### 🎃面向角色扮演功能的多模态交互系统🤖 [[飞书Link](https://lleeei6t29.feishu.cn/docx/BzVWd57K9oyVSixhTamcv4tSnHf)]

- 🦾前端：基于Linux端侧平台的语音、视觉交互系统，可以实现语音唤醒、语音输入、语音播放、表情互动等功能。其中语音输入框架如图所示：

![前端](docs/images/frontend-audio-pipeline.png)

- 🖲️后端：基于Python Flask框架的后端语音识别服务，可以实现流式语音识别、大模型流式生成、流式语音合成等功能。后端多进程框架如下图所示：

      待更新...

<!-- ![后端](docs/images/backend-framework.png) -->

---

### 📆项目更新日志


<details>
<summary>点击展开更新日志</summary>

- **2024.4.8**：
  1. 完成后端服务FastAPI的中数据库功能搭建。
- **2024.4.6**：
  1. 完成初版FastAPI后端服务搭建。
- **2024.3.21**：
  1. 完成基于[bida](https://github.com/xusenlinzy/bida)的商业模型API接入。
- **2024.3.14**：
  1. 接入[api-for-open-llm](https://github.com/xusenlinzy/api-for-open-llm)，支持本地部署模型，并统一模型服务API接口。
- **2024.3.13**：
  1. 接入[FunASR](https://github.com/alibaba-damo-academy/FunASR)，支持[modelscope](https://www.modelscope.cn/)上百种多语言语音识别模型。
- **2024.3.1**：
  1. 项目发布🔥🔥🔥🚀🚀🚀！
- **2024.2.27**：
  1. 调试并确认完成前后端通信数据格式；
  2. 初步确认大模型角色扮演系统运行。
- **2024.2.26**：
  1. 封装Character角色扮演代码封装 `RolyPlayingCharacterInfo`和 `RolyPlayingFunction`：
     ①支持自定义sys_prompt及调用；
     ②支持前端/后端character信息调用；
  2. 封装基于星火大模型的角色扮演对话系统；
  3. 封装基于本地Client的角色扮演系统；
  4. 重构前后端通信数据格式；
- **2024.2.25**：
  1. 完成板载前端系统和后端服务器对接；
     ①设置回答表情反应；
     ②设置角色扮演对话；
     ③问题：当语音流式播放时，动画播放卡顿，延迟高；
- **2024.2.22-2.24**：
  1. 完成后端服务器全流式多进程高并发并发系统 `TakwayApp`搭建；
     ①多线程支持流式获取并识别语音片段，等待完全识别后送入大模型生成部分；
     ②多线程支持流式大模型生成内容；
     ③多线程支持流式获取大模型输出，并输入到VITS端流式合成音频；
     ④流式返回音频数据，并实现本地快速播放；
- **2024.2.18**：
  1. 星火大模型代码封装 `SparkChatClient`：
     ①支持流式输出；
  2. VITS TTS代码封装 `TextToSpeech`：
     ①支持流式生成音频；
  3. 本地音频播放模块代码封装 `AudioPlayer`：
     ①支持VITS输出无损转换PCM；
     ②支持流式播放音频；
- **2024.2.17**：
  1. 本地语音系统代码封装 `PicovoiceRecorder`：
     ①增加VAD功能；
     ②增加 `Picovoice`的语音唤醒功能；
  2. 本地EMO表情管理模块代码封装 `EmoVideoPlayer`：
     ①增加随机wink功能；
     ②预留服务器端自定义表情接口；
  3. 完成本地Client客户端多进程系统搭建；

</details>

---

### 📌功能支持

- ✅ PicoVoice语音唤醒
- ✅ 后端全流式流式生成
- ✅ 支持FunASR框架和Modelscope模型库
- ✅ 支持本地模型API接入
- ✅ 支持闭源API模型统一接口接入 @鹤蓝
- 🟥 统一Logger & Error基类 @
- ✅ FastAPI高并发后端设计

### 🧩模块设计

```
├─takway                            # takway框架主目录
│  ├─*.py                               # 模块代码
│  ├─stt                                # 语音识别stt模块
│  ├─tts                                # 语音合成tts模块
│  │  ├─vits                                # vits模块
│  ├─llm                                # 大模型llm模块
│  ├─board                              # 硬件板载端模块
│  ├─clients                            # 硬件客户端模块
│  ├─apps                               # 旧版后端服务模块
│  ├─bida                               # bida模块
├─examples                          # 示例代码
├─tools                             # 工具脚本
├─main.py                           # AI后端服务启动文件
├─README.md                         # 本说明文件
├─docs                              # 帮助文档
├─requirements/                     # 相关依赖包
│   ├─board_requirements.txt            # 硬件板载端依赖
│   ├─requirements.txt                  # 服务器端依赖
├─vits_model                        # vits模型目录(必须)
│  ├─config.json                        # vits模型配置文件
│  ├─*.pth                              # vits模型权重文件
├─api-for-open-llm                  # 本地模型目录(可选)
│  ├─models                             # 本地模型目录
│  │  ├─internlm2-chat-1_8b             # (示例)
```

## 🖥️安装和运行：

### 1. 创建conda环境并安装Pytorch：

- 安装基础依赖项(Linux):

```
sudo apt-get update
sudo apt-get install cmake g++ gcc portaudio19-dev
```

- Conda环境安装(Win & Linux):

```
conda create -n takway python=3.8
```

- [pytorch](https://pytorch.org/get-started/previous-versions/):

```
// 安装Pytorch，其他版本参照：https://pytorch.org/get-started/previous-versions
// 最新版本：pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 
pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118
```

- 安装项目依赖项：

```
pip install -r requirements.txt
```

### 2. 克隆项目到本地并安装依赖：

- `Takway`:

```
// 克隆项目到本地 https or ssh
git clone https://github.com/Irvingao/takway_base.git or git clone git@github.com:Irvingao/takway_base.git
cd takway_base
pip install -v -e .
```

#### (1) LLM模型依赖项安装：

- 如果使用商业LLM API服务（如minimax等）:

  - 无需安装依赖项，直接进入[3. 下载相关模型文件步骤](#3-下载相关模型文件)。



- 如果使用商业LLM bida API（不使用则跳过）:
  <details>
  <summary>点击展开安装细节</summary>

  - `bida`:

  ```
  pip install -r bida/requirements.txt
  cd bida
  # pip install -e .
  ```
  </details>

- 如果使用本地LLM模型（不使用则跳过）：
  <details>
  <summary>点击展开安装细节</summary>
  - `api-for-open-llm`:

  ```
  git clone https://github.com/xusenlinzy/api-for-open-llm.git
  ```

  - 安装vllm-cuda118版本：

  ```
    pip install vllm==0.3.3
    export VLLM_VERSION=0.3.2
    export PYTHON_VERSION=38
    pip install https://github.com/vllm-project/vllm/releases/download/v${VLLM_VERSION}/vllm-${VLLM_VERSION}+cu118-cp${PYTHON_VERSION}-cp${PYTHON_VERSION}-manylinux1_x86_64.whl
    # Re-install xFormers with CUDA 11.8.
    pip install xformers==0.0.23.post1+cu118 --index-url https://download.pytorch.org/whl/cu118 --no-deps
  ```

  - 安装其他依赖项：

  ```
    pip install -r api-for-open-llm/requirements.txt
    pip uninstall transformer-engine -y
  ```

  </details>

### 3. 下载相关模型文件:

- VITS语音合成模型（必须）：[vits-uma-genshin-honkai](https://huggingface.co/spaces/zomehwh/vits-uma-genshin-honkai/tree/main)

  ```
  // 下载VITS语音合成模型
  git lfs install
  git clone https://huggingface.co/spaces/zomehwh/vits-uma-genshin-honkai.git
  ```
- InternLM模型（可选）：[internlm2-chat-1_8b](https://www.modelscope.cn/models/jayhust/internlm2-chat-1_8b/summary)
  <details>
  <summary>点击展开下载细节</summary>

  ```
  // 下载InternLM模型(Linux: `apt-get install git-lfs`)
  git lfs install
  git clone https://www.modelscope.cn/jayhust/internlm2-chat-1_8b.git
  ```
  </details>

### 4. 运行项目：

#### (1) 服务器后端(Linux)：

> 后端可以部署在具有GPU的云端/本地机器上。

- **启动后端服务**:

  ```
  python main.py
  ```

#### (2) 硬件客户端(Windows/Linux)：
- **启动硬件交互前端服务**:

  ```
  python local_client.py
  ```
