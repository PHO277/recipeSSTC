# components/config_checker.py
import streamlit as st
from utils.config_manager import ConfigManager


class ConfigChecker:
    """配置检查和设置组件"""

    @staticmethod
    def check_and_setup():
        """检查配置并提供设置界面"""
        missing_configs = []

        # 检查所有必需的配置
        for key in ConfigManager.get_all_required_keys():
            if not ConfigManager.is_configured(key):
                missing_configs.append(key)

        if missing_configs:
            with st.expander("⚠️ 缺少配置", expanded=True):
                st.warning("检测到缺少一些必要的配置。您可以：")
                st.markdown("""
                1. **生产环境**：在 Streamlit Cloud 的 Secrets 中配置
                2. **本地开发**：使用环境变量或下方输入框临时配置
                """)

                # 提供输入界面
                st.markdown("### 临时配置（仅本次会话有效）")

                for key in missing_configs:
                    value = st.text_input(
                        f"{key}:",
                        type="password",
                        key=f"input_{key}",
                        help=ConfigChecker._get_help_text(key)
                    )

                    if value:
                        ConfigManager.set_runtime_config(key, value)
                        st.success(f"✅ {key} 已配置")

                # 提供获取API密钥的链接
                st.markdown("### 获取API密钥")
                st.markdown("""
                - [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
                - [DeepSeek API](https://platform.deepseek.com/)
                - [SiliconFlow API](https://siliconflow.cn/)
                - [高德地图API](https://lbs.amap.com/)
                """)

                return False

        return True

    @staticmethod
    def _get_help_text(key: str) -> str:
        """获取配置项的帮助文本"""
        help_texts = {
            'MONGODB_URI': '格式: mongodb+srv://username:password@cluster.mongodb.net/database',
            'DEEPSEEK_API_KEY': 'DeepSeek平台的API密钥',
            'SILICONFLOW_API_KEY': 'SiliconFlow图像识别API密钥',
            'AMAP_API_KEY': '高德地图Web服务API密钥'
        }
        return help_texts.get(key, '')