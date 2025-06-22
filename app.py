import streamlit as st
# 必须在最开始设置页面配置
st.set_page_config(
    page_title="Smart Recipe Generator | 智能食谱生成器",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/smart-recipe-generator',
        'Report a bug': "https://github.com/yourusername/smart-recipe-generator/issues",
        'About': "# Smart Recipe Generator\n智能食谱生成器 - 让AI帮您规划每一餐"
    }
)
# 然后导入其他模块 - 注意这里只导入 load_css
from config.page_config import load_css  # 只导入 load_css，不导入 setup_page
from utils.session import initialize_session
from utils.translations import get_translation, LANGUAGES
from components.sidebar import render_sidebar
from components.home import render_home
from components.generate_recipe import render_generate_recipe
from components.my_recipes import render_my_recipes
from components.discover import render_discover
from components.statistics import render_statistics
from components.settings import render_settings
from components.footer import render_footer
from components.map_search import MapSearch

def main():
    # 加载CSS样式
    load_css()
    # 初始化会话状态
    initialize_session()
    # 渲染侧边栏
    render_sidebar()
    # 根据登录状态显示内容
    if not st.session_state.logged_in:
        render_home()
    else:
        # 为已登录用户创建标签页
        tab_list = [
            get_translation('generate_recipe', st.session_state.language),
            get_translation('my_recipes', st.session_state.language),
            get_translation('map_search', st.session_state.language),  # 修改这里：使用翻译函数
            get_translation('discover', st.session_state.language),
            get_translation('statistics', st.session_state.language),
            get_translation('settings', st.session_state.language)
        ]
        tabs = st.tabs(tab_list)
        
        with tabs[0]:
            render_generate_recipe()
        with tabs[1]:
            render_my_recipes()
        with tabs[2]:  # 地图搜索标签页
            map_search = MapSearch()
            map_search.render_map_page()
        with tabs[3]:
            render_discover()
        with tabs[4]:
            render_statistics()
        with tabs[5]:
            render_settings()
    # 渲染页脚
    render_footer()

if __name__ == "__main__":
    main()
