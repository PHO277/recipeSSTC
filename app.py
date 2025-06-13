import streamlit as st
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from mongodb_manager import MongoDBManager
from utils.translations import get_translation, LANGUAGES
from llm_interface import LLMInterface
from nutrition_analyzer import NutritionAnalyzer

# 页面配置
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


# 加载自定义CSS
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
    """, unsafe_allow_html=True)


# 初始化
load_css()

# Session State 初始化
if 'db' not in st.session_state:
    mongo_uri = st.secrets.get("MONGODB_URI", os.getenv("MONGODB_URI"))
    if not mongo_uri:
        st.error("⚠️ MongoDB connection string not found. Please configure it in secrets.")
        st.stop()
    st.session_state.db = MongoDBManager(mongo_uri)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'language' not in st.session_state:
    st.session_state.language = 'zh'

# 获取当前语言的翻译函数
t = lambda key: get_translation(key, st.session_state.language)

# 数据库实例
db = st.session_state.db

# 侧边栏
with st.sidebar:
    # 语言选择（始终显示）
    st.markdown("### 🌐 Language / 语言")
    selected_lang = st.selectbox(
        "",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x]['name'],
        index=list(LANGUAGES.keys()).index(st.session_state.language),
        label_visibility="collapsed"
    )

    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        if st.session_state.logged_in:
            db.update_user_language(st.session_state.username, selected_lang)
        st.rerun()

    st.markdown("---")

    # 用户认证区域
    if not st.session_state.logged_in:
        st.markdown(f"### 🔐 {t('user_auth')}")

        auth_mode = st.radio(
            "",
            [t('login'), t('register')],
            label_visibility="collapsed"
        )

        if auth_mode == t('login'):
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input(t('username'), placeholder=t('username_placeholder'))
                password = st.text_input(t('password'), type="password", placeholder=t('password_placeholder'))
                col1, col2 = st.columns(2)
                with col1:
                    login_btn = st.form_submit_button(t('login'), type="primary", use_container_width=True)
                with col2:
                    demo_btn = st.form_submit_button(t('demo_login'), use_container_width=True)

                if login_btn and username and password:
                    success, user_data = db.verify_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_data = user_data
                        st.session_state.language = user_data.get('language', 'zh')
                        st.success(t('login_success'))
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(t('login_failed'))

                if demo_btn:
                    # 演示账号
                    success, user_data = db.verify_user("demo", "demo123")
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = "demo"
                        st.session_state.user_data = user_data
                        st.info(t('demo_login_info'))
                        st.rerun()

        else:  # 注册
            with st.form("register_form", clear_on_submit=True):
                new_username = st.text_input(t('username'), placeholder=t('username_placeholder'))
                new_email = st.text_input(t('email'), placeholder=t('email_placeholder'))
                new_password = st.text_input(t('password'), type="password", placeholder=t('password_placeholder'))
                confirm_password = st.text_input(t('confirm_password'), type="password")

                agree_terms = st.checkbox(t('agree_terms'))

                register_btn = st.form_submit_button(t('register'), type="primary", use_container_width=True)

                if register_btn:
                    if not agree_terms:
                        st.error(t('must_agree_terms'))
                    elif not new_username or len(new_username) < 3:
                        st.error(t('username_too_short'))
                    elif new_password != confirm_password:
                        st.error(t('password_mismatch'))
                    elif len(new_password) < 6:
                        st.error(t('password_too_short'))
                    else:
                        success, message = db.create_user(
                            new_username,
                            new_password,
                            st.session_state.language,
                            new_email
                        )
                        if success:
                            st.success(t('register_success'))
                            # 自动创建演示账号
                            if not db.get_user("demo"):
                                db.create_user("demo", "demo123", "zh", "demo@example.com")
                        else:
                            st.error(message)

    else:  # 已登录
        # 用户信息卡片
        st.markdown(f"### 👤 {t('user_info')}")

        # 用户头像和名称
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(
                f'<div class="user-avatar">{st.session_state.username[0].upper()}</div>',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(f"**{st.session_state.username}**")
            member_since = st.session_state.user_data.get('created', datetime.utcnow())
            if isinstance(member_since, str):
                member_since = datetime.fromisoformat(member_since)
            st.caption(f"{t('member_since')} {member_since.strftime('%Y-%m')}")

        # 用户统计
        stats = db.get_recipe_statistics(st.session_state.username)
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(t('total_recipes'), stats.get('total_recipes', 0))
            with col2:
                avg_rating = stats.get('avg_rating', 0)
                if avg_rating:
                    st.metric(t('avg_rating'), f"{avg_rating:.1f} ⭐")

        st.markdown("---")

        # 快速操作
        st.markdown(f"### ⚡ {t('quick_actions')}")

        if st.button(f"➕ {t('new_recipe')}", use_container_width=True):
            st.session_state.active_tab = "generate"

        if st.button(f"📚 {t('my_recipes')}", use_container_width=True):
            st.session_state.active_tab = "recipes"

        if st.button(f"⚙️ {t('settings')}", use_container_width=True):
            st.session_state.active_tab = "settings"

        st.markdown("---")

        # 退出登录
        if st.button(f"🚪 {t('logout')}", use_container_width=True, type="secondary"):
            for key in ['logged_in', 'username', 'user_data']:
                st.session_state[key] = None
            st.rerun()

# 主界面
if not st.session_state.logged_in:
    # 未登录主页
    st.markdown(f"# 🍳 {t('app_title')}")
    st.markdown(f"### {t('app_subtitle')}")

    # 特性展示
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="recipe-card">
            <h3>🤖 {t('feature_1_title')}</h3>
            <p>{t('feature_1_desc')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="recipe-card">
            <h3>📊 {t('feature_2_title')}</h3>
            <p>{t('feature_2_desc')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="recipe-card">
            <h3>☁️ {t('feature_3_title')}</h3>
            <p>{t('feature_3_desc')}</p>
        </div>
        """, unsafe_allow_html=True)

    # 演示视频或图片
    st.markdown("---")
    st.markdown(f"### 🎥 {t('how_it_works')}")

    # 这里可以添加演示GIF或视频
    st.info(t('login_to_start'))

else:
    # 已登录主界面
    st.markdown(f"# 🍳 {t('app_title')}")

    # 获取或设置活动标签
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "generate"

    # 标签页
    tab_list = [t('generate_recipe'), t('my_recipes'), t('discover'), t('statistics'), t('settings')]
    tabs = st.tabs(tab_list)

    # 生成食谱标签
    with tabs[0]:
        col1, col2 = st.columns([2, 3])

        with col1:
            st.markdown(f"### 📝 {t('recipe_params')}")

            with st.form("recipe_form", clear_on_submit=False):
                # 食材输入
                ingredients = st.text_area(
                    t('ingredients'),
                    placeholder=t('ingredients_placeholder'),
                    height=100,
                    help=t('ingredients_help')
                )

                # 饮食偏好
                diet_options = {
                    t('no_preference'): "",
                    t('vegetarian'): "vegetarian",
                    t('vegan'): "vegan",
                    t('keto'): "keto",
                    t('low_carb'): "low-carb",
                    t('high_protein'): "high-protein",
                    t('mediterranean'): "mediterranean",
                    t('gluten_free'): "gluten-free"
                }

                diet = st.selectbox(
                    t('diet_preference'),
                    options=list(diet_options.keys()),
                    help=t('diet_help')
                )

                # 健康目标
                goal_options = {
                    t('no_goal'): "",
                    t('weight_loss'): "weight-loss",
                    t('muscle_gain'): "muscle-gain",
                    t('energy_boost'): "energy",
                    t('better_digestion'): "digestion",
                    t('immune_boost'): "immunity",
                    t('heart_health'): "heart-health"
                }

                goal = st.selectbox(
                    t('health_goal'),
                    options=list(goal_options.keys()),
                    help=t('goal_help')
                )

                # 高级选项
                with st.expander(t('advanced_options')):
                    col_adv1, col_adv2 = st.columns(2)

                    with col_adv1:
                        cuisine = st.selectbox(
                            t('cuisine_type'),
                            [t('any_cuisine'), t('chinese'), t('western'), t('japanese'),
                             t('korean'), t('thai'), t('italian'), t('mexican')]
                        )

                        cooking_time = st.select_slider(
                            t('cooking_time'),
                            options=[t('15_min'), t('30_min'), t('45_min'), t('60_min'), t('90_min')],
                            value=t('30_min')
                        )

                    with col_adv2:
                        difficulty = st.select_slider(
                            t('difficulty'),
                            options=[t('easy'), t('medium'), t('hard')],
                            value=t('medium')
                        )

                        servings = st.number_input(
                            t('servings'),
                            min_value=1,
                            max_value=10,
                            value=2
                        )

                # 生成按钮
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    generate_btn = st.form_submit_button(
                        t('generate_recipe'),
                        type="primary",
                        use_container_width=True
                    )
                with col_btn2:
                    lucky_btn = st.form_submit_button(
                        t('feeling_lucky'),
                        use_container_width=True
                    )

        with col2:
            # 结果显示区域
            if generate_btn and ingredients:
                with st.spinner(t('generating_recipe')):
                    try:
                        # 初始化API
                        api_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
                        if not api_key:
                            st.error(t('api_key_missing'))
                            st.stop()

                        llm = LLMInterface(api_key=api_key)
                        nutrition = NutritionAnalyzer()

                        # 构建提示
                        actual_diet = diet_options[diet]
                        actual_goal = goal_options[goal]

                        # 生成食谱
                        llm_output = llm.generate_recipe_and_nutrition(
                            ingredients,
                            actual_diet,
                            actual_goal,
                            language=st.session_state.language,
                            cuisine=cuisine if 'cuisine' in locals() else None,
                            cooking_time=cooking_time if 'cooking_time' in locals() else None,
                            difficulty=difficulty if 'difficulty' in locals() else None,
                            servings=servings if 'servings' in locals() else 2
                        )

                        # 解析结果
                        nutrition_info = nutrition.parse_nutrition(llm_output)

                        if "## Nutrition Facts" in llm_output:
                            recipe = llm_output.split("## Nutrition Facts")[0].strip()
                        else:
                            recipe = llm_output.strip()

                        # 显示成功消息
                        st.success(t('recipe_generated'))

                        # 食谱卡片
                        st.markdown(
                            f'<div class="recipe-card">{recipe}</div>',
                            unsafe_allow_html=True
                        )

                        # 营养信息
                        st.markdown(f"### 🥗 {t('nutrition_facts')}")

                        # 解析营养数据
                        nutrition_dict = {}
                        for line in nutrition_info.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                nutrition_dict[key.strip().strip('-')] = value.strip()

                        # 去除键名前空格
                        nutrition_dict = {key.strip(): value for key, value in nutrition_dict.items()}

                        # 营养信息网格
                        nutrition_items = [
                            ("🔥", t('calories'), nutrition_dict.get("Calories", "N/A")),
                            ("🥩", t('protein'), nutrition_dict.get("Protein", "N/A")),
                            ("🥑", t('fat'), nutrition_dict.get("Fat", "N/A")),
                            ("🌾", t('carbs'), nutrition_dict.get("Carbohydrates", "N/A"))
                        ]

                        # 单独渲染每个营养项
                        for icon, label, value in nutrition_items:
                            nutrition_html = f'''
                            <div class="nutrition-item" style="background-color: #e6f3ff; padding: 10px; margin: 5px; border-radius: 5px; display: inline-block;">
                                <span style="font-size: 1.5em;">{icon}</span>
                                <strong>{label}:</strong> {value}
                            </div>
                            '''
                            st.markdown(nutrition_html, unsafe_allow_html=True)

                        # 保存和操作区域
                        st.markdown("---")
                        st.markdown(f"### 💾 {t('save_options')}")

                        col_save1, col_save2 = st.columns(2)

                        with col_save1:
                            rating = st.slider(t('rate_recipe'), 0, 5, 3, help=t('rate_help'))
                            tags_input = st.text_input(
                                t('add_tags'),
                                placeholder=t('tags_placeholder'),
                                help=t('tags_help')
                            )

                        with col_save2:
                            notes = st.text_area(
                                t('notes'),
                                placeholder=t('notes_placeholder'),
                                height=100
                            )

                        # 保存按钮
                        col_action1, col_action2, col_action3 = st.columns(3)

                        with col_action1:
                            if st.button(t('save_recipe'), type="primary", use_container_width=True):
                                # 准备保存数据
                                recipe_data = {
                                    "ingredients": ingredients,
                                    "diet": diet,
                                    "goal": goal,
                                    "recipe": recipe,
                                    "nutrition": nutrition_info,
                                    "rating": rating,
                                    "tags": [tag.strip() for tag in tags_input.split(',') if tag.strip()],
                                    "notes": notes,
                                    "cuisine": cuisine if 'cuisine' in locals() else "",
                                    "cooking_time": cooking_time if 'cooking_time' in locals() else "",
                                    "difficulty": difficulty if 'difficulty' in locals() else "",
                                    "servings": servings if 'servings' in locals() else 2
                                }

                                recipe_id = db.save_recipe(st.session_state.username, recipe_data)
                                st.success(t('recipe_saved'))
                                st.balloons()

                        with col_action2:
                            # 下载按钮
                            recipe_text = f"""
{t('recipe')}
{'=' * 50}

{recipe}

{t('nutrition_facts')}
{'=' * 50}

{nutrition_info}

---
{t('generated_on')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{t('ingredients')}: {ingredients}
{t('diet_preference')}: {diet}
{t('health_goal')}: {goal}
"""
                            st.download_button(
                                label=t('download_recipe'),
                                data=recipe_text.encode('utf-8'),
                                file_name=f"recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )

                        with col_action3:
                            if st.button(t('share_recipe'), use_container_width=True):
                                st.info(t('share_coming_soon'))

                    except Exception as e:
                        st.error(f"{t('generation_error')}: {str(e)}")
                        st.info(t('try_again_later'))

            elif lucky_btn:
                # "手气不错"功能 - 随机生成
                import random

                random_ingredients = random.choice([
                    "鸡胸肉, 西兰花, 胡萝卜",
                    "豆腐, 香菇, 青菜",
                    "三文鱼, 芦笋, 柠檬",
                    "牛肉, 土豆, 洋葱",
                    "虾, 黄瓜, 番茄"
                ])

                st.info(f"{t('lucky_ingredients')}: {random_ingredients}")
                st.info(t('click_generate_with_these'))

            elif generate_btn:
                st.warning(t('please_enter_ingredients'))

    # 我的食谱标签
    with tabs[1]:
        st.markdown(f"### 📚 {t('my_recipes')}")

        # 搜索和筛选
        col_search1, col_search2, col_search3 = st.columns([2, 1, 1])

        with col_search1:
            search_query = st.text_input(
                "",
                placeholder=t('search_recipes'),
                label_visibility="collapsed"
            )

        with col_search2:
            sort_by = st.selectbox(
                "",
                [t('newest_first'), t('oldest_first'), t('highest_rated'), t('most_used')],
                label_visibility="collapsed"
            )

        with col_search3:
            filter_diet = st.selectbox(
                "",
                [t('all_diets')] + list(diet_options.keys()),
                label_visibility="collapsed"
            )

        # 获取食谱
        if search_query:
            recipes = db.search_recipes(st.session_state.username, search_query)
        else:
            recipes = db.get_user_recipes(st.session_state.username)

        # 排序
        if recipes:
            if sort_by == t('oldest_first'):
                recipes.reverse()
            elif sort_by == t('highest_rated'):
                recipes.sort(key=lambda x: x.get('rating', 0), reverse=True)

            # 筛选
            if filter_diet != t('all_diets'):
                recipes = [r for r in recipes if r.get('diet') == diet_options.get(filter_diet, '')]

        # 显示食谱
        if recipes:
            # 食谱统计
            st.info(f"{t('found_recipes')}: {len(recipes)}")

            # 食谱网格
            for idx, recipe in enumerate(recipes):
                created = recipe['created']
                if isinstance(created, str):
                    created = datetime.fromisoformat(created)

                # 食谱卡片
                with st.expander(
                        f"{created.strftime('%Y-%m-%d')} | "
                        f"{recipe['ingredients'][:50]}... | "
                        f"{'⭐' * recipe.get('rating', 0)}"
                ):
                    # 食谱信息
                    col_info1, col_info2 = st.columns([3, 1])

                    with col_info1:
                        # 标签显示
                        if recipe.get('tags'):
                            tags_html = ''.join([f'<span class="tag">{tag}</span>' for tag in recipe['tags']])
                            st.markdown(tags_html, unsafe_allow_html=True)

                        # 基本信息
                        info_items = []
                        if recipe.get('cuisine'):
                            info_items.append(f"🍽️ {recipe['cuisine']}")
                        if recipe.get('cooking_time'):
                            info_items.append(f"⏱️ {recipe['cooking_time']}")
                        if recipe.get('difficulty'):
                            info_items.append(f"📊 {recipe['difficulty']}")
                        if recipe.get('servings'):
                            info_items.append(f"👥 {recipe['servings']} {t('servings')}")

                        if info_items:
                            st.markdown(" | ".join(info_items))

                        # 食材
                        st.markdown(f"**{t('ingredients')}**: {recipe['ingredients']}")

                        # 备注
                        if recipe.get('notes'):
                            st.markdown(f"**{t('notes')}**: {recipe['notes']}")

                    with col_info2:
                        # 操作按钮
                        if st.button(f"🗑️ {t('delete')}", key=f"del_{recipe['_id']}"):
                            if db.delete_recipe(str(recipe['_id'])):
                                st.success(t('recipe_deleted'))
                                st.rerun()

                        if st.button(f"📤 {t('share')}", key=f"share_{recipe['_id']}"):
                            st.info(t('share_coming_soon'))

                    # 食谱内容
                    st.markdown("---")
                    st.markdown(f"### {t('recipe_content')}")
                    st.markdown(recipe.get('recipe_text', recipe.get('recipe', '')))

                    # 营养信息
                    st.markdown(f"### {t('nutrition_info')}")
                    st.text(recipe.get('nutrition_info', 'N/A'))
        else:
            # 空状态
            st.info(t('no_recipes_yet'))
            if st.button(t('create_first_recipe')):
                st.session_state.active_tab = "generate"
                st.rerun()

    # 发现标签
    with tabs[2]:
        st.markdown(f"### 🌟 {t('discover_recipes')}")
        st.info(t('discover_coming_soon'))

        # 这里可以展示：
        # - 热门食谱
        # - 推荐食谱
        # - 社区分享的食谱
        # - 食谱排行榜

    # 统计标签
    with tabs[3]:
        st.markdown(f"### 📊 {t('statistics')}")

        stats = db.get_recipe_statistics(st.session_state.username)

        if stats and stats.get('total_recipes', 0) > 0:
            # 概览卡片
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    t('total_recipes'),
                    stats.get('total_recipes', 0),
                    help=t('total_recipes_help')
                )

            with col2:
                avg_rating = stats.get('avg_rating', 0)
                st.metric(
                    t('avg_rating'),
                    f"{avg_rating:.1f} ⭐" if avg_rating else "N/A",
                    help=t('avg_rating_help')
                )

            with col3:
                # 最常用的饮食类型
                diets = stats.get('most_used_diet', [])
                if diets:
                    most_common_diet = max(set(diets), key=diets.count)
                    # 反向查找显示名称
                    diet_display = next((k for k, v in diet_options.items() if v == most_common_diet), most_common_diet)
                else:
                    diet_display = "N/A"

                st.metric(
                    t('favorite_diet'),
                    diet_display,
                    help=t('favorite_diet_help')
                )

            with col4:
                # 本月食谱数
                current_month_recipes = db.get_user_recipes_by_month(
                    st.session_state.username,
                    datetime.now().year,
                    datetime.now().month
                ) if hasattr(db, 'get_user_recipes_by_month') else []

                st.metric(
                    t('this_month'),
                    len(current_month_recipes) if current_month_recipes else "N/A",
                    help=t('this_month_help')
                )

            st.markdown("---")

            # 详细统计
            col_stat1, col_stat2 = st.columns(2)

            with col_stat1:
                st.markdown(f"### 📈 {t('recipe_trends')}")

                # 最近7天的食谱
                recent_recipes = db.get_user_recipes(st.session_state.username, limit=7)
                if recent_recipes:
                    st.markdown(f"**{t('recent_recipes')}:**")
                    for recipe in recent_recipes[:5]:
                        created = recipe['created']
                        if isinstance(created, str):
                            created = datetime.fromisoformat(created)

                        st.markdown(
                            f"- {created.strftime('%m-%d')} - "
                            f"{recipe['ingredients'][:30]}... "
                            f"{'⭐' * recipe.get('rating', 0)}"
                        )

            with col_stat2:
                st.markdown(f"### 🏷️ {t('popular_tags')}")

                # 收集所有标签
                all_tags = []
                all_recipes = db.get_user_recipes(st.session_state.username, limit=100)
                for recipe in all_recipes:
                    all_tags.extend(recipe.get('tags', []))

                if all_tags:
                    from collections import Counter

                    tag_counts = Counter(all_tags)

                    st.markdown(f"**{t('most_used_tags')}:**")
                    for tag, count in tag_counts.most_common(10):
                        st.markdown(f"- {tag} ({count})")

            # 可视化图表（需要额外的库如plotly）
            st.markdown("---")
            st.info(t('more_analytics_coming_soon'))

        else:
            st.info(t('no_statistics_yet'))
            if st.button(t('start_cooking')):
                st.session_state.active_tab = "generate"
                st.rerun()

    # 设置标签
    with tabs[4]:
        st.markdown(f"### ⚙️ {t('settings')}")

        # 用户信息
        st.markdown(f"#### {t('account_info')}")

        col_set1, col_set2 = st.columns(2)

        with col_set1:
            st.text_input(
                t('username'),
                value=st.session_state.username,
                disabled=True
            )

            user_email = st.session_state.user_data.get('email', '')
            new_email = st.text_input(
                t('email'),
                value=user_email,
                placeholder=t('email_placeholder')
            )

        with col_set2:
            st.text_input(
                t('member_since'),
                value=st.session_state.user_data['created'].strftime('%Y-%m-%d')
                if isinstance(st.session_state.user_data.get('created'), datetime)
                else st.session_state.user_data.get('created', 'N/A'),
                disabled=True
            )

            # 更改密码
            if st.button(t('change_password')):
                st.info(t('change_password_coming_soon'))

        # 偏好设置
        st.markdown(f"#### {t('preferences')}")

        user_prefs = st.session_state.user_data.get('preferences', {})

        col_pref1, col_pref2 = st.columns(2)

        with col_pref1:
            default_diet = st.selectbox(
                t('default_diet'),
                options=list(diet_options.keys()),
                index=0,
                help=t('default_diet_help')
            )

            default_cuisine = st.multiselect(
                t('favorite_cuisines'),
                [t('chinese'), t('western'), t('japanese'), t('korean'),
                 t('thai'), t('italian'), t('mexican')],
                default=user_prefs.get('favorite_cuisines', []),
                help=t('favorite_cuisines_help')
            )

        with col_pref2:
            default_goal = st.selectbox(
                t('default_goal'),
                options=list(goal_options.keys()),
                index=0,
                help=t('default_goal_help')
            )

            newsletter = st.checkbox(
                t('subscribe_newsletter'),
                value=user_prefs.get('newsletter', False),
                help=t('newsletter_help')
            )

        # 保存设置
        if st.button(t('save_settings'), type="primary"):
            # 更新偏好设置
            new_prefs = {
                'default_diet': diet_options[default_diet],
                'default_goal': goal_options[default_goal],
                'favorite_cuisines': default_cuisine,
                'newsletter': newsletter
            }

            db.update_user_preferences(st.session_state.username, new_prefs)

            # 更新邮箱
            if new_email != user_email:
                db.update_user_email(st.session_state.username, new_email)

            st.success(t('settings_saved'))
            st.balloons()

        # 危险区域
        st.markdown("---")
        st.markdown(f"#### ⚠️ {t('danger_zone')}")

        col_danger1, col_danger2, col_danger3 = st.columns(3)

        with col_danger1:
            if st.button(t('export_data'), use_container_width=True):
                # 导出用户数据
                user_data = {
                    'user_info': st.session_state.user_data,
                    'recipes': db.get_user_recipes(st.session_state.username, limit=1000)
                }

                import json

                st.download_button(
                    label=t('download_data'),
                    data=json.dumps(user_data, ensure_ascii=False, indent=2, default=str),
                    file_name=f"recipe_data_{st.session_state.username}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

        with col_danger2:
            if st.button(t('clear_recipes'), type="secondary", use_container_width=True):
                st.warning(t('clear_recipes_warning'))

        with col_danger3:
            if st.button(t('delete_account'), type="secondary", use_container_width=True):
                st.error(t('delete_account_warning'))

# 页脚
st.markdown("---")

# 响应式页脚
footer_cols = st.columns([2, 1, 1, 1])

with footer_cols[0]:
    st.markdown(
        f"© 2024 Smart Recipe Generator | "
        f"{t('made_with')} ❤️ | "
        f"{t('version')} 1.0.0"
    )

with footer_cols[1]:
    st.markdown(f"[{t('privacy_policy')}](#)")

with footer_cols[2]:
    st.markdown(f"[{t('terms_of_service')}](#)")

with footer_cols[3]:
    st.markdown(f"[{t('contact_us')}](#)")

# 添加自定义JavaScript（可选）
st.markdown("""
<script>
// 添加页面加载动画
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.recipe-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
});
</script>
""", unsafe_allow_html=True)