Takway.AI Linux板载端侧Linux环境安装指南
=========

## 🖥️安装和运行：


### 1. 创建conda环境并安装依赖：

- 安装基础依赖项: 
```
sudo apt-get update
sudo apt-get install cmake g++ gcc portaudio19-dev
```

- Conda环境安装: 
```
conda create -n takway python=3.8
conda activate takway
```

- 安装项目依赖项：
```
pip install -r requirements/board_requirements.txt
```

### 2. 克隆项目到本地：

- `Takway`: 
```
// 克隆项目到本地 https or ssh
git clone https://github.com/Irvingao/takway_base.git or git clone git@github.com:Irvingao/takway_base.git
cd takway_base
pip install -v -e .
```


### 3. 运行项目：

#### 运行端侧前端：
```
conda activate takway
// 如果出错就按照出错信息用 pip 安装相应的库
python local_client.py 
```

如果出现以下输出，则表示运行成功，可以进行按键/语音交互：
```
Waiting for button press...
Waiting for hardware trigger.
Waiting for wake up...
```