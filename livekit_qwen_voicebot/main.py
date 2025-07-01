import logging
from livekit_qwen_voicebot.voice_assistant import VoiceAssistant

logger = logging.getLogger("qwen-agent")
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    assistant = VoiceAssistant()
    print("语音助手已初始化。你可以在这里添加测试代码。")