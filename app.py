import os
import logging
import base64
import json
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import asyncio
import threading
from io import BytesIO

# 导入我们的语音助手
from livekit_qwen_voicebot.voice_assistant import VoiceAssistant

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)  # 允许跨域请求

# 创建SocketIO实例
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# 全局语音助手实例
voice_assistant = VoiceAssistant()

# 设置API Keys
os.environ['QWEN_API_KEY'] = 'sk-31dc4cbb431940ee8fb7b6a0678f9e4f'
os.environ['ELEVENLABS_API_KEY'] = 'sk_f3860d0ead8c7b42ee46b4c11d4233f95a3ab56b15c54661'

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取机器人状态"""
    try:
        status = voice_assistant.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/voice', methods=['POST'])
def set_voice():
    """设置声音类型"""
    try:
        data = request.get_json()
        voice_type = data.get('voice_type', 'female')
        
        voice_assistant.set_voice(voice_type)
        
        return jsonify({
            'success': True,
            'message': f'声音类型已设置为: {voice_type}'
        })
    except Exception as e:
        logger.error(f"设置声音失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio', methods=['POST'])
def process_audio():
    """处理音频输入"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有找到音频文件'
            }), 400
        
        audio_file = request.files['audio']
        # 读取音频数据
        audio_data = audio_file.read()
        
        # 同步处理音频
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(voice_assistant.process_audio(audio_data))
        loop.close()
        
        if result:
            # audio字段已为base64字符串，直接重命名为audio_base64
            if 'audio' in result:
                result['audio_base64'] = result['audio']
                del result['audio']
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': '未能处理音频'
            }), 500
    except Exception as e:
        logger.error(f"处理音频请求失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """清空对话历史"""
    try:
        voice_assistant.clear_history()
        return jsonify({
            'success': True,
            'message': '对话历史已清空'
        })
    except Exception as e:
        logger.error(f"清空历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取对话历史"""
    try:
        return jsonify({
            'success': True,
            'data': voice_assistant.conversation_history
        })
    except Exception as e:
        logger.error(f"获取历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    logger.info('客户端已连接')
    emit('status', {'message': '已连接到语音助手服务器'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    logger.info('客户端已断开连接')

@socketio.on('wake_up')
def handle_wake_up():
    """手动唤醒"""
    try:
        asyncio.run(voice_assistant._wake_up())
        emit('status', {
            'type': 'wake',
            'text': f'你好！我是{voice_assistant.wake_word}，有什么可以帮助你的吗？',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('error', {'error': str(e)})

@socketio.on('sleep')
def handle_sleep():
    """手动休眠"""
    try:
        asyncio.run(voice_assistant._sleep())
        emit('status', {
            'type': 'sleep',
            'text': '好的，我进入休眠状态了。说"小鹅"可以唤醒我。',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('error', {'error': str(e)})

if __name__ == '__main__':
    logger.info("启动语音助手服务器...")
    logger.info(f"Qwen API Key: {os.environ.get('QWEN_API_KEY', '未设置')[:10]}...")
    logger.info(f"ElevenLabs API Key: {os.environ.get('ELEVENLABS_API_KEY', '未设置')[:10]}...")
    
    # 启动服务器
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 