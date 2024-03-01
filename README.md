简介：
======

基于对话大模型、二次元语音合成模型和语音识别模型的元神主题语音对话系统

项目描述：
==========

该项目是一个元神主题的语音对话系统，利用对话大模型、二次元语音合成模型和语音识别模型的结合，为用户提供与元神主题相关的语音对话体验。系统支持用户通过语音输入与系统进行对话，并通过语音合成将系统的回答转化为二次元风格的语音输出。

功能特点：

- 对话大模型：系统基于强大的对话大模型，能够实现自然、流畅的对话交互。
- 二次元语音合成模型：系统利用二次元语音合成模型，将系统的回答转化为具有元神主题风格的语音输出。
- 语音识别模型：系统具备语音识别功能，能够将用户的语音输入转化为文本形式，以便进行对话处理。
- 元神主题：系统以元神游戏为主题，提供与元神世界相关的对话体验，包括角色对话、任务交互等。

安装和运行：
============

1. 克隆项目到本地：

   ```
   git clone https://github.com/Irvingao/GenshinVoiceChat.git
   cd GenshinVoiceChat
   ```
2. 创建conda环境并安装依赖：

   ```
   conda create -n vits python=3.8
   // 安装Pytorch，其他版本参照：https://pytorch.org/get-started/previous-versions
   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 
   pip install tensorflow-gpu==2.5.0
   pip install -r requirements.txt
   ```

   - 安装vosk pip预编译库:

     - [Linux whl](https://github.com/alphacep/vosk-api/releases/download/v0.3.45/vosk-0.3.45-py3-none-linux_x86_64.whl)、[Win whl](https://github.com/alphacep/vosk-api/releases/download/v0.3.45/vosk-0.3.45-py3-none-win_amd64.whl)

     ```
     pip install xxx.whi
     ```
3. 下载相关模型文件:

   - Vosk语音识别模型：[vosk-model-small-cn-0.22.zip](https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip)
   - VITS语音合成模型：[vits-uma-genshin-honkai](https://huggingface.co/spaces/zomehwh/vits-uma-genshin-honkai/tree/main)
4. 配置星火大模型的API：

   - `main.py`中的 `appid`、`api_secret`、`api_key`，参考：[快速指引](https://www.xfyun.cn/doc/platform/quickguide.html#%E7%AC%AC%E4%B8%80%E6%AD%A5-%E6%B3%A8%E5%86%8C%E6%88%90%E4%B8%BA%E5%BC%80%E5%8F%91%E8%80%85)。
5. 运行项目：

   ```
   python main.py
   ```

表情




### 人物列表

- 可以通过脚本查看人物的序号:
  ```
  python list_characters.py
  ```

```

103: 可莉
104: 钟离
107: 达达利亚（公子）
111: 甘雨（椰羊）
115: 刻晴
119: 胡桃
120: 枫原万叶（万叶）
133: 八重神子（神子）
134: 神里绫人（绫人）
142: 纳西妲（草神）
```
