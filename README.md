# voiceassistant
## 🚀 启动方式

### 1. 安装依赖
```bash
pip install -r requirements.txt

###2. 创建 .env 配置文件
QWEN_API_KEY=sk-xxx
ALI_APPKEY=xxxxxx
ALI_TOKEN=xxxxxx

###3. 启动 Flask 服务
python app.py

###4. 浏览器访问
http://localhost:5000/

###支持功能

✅ Whisper 模型离线语音识别
✅ 接入 Qwen-turbo 大模型接口智能问答
✅ 接入 Qwen-turbo 大模型回答精简
✅ 阿里 TTS 语音合成（多角色）
✅ 插件机制，可扩展知识库/控制设备等（待开发）

🧩 TODO
 1、Websocket 接入 LiveKit 实时音频流
 2、支持 ChatFlow 插件对话机制
 3、支持模型热切换（文生文、多模态等）