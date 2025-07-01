import asyncio
import logging
from livekit_qwen_voicebot.voice_assistant import VoiceAssistant

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_voice_assistant():
    """测试语音助手功能"""
    print("=== 语音助手后端测试 ===")
    
    # 创建语音助手实例
    assistant = VoiceAssistant()
    
    print(f"1. 初始状态: 唤醒={assistant.is_awake}")
    print(f"2. 当前声音类型: {assistant.voice_type}")
    print(f"3. 对话历史数量: {len(assistant.conversation_history)}")
    
    # 测试1: 手动唤醒
    print("\n=== 测试1: 手动唤醒 ===")
    await assistant._wake_up()
    print(f"唤醒后状态: {assistant.is_awake}")
    
    # 测试2: 设置声音类型
    print("\n=== 测试2: 设置声音类型 ===")
    try:
        assistant.set_voice("male")
        print("声音类型设置成功: male")
    except Exception as e:
        print(f"设置声音类型失败: {e}")
    
    # 测试3: 测试Qwen API调用
    print("\n=== 测试3: 测试Qwen API调用 ===")
    try:
        test_question = "你好，请介绍一下你自己"
        print(f"测试问题: {test_question}")
        
        response = await assistant._call_qwen_api(test_question)
        print(f"Qwen API 回复: {response}")
        
        # 测试精简回答
        simplified = await assistant._simplify_response(response)
        print(f"精简后回答: {simplified}")
        
    except Exception as e:
        print(f"Qwen API 测试失败: {e}")
    
    # 测试4: 测试TTS生成
    print("\n=== 测试4: 测试TTS生成 ===")
    try:
        test_text = "你好，我是小鹅语音助手"
        print(f"测试文本: {test_text}")
        
        audio_data = await assistant._generate_speech(test_text)
        print(f"TTS生成成功，音频数据大小: {len(audio_data)} 字节")
        
        # 保存音频文件用于测试
        with open("test_audio.mp3", "wb") as f:
            f.write(audio_data)
        print("音频已保存为 test_audio.mp3")
        
    except Exception as e:
        print(f"TTS测试失败: {e}")
    
    # 测试5: 测试完整流程
    print("\n=== 测试5: 测试完整流程 ===")
    try:
        # 模拟用户问题
        test_question = "今天天气怎么样？"
        print(f"模拟用户问题: {test_question}")
        
        # 处理用户问题
        result = await assistant._process_user_question(test_question)
        
        if result:
            print(f"处理结果类型: {result['type']}")
            print(f"用户问题: {result['user_question']}")
            print(f"AI回答: {result['ai_response']}")
            print(f"音频数据大小: {len(result['audio'])} 字节")
            
            # 保存对话历史
            assistant.conversation_history.append({
                'question': result['user_question'],
                'response': result['ai_response'],
                'timestamp': result['timestamp']
            })
            
            print(f"对话历史已更新，当前数量: {len(assistant.conversation_history)}")
        else:
            print("处理结果为空")
            
    except Exception as e:
        print(f"完整流程测试失败: {e}")
    
    # 测试6: 测试状态获取
    print("\n=== 测试6: 测试状态获取 ===")
    status = assistant.get_status()
    print(f"助手状态: {status}")
    
    # 测试7: 测试休眠
    print("\n=== 测试7: 测试休眠 ===")
    await assistant._sleep()
    print(f"休眠后状态: {assistant.is_awake}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_voice_assistant()) 