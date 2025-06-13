import streamlit as st

def setup_page():
    st.set_page_config(
        page_title="Smart Recipe Generator | 智能食谱生成器",
        page_icon="🍳",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/yourusername/recipe-generator',
            'Report a bug': "https://github.com/yourusername/recipe-generator/issues",
            'About': "# Smart Recipe Generator\n AI-powered recipe generation with nutrition analysis"
        }
    )

def load_css():
    st.markdown("""
    <style>
        /* 主题色彩 */
        :root {
            --primary-color: #4CAF50;
            --secondary-color: #45a049;
            --background-color: #f5f5f5;
            --card-background: #ffffff;
            --text-color: #333333;
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            .main > div {
                padding: 1rem;
            }
        }

        /* 卡片样式 */
        .recipe-card {
            background: var(--card-background);
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: transform 0.3s ease;
        }

        .recipe-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }

        /* 营养信息网格 */
        .nutrition-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }

        .nutrition-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }

        /* 用户头像 */
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--primary-color);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 10px;
        }

        /* 按钮样式 */
        .stButton > button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            background-color: var(--secondary-color);
            transform: translateY(-1px);
        }

        /* 标签样式 */
        .tag {
            display: inline-block;
            background: #e0e0e0;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            margin: 0.25rem;
            font-size: 0.875rem;
        }

        /* 评分星星 */
        .rating {
            color: #ffd700;
            font-size: 1.2rem;
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.recipe-card');
            cards.forEach((card, index) => {
                card.style.animationDelay = `${index * 0.1}s`;
            });
        });
    </script>
    """, unsafe_allow_html=True)