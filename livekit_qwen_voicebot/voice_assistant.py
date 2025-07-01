import asyncio
import logging
import whisper
import requests
import tempfile
import os
from datetime import datetime
from pydub import AudioSegment
import uuid
import base64

logger = logging.getLogger("voice-assistant")

class VoiceAssistant:
    def __init__(self):
        self.wake_word = "小鹅"
        self.sleep_word = "结束"
        self.is_awake = False
        self.is_speaking = False
        
        # 初始化组件
        self.stt_model = whisper.load_model("base")
        self.qwen_api_key = "sk-31dc4cbb431940ee8fb7b6a0678f9e4f"
        # 阿里云TTS参数
        self.ali_appkey = "BtWNoXUl0nePqZKS"
        self.ali_token = "532a40c8bf314b2d9a8d9167c90df7e5"
        
        # 声音设置（支持四种音色）
        self.voices = {
            "zhixiaobai": "zhixiaobai",      # 知小白
            "zhifeng_emo": "zhifeng_emo",  # 知锋_多情感
            "xiaogang": "xiaogang",        # 小刚
            "aimei": "aimei"               # 艾美
        }
        self.voice_type = "zhixiaobai"  # 默认知小白
        
        # 对话历史
        self.conversation_history = []
        self.last_activity = datetime.now()
        
    async def process_audio(self, audio_data: bytes):
        try:
            logger.info("开始语音转文字")
            text = await self._transcribe_audio(audio_data)
            logger.info(f"STT结果: {text}")
            if not text or text.strip() == "":
                logger.info("STT结果为空，返回None")
                return None
            logger.info(f"识别到文字: {text}")
            # 注释掉唤醒/休眠逻辑，直接进入问答
            # if not self.is_awake and self.wake_word in text:
            #     await self._wake_up()
            #     logger.info("检测到唤醒词，已唤醒")
            #     return {
            #         "type": "wake",
            #         "text": f"你好！我是{self.wake_word}，有什么可以帮助你的吗？",
            #         "timestamp": datetime.now().isoformat()
            #     }
            # if self.is_awake and self.sleep_word in text:
            #     await self._sleep()
            #     logger.info("检测到休眠词，已休眠")
            #     return {
            #         "type": "sleep",
            #         "text": "好的，我进入休眠状态了。说'小鹅'可以唤醒我。",
            #         "timestamp": datetime.now().isoformat()
            #     }
            # if not self.is_awake:
            #     logger.info("未唤醒，忽略输入")
            #     return None
            logger.info("进入用户问题处理流程")
            return await self._process_user_question(text)
        except Exception as e:
            logger.error(f"处理音频时出错: {str(e)}")
            return None
    
    async def _transcribe_audio(self, audio_data: bytes) -> str:
        """语音转文字，支持webm转wav，保存到audiofile目录，自动清理"""
        try:
            audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "audiofile"))
            os.makedirs(audio_dir, exist_ok=True)
            webm_path = os.path.join(audio_dir, f"{uuid.uuid4().hex}.webm")
            wav_path = webm_path.replace('.webm', '.wav')
            with open(webm_path, "wb") as f:
                f.write(audio_data)
            logger.info(f"已保存webm音频: {webm_path}, 大小: {os.path.getsize(webm_path)} 字节")
            # 转码为wav
            audio = AudioSegment.from_file(webm_path, format="webm")
            audio.export(wav_path, format="wav")
            logger.info(f"已转码为wav: {wav_path}, 大小: {os.path.getsize(wav_path)} 字节")
            # whisper识别
            result = self.stt_model.transcribe(wav_path, language="zh")
            text = result["text"] if isinstance(result["text"], str) else str(result["text"])
            logger.info(f"识别到文字: {text}")
            os.remove(webm_path)
            os.remove(wav_path)
            return text.strip()
        except Exception as e:
            logger.error(f"语音转文字失败: {str(e)}")
            return ""
    
    async def _wake_up(self):
        """唤醒助手"""
        self.is_awake = True
        self.last_activity = datetime.now()
        logger.info("助手已唤醒")
    
    async def _sleep(self):
        """休眠助手"""
        self.is_awake = False
        self.is_speaking = False
        logger.info("助手已休眠")
    
    async def _process_user_question(self, question: str):
        try:
            logger.info(f"开始处理用户问题: {question}")
            self.last_activity = datetime.now()
            
            # 调用Qwen大模型
            response = await self._call_qwen_api(question)
            logger.info(f"Qwen大模型回复: {response}")
            
            # 精简回答
            simplified_response = await self._simplify_response(response)
            logger.info(f"精简后回复: {simplified_response}")
            
            # 生成语音（如果TTS失败，只返回文本）
            try:
                audio_data = await self._generate_speech(simplified_response)
                logger.info(f"TTS音频生成成功，字节数: {len(audio_data)}")
                has_audio = True
            except Exception as e:
                logger.warning(f"TTS生成失败，只返回文本: {e}")
                audio_data = b""
                has_audio = False
            
            result = {
                "type": "response",
                "user_question": question,
                "ai_response": simplified_response,
                "timestamp": datetime.now().isoformat()
            }
            
            # 存入对话历史，实现上下文记忆
            self.conversation_history.append({
                'question': question,
                'response': simplified_response,
                'timestamp': result['timestamp']
            })
            # 只保留最近20轮
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            if has_audio:
                result["audio"] = base64.b64encode(audio_data).decode('utf-8')
            
            if result:
                logger.info(f"最终结果已生成，准备emit: type={result.get('type')}, user_question={result.get('user_question')}, ai_response={str(result.get('ai_response'))[:20]}")
            return result
            
        except Exception as e:
            logger.error(f"处理用户问题时出错: {str(e)}")
            return {
                "type": "error",
                "text": "抱歉，我遇到了一些问题，请稍后再试。",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _call_qwen_api(self, question: str) -> str:
        """调用Qwen API"""
        try:
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            headers = {
                "Authorization": f"Bearer {self.qwen_api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建对话历史
            messages = []
            for conv in self.conversation_history[-5:]:
                messages.append({"role": "user", "content": conv["question"]})
                messages.append({"role": "assistant", "content": conv["response"]})
            
            messages.append({"role": "user", "content": question})
            
            payload = {
                "model": "qwen-turbo",
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "result_format": "message",
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result["output"]["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Qwen API 调用失败: {response.text}")
                
        except Exception as e:
            logger.error(f"调用Qwen API失败: {str(e)}")
            raise
    
    async def _simplify_response(self, response: str) -> str:
        """精简回答"""
        try:
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            headers = {
                "Authorization": f"Bearer {self.qwen_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""请精简以下回答，去除冗余信息，保持核心内容，控制在100字以内：\n\n原文：{response}\n\n精简后的回答："""
            
            payload = {
                "model": "qwen-turbo",
                "input": {
                    "messages": [{"role": "user", "content": prompt}]
                },
                "parameters": {
                    "result_format": "message",
                    "max_tokens": 200,
                    "temperature": 0.3
                }
            }
            
            simplify_response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if simplify_response.status_code == 200:
                result = simplify_response.json()
                return result["output"]["choices"][0]["message"]["content"]
            else:
                return response
                
        except Exception as e:
            logger.error(f"精简回答失败: {str(e)}")
            return response
    
    async def _generate_speech(self, text: str) -> bytes:
        """使用阿里云TTS合成语音"""
        try:
            url = "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/tts"
            headers = {
                "X-NLS-Token": self.ali_token,
                "Content-Type": "application/json"
            }
            payload = {
                "appkey": self.ali_appkey,
                "text": text,
                "format": "mp3",
                "sample_rate": 16000,
                "voice": self.voices.get(self.voice_type, "zhixiaobai"),
                "volume": 50,
                "speech_rate": 0,
                "pitch_rate": 0
            }
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.headers.get("Content-Type", "").startswith("audio"):
                return response.content
            else:
                raise Exception(f"TTS API 调用失败: {response.text}")
        except Exception as e:
            logger.error(f"阿里云TTS生成失败: {str(e)}")
            raise
    
    def set_voice(self, voice_type: str):
        """设置声音类型"""
        if voice_type in self.voices:
            self.voice_type = voice_type
            logger.info(f"声音类型已设置为: {voice_type}")
        else:
            raise ValueError(f"不支持的声音类型: {voice_type}")
    
    def get_status(self):
        """获取助手状态"""
        return {
            "is_awake": self.is_awake,
            "is_speaking": self.is_speaking,
            "voice_type": self.voice_type,
            "last_activity": self.last_activity.isoformat(),
            "conversation_count": len(self.conversation_history)
        }
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info("对话历史已清空") 