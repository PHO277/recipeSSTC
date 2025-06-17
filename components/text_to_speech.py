"""
改进的语音播报功能模块 - 支持多种TTS方案
包含网络重试机制、本地TTS备选方案和错误处理优化
"""

import streamlit as st
from gtts import gTTS
import io
import time
import requests
from typing import Optional, Union
import base64

class TextToSpeechManager:
    """改进的语音播报管理器"""

    def __init__(self):
        # 语言映射，用于 gTTS
        self.language_mapping = {
            'zh': 'zh-CN',
            'en': 'en',
            'ja': 'ja',
            'ko': 'ko'
        }
        
        # 网络重试配置
        self.max_retries = 3
        self.retry_delay = 2  # 秒
        
    def check_internet_connection(self, timeout=5):
        """检查网络连接状态"""
        try:
            response = requests.get('https://www.google.com', timeout=timeout)
            return response.status_code == 200
        except:
            return False

    def generate_audio_bytes_with_retry(self, text: str, language: str = 'zh') -> Optional[bytes]:
        """
        带重试机制的音频生成函数
        """
        tts_lang = self.language_mapping.get(language, 'zh-CN')
        
        for attempt in range(self.max_retries):
            try:
                # 显示重试状态
                if attempt > 0:
                    st.info(f"正在重试... ({attempt + 1}/{self.max_retries})")
                
                # 创建内存文件对象
                fp = io.BytesIO()
                
                # 创建 gTTS 对象
                tts = gTTS(text=text, lang=tts_lang, slow=False)
                
                # 将音频数据写入内存文件
                tts.write_to_fp(fp)
                fp.seek(0)
                
                # 读取所有字节
                audio_bytes = fp.read()
                
                if audio_bytes:
                    return audio_bytes
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    st.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")
                    time.sleep(self.retry_delay)
                else:
                    st.error(f"所有重试都失败了。最后一次错误: {str(e)}")
        
        return None

    def generate_fallback_audio(self, text: str) -> Optional[str]:
        """
        生成备选的语音提示方案
        当gTTS失败时，提供文本朗读提示
        """
        try:
            # 方案1: 使用Web Speech API (通过JavaScript)
            speech_js = f"""
            <script>
            function speakText() {{
                if ('speechSynthesis' in window) {{
                    const utterance = new SpeechSynthesisUtterance(`{text}`);
                    utterance.lang = 'zh-CN';
                    utterance.rate = 0.8;
                    speechSynthesis.speak(utterance);
                }} else {{
                    alert('您的浏览器不支持语音朗读功能');
                }}
            }}
            </script>
            <button onclick="speakText()" style="
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            ">🔊 点击朗读</button>
            """
            return speech_js
        except Exception as e:
            st.error(f"备选方案也失败了: {str(e)}")
            return None

    def create_text_display_with_audio_hint(self, text: str) -> str:
        """
        创建带音频提示的文本显示
        """
        return f"""
        <div style="
            background-color: #f0f8ff;
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h4 style="color: #2e7d32; margin-top: 0;">
                🎯 食谱内容 (可复制到其他TTS工具朗读)
            </h4>
            <div style="
                background-color: white;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #4CAF50;
                font-size: 16px;
                line-height: 1.6;
            ">
                {text}
            </div>
            <p style="color: #666; font-size: 14px; margin-bottom: 0;">
                💡 提示: 您可以复制上述文本到手机或电脑的语音助手进行朗读
            </p>
        </div>
        """

def render_tts_component_improved(text: str, language: str = 'zh', key: str = None):
    """
    改进的TTS组件渲染函数，使用session state避免页面重置
    """
    if not text.strip():
        st.warning("没有可供播报的文本内容。")
        return

    tts_manager = TextToSpeechManager()
    
    # 初始化session state
    tts_state_key = f"tts_state_{key}"
    if tts_state_key not in st.session_state:
        st.session_state[tts_state_key] = {
            'mode': None,
            'audio_data': None,
            'show_content': False
        }
    
    # 添加语音播报选项
    st.markdown("### 🔊 语音播报选项")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(
            "🌐 在线语音播报", 
            help="使用Google TTS在线生成语音",
            key=f"online_tts_{key}"
        ):
            st.session_state[tts_state_key]['mode'] = 'online'
            st.session_state[tts_state_key]['show_content'] = True
    
    with col2:
        if st.button(
            "🔊 浏览器朗读", 
            help="使用浏览器内置的语音功能",
            key=f"browser_tts_{key}"
        ):
            st.session_state[tts_state_key]['mode'] = 'browser'
            st.session_state[tts_state_key]['show_content'] = True
    
    with col3:
        if st.button(
            "📝 显示文本", 
            help="显示完整文本内容，便于复制到其他工具朗读",
            key=f"show_text_{key}"
        ):
            st.session_state[tts_state_key]['mode'] = 'text'
            st.session_state[tts_state_key]['show_content'] = True

    # 根据选择的模式显示相应内容
    if st.session_state[tts_state_key]['show_content']:
        current_mode = st.session_state[tts_state_key]['mode']
        
        if current_mode == 'online':
            st.markdown("---")
            st.markdown("#### 🌐 在线语音播报")
            
            # 首先检查网络连接
            if not tts_manager.check_internet_connection():
                st.error("⚠️ 网络连接不可用，请检查您的网络设置或尝试其他选项。")
                st.info("💡 建议尝试「浏览器朗读」或「显示文本」选项")
            else:
                # 检查是否已经有缓存的音频数据
                if st.session_state[tts_state_key]['audio_data'] is None:
                    with st.spinner("正在生成语音，请稍候..."):
                        # 尝试生成音频
                        audio_bytes = tts_manager.generate_audio_bytes_with_retry(text, language)
                        st.session_state[tts_state_key]['audio_data'] = audio_bytes
                
                audio_bytes = st.session_state[tts_state_key]['audio_data']
                if audio_bytes:
                    st.success("✅ 语音生成成功！")
                    st.audio(audio_bytes, format='audio/mp3')
                else:
                    st.error("❌ 在线语音生成失败")
                    st.info("💡 请尝试「浏览器朗读」或「显示文本」选项")
        
        elif current_mode == 'browser':
            st.markdown("---")
            st.markdown("#### 🔊 浏览器语音朗读")
            fallback_html = tts_manager.generate_fallback_audio(text)
            if fallback_html:
                st.markdown(fallback_html, unsafe_allow_html=True)
                st.info("💡 点击上方按钮即可听到朗读。如果没有声音，请检查浏览器设置。")
        
        elif current_mode == 'text':
            st.markdown("---")
            formatted_text = tts_manager.create_text_display_with_audio_hint(text)
            st.markdown(formatted_text, unsafe_allow_html=True)
        
        # 添加清除按钮
        if st.button("🗑️ 清除", key=f"clear_tts_{key}", help="清除当前显示内容"):
            st.session_state[tts_state_key] = {
                'mode': None,
                'audio_data': None,
                'show_content': False
            }
            st.rerun()

def render_tts_component_simple(text: str, language: str = 'zh', key: str = None):
    """
    简化版TTS组件 - 使用session state保持状态
    """
    if not text.strip():
        st.warning("没有可供播报的文本内容。")
        return

    st.markdown("### 🔊 食谱朗读")
    
    # 初始化session state
    simple_state_key = f"simple_tts_{key}"
    if simple_state_key not in st.session_state:
        st.session_state[simple_state_key] = {'show_content': True, 'show_browser': False}
    
    # 直接显示格式化的文本内容
    if st.session_state[simple_state_key]['show_content']:
        tts_manager = TextToSpeechManager()
        formatted_text = tts_manager.create_text_display_with_audio_hint(text)
        st.markdown(formatted_text, unsafe_allow_html=True)
    
    # 提供浏览器朗读选项
    with st.expander("🎙️ 尝试浏览器朗读功能", expanded=st.session_state[simple_state_key]['show_browser']):
        if st.button("开始朗读", key=f"simple_browser_tts_{key}"):
            st.session_state[simple_state_key]['show_browser'] = True
            
        if st.session_state[simple_state_key]['show_browser']:
            tts_manager = TextToSpeechManager()  
            fallback_html = tts_manager.generate_fallback_audio(text)
            if fallback_html:
                st.markdown(fallback_html, unsafe_allow_html=True)
                st.info("💡 点击上方按钮即可听到朗读。")

# 使用示例
if __name__ == "__main__":
    st.title("改进的语音播报功能演示")
    
    sample_text = """
    菜名: 蒜蓉西兰花炒虾仁
    描述: 营养丰富的健康菜品，富含蛋白质和维生素
    所需食材: 西兰花 300克, 虾仁 200克, 大蒜 3瓣, 生抽 1勺, 盐 适量
    制作步骤: 第1步, 西兰花切小朵焯水备用 第2步, 虾仁用料酒腌制5分钟 第3步, 热锅下蒜爆香 第4步, 下虾仁炒至变色 第5步, 加入西兰花翻炒 第6步, 调味出锅
    """
    
    st.markdown("#### 原始文本:")
    st.write(sample_text)
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["完整版TTS", "简化版TTS"])
    
    with tab1:
        st.markdown("##### 完整版 - 多种语音选项")
        render_tts_component_improved(sample_text, language='zh', key='demo1')
    
    with tab2:
        st.markdown("##### 简化版 - 重点显示文本")
        render_tts_component_simple(sample_text, language='zh', key='demo2')