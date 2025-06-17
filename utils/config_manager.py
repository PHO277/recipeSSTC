# utils/config_manager.py
import os
import streamlit as st
from typing import Optional


class ConfigManager:
    """安全的配置管理器"""

    @staticmethod
    def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        按优先级获取配置：
        1. Streamlit secrets (生产环境/Streamlit Cloud)
        2. 环境变量 (本地开发)
        3. Session state (用户运行时输入)
        4. 默认值
        """

        # 1. 尝试从 Streamlit secrets 获取（部署环境）
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except:
            pass

        # 2. 从环境变量获取（本地开发）
        env_value = os.environ.get(key)
        if env_value:
            return env_value

        # 3. 从 session state 获取（用户输入）
        session_key = f"config_{key.lower()}"
        if session_key in st.session_state:
            return st.session_state[session_key]

        # 4. 返回默认值
        return default

    @staticmethod
    def set_runtime_config(key: str, value: str):
        """运行时设置配置（保存到session state）"""
        session_key = f"config_{key.lower()}"
        st.session_state[session_key] = value

    @staticmethod
    def is_configured(key: str) -> bool:
        """检查配置是否存在"""
        return ConfigManager.get_config(key) is not None

    @staticmethod
    def get_all_required_keys():
        """获取所有必需的配置键"""
        return [
            'MONGODB_URI',
            'DEEPSEEK_API_KEY',
            'SILICONFLOW_API_KEY',
            'AMAP_API_KEY'
        ]