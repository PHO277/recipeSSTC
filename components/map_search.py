# components/map_search.py
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime
import os


class MapSearch:
    def __init__(self):
        # 地图API密钥
        try:
            self.amap_key = st.secrets.get("AMAP_API_KEY", "")
        except:
            self.amap_key = ""

        # 初始化 DeepSeek（复用项目中的 LLM）
        try:
            from llm_interface import LLMInterface
            deepseek_key = st.secrets.get("DEEPSEEK_API_KEY", "")
            if deepseek_key:
                self.llm = LLMInterface(deepseek_key)
            else:
                self.llm = None
        except:
            self.llm = None

        # 初始化用户位置
        if 'user_location' not in st.session_state:
            st.session_state.user_location = [39.9042, 116.4074]  # 默认北京

        self.user_location = st.session_state.user_location

    def render_map_page(self):
        """渲染地图搜索页面"""
        st.title("🗺️ 餐厅地图搜索")
        st.markdown("### 搜索您想吃的菜品，智能推荐附近餐厅")

        if not self.amap_key:
            with st.info("ℹ️ 提示"):
                st.markdown("当前使用**模拟数据模式**。配置API密钥以使用真实地图数据。")

        # 创建两列布局
        col1, col2 = st.columns([2, 3])

        with col1:
            self._render_search_panel()

        with col2:
            self._render_map()

    def _render_search_panel(self):
        """渲染搜索面板"""
        st.markdown("#### 🔍 搜索菜品")

        # 搜索输入
        dish_name = st.text_input(
            "输入菜品名称",
            placeholder="例如：番茄炒蛋、麻婆豆腐、寿司...",
            key="dish_search_input"
        )

        # 搜索选项
        with st.expander("高级选项", expanded=False):
            search_radius = st.slider(
                "搜索范围（公里）",
                min_value=1,
                max_value=10,
                value=3,
                key="search_radius"
            )

            price_range = st.select_slider(
                "价格范围",
                options=["💰", "💰💰", "💰💰💰", "💰💰💰💰"],
                value="💰💰",
                key="price_range"
            )

            min_rating = st.slider(
                "最低评分",
                min_value=0.0,
                max_value=5.0,
                value=3.5,
                step=0.5,
                key="min_rating"
            )

        # 获取search_radius的值（如果高级选项未展开，使用默认值）
        search_radius = st.session_state.get('search_radius', 3)

        # 搜索按钮
        col1, col2 = st.columns(2)
        with col1:
            search_button = st.button(
                "🔍 搜索餐厅",
                type="primary",
                use_container_width=True,
                key="search_restaurants_btn"
            )
        with col2:
            lucky_button = st.button(
                "🎲 随机推荐",
                use_container_width=True,
                key="lucky_search_btn"
            )

        # 处理搜索
        if search_button and dish_name:
            with st.spinner("正在搜索相关餐厅..."):
                self._search_restaurants(dish_name, search_radius)
                if "search_results" in st.session_state and st.session_state.search_results:
                    st.success(f"找到 {len(st.session_state.search_results)} 家相关餐厅！")
                else:
                    st.warning("没有找到相关餐厅，请尝试其他关键词。")

        if lucky_button:
            # 随机菜品列表
            random_dishes = ["宫保鸡丁", "糖醋排骨", "鱼香肉丝", "麻辣香锅", "寿司", "拉面", "披萨", "汉堡"]
            import random
            random_dish = random.choice(random_dishes)

            # 不要修改 session_state，而是直接显示和搜索
            st.info(f"🎲 随机推荐：{random_dish}")

            with st.spinner(f"正在搜索 {random_dish} 相关餐厅..."):
                self._search_restaurants(random_dish, search_radius)
                if "search_results" in st.session_state and st.session_state.search_results:
                    st.success(f"找到 {len(st.session_state.search_results)} 家相关餐厅！")

        # 显示搜索结果
        if "search_results" in st.session_state and st.session_state.search_results:
            self._display_search_results()

    def _search_restaurants(self, dish_name, radius):
        """搜索餐厅"""
        try:
            # 1. 使用LLM分析菜品类型
            cuisine_info = self._analyze_dish_cuisine(dish_name)

            # 2. 构建搜索关键词
            search_keywords = self._build_search_keywords(dish_name, cuisine_info)

            # 3. 调用地图API搜索
            results = []
            for keyword in search_keywords[:3]:  # 最多使用3个关键词
                restaurants = self._call_map_api(keyword, radius)
                results.extend(restaurants)

            # 4. 去重和排序
            unique_results = self._deduplicate_results(results)
            ranked_results = self._rank_results(unique_results, dish_name, cuisine_info)

            # 5. 保存结果
            st.session_state.search_results = ranked_results
            st.session_state.search_dish = dish_name
            st.session_state.cuisine_info = cuisine_info

        except Exception as e:
            st.error(f"搜索失败：{str(e)}")

    def _analyze_dish_cuisine(self, dish_name):
        """使用 DeepSeek 智能分析菜品"""
        # 如果没有 LLM，使用规则匹配
        if not self.llm:
            return self._analyze_dish_cuisine_fallback(dish_name)

        try:
            # 构建 prompt
            prompt = f"""
            请分析菜品"{dish_name}"，返回JSON格式的结果：
            {{
                "cuisine_type": "菜系类型（如：中餐、日料、韩餐、西餐、火锅等）",
                "restaurant_types": ["推荐的餐厅类型列表，至少3个"],
                "search_keywords": ["搜索关键词列表，用于查找相关餐厅"],
                "dish_characteristics": {{
                    "spicy_level": "辣度（0-5）",
                    "price_range": "价格区间（低/中/高）",
                    "cooking_method": "烹饪方式"
                }},
                "similar_dishes": ["相似菜品列表"],
                "recommended_restaurant_names": ["推荐的餐厅名称模式，如'川菜馆'、'家常菜馆'等"]
            }}

            只返回JSON，不要其他说明。
            """

            # 调用 LLM
            response = self.llm.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个美食专家，擅长分析菜品和推荐餐厅。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            # 解析响应
            result = response.choices[0].message.content.strip()
            # 清理可能的 markdown 标记
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]

            cuisine_info = json.loads(result.strip())

            # 添加置信度
            cuisine_info['confidence'] = 0.95
            cuisine_info['analysis_method'] = 'deepseek_ai'

            return cuisine_info

        except Exception as e:
            st.warning(f"AI分析失败，使用规则匹配: {str(e)}")
            return self._analyze_dish_cuisine_fallback(dish_name)

    def _analyze_dish_cuisine_fallback(self, dish_name):
        """备用的规则匹配方法"""
        cuisine_rules = {
            "中餐": ["炒", "煮", "蒸", "炖", "烧", "宫保", "鱼香", "麻婆", "糖醋", "红烧", "麻辣", "香锅"],
            "日料": ["寿司", "刺身", "拉面", "天妇罗", "照烧", "味增", "日本", "日式"],
            "韩餐": ["泡菜", "烤肉", "石锅", "冷面", "拌饭", "韩国", "韩式"],
            "西餐": ["披萨", "意面", "汉堡", "牛排", "沙拉", "薯条", "西式", "意大利"],
            "火锅": ["火锅", "串串", "麻辣烫", "冒菜"]
        }

        detected_cuisine = "中餐"  # 默认
        restaurant_types = ["中餐厅", "中国餐厅"]

        for cuisine, keywords in cuisine_rules.items():
            if any(keyword in dish_name for keyword in keywords):
                detected_cuisine = cuisine
                if cuisine == "中餐":
                    restaurant_types = ["中餐厅", "中国餐厅", "家常菜", "川菜", "粤菜"]
                elif cuisine == "日料":
                    restaurant_types = ["日本料理", "日料", "寿司店", "居酒屋"]
                elif cuisine == "韩餐":
                    restaurant_types = ["韩国料理", "韩餐", "烤肉店"]
                elif cuisine == "西餐":
                    restaurant_types = ["西餐厅", "牛排馆", "披萨店", "意大利餐厅"]
                elif cuisine == "火锅":
                    restaurant_types = ["火锅店", "火锅", "串串香"]
                break

        return {
            "cuisine_type": detected_cuisine,
            "restaurant_types": restaurant_types,
            "confidence": 0.85,
            "analysis_method": "rule_based"
        }

    def _build_search_keywords(self, dish_name, cuisine_info):
        """构建智能搜索关键词"""
        keywords = []

        # 如果是 AI 分析的结果，使用 AI 推荐的关键词
        if cuisine_info.get('search_keywords'):
            keywords.extend(cuisine_info['search_keywords'][:3])

        # 添加餐厅类型关键词
        keywords.extend(cuisine_info["restaurant_types"][:2])

        # 添加菜系关键词
        keywords.append(cuisine_info["cuisine_type"])

        # 如果有推荐的餐厅名称模式
        if cuisine_info.get('recommended_restaurant_names'):
            keywords.extend(cuisine_info['recommended_restaurant_names'][:2])

        # 去重
        keywords = list(dict.fromkeys(keywords))

        return keywords

    def _call_map_api(self, keyword, radius):
        """调用高德地图API"""
        if not self.amap_key:
            # 如果没有API key，返回模拟数据
            return self._get_mock_restaurants(keyword)

        try:
            # 获取当前选择的城市
            city = st.session_state.get('city_select', '北京')

            # 确保 radius 是数字类型
            if isinstance(radius, (list, tuple)):
                radius = radius[0] if radius else 3
            else:
                radius = float(radius) if radius else 3

            url = "https://restapi.amap.com/v3/place/around"  # 改用 around 接口

            # 确保位置格式正确
            if isinstance(self.user_location, list) and len(self.user_location) >= 2:
                lat = self.user_location[0]
                lng = self.user_location[1]
            else:
                # 默认北京坐标
                lat = 39.9042
                lng = 116.4074

            params = {
                'key': self.amap_key,
                'keywords': keyword,
                'location': f"{lng},{lat}",  # 高德要求：经度在前，纬度在后
                'radius': int(radius * 1000),  # 转换为米
                'types': '050000',  # 餐饮服务
                'sortrule': 'distance',  # 按距离排序
                'offset': 25,
                'page': 1,
                'extensions': 'all'
            }

            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data['status'] == '1':
                pois = data.get('pois', [])
                results = []

                for poi in pois:
                    # 处理每个餐厅数据
                    restaurant = {
                        'id': poi.get('id', ''),
                        'name': poi.get('name', ''),
                        'address': poi.get('address', ''),
                        'location': poi.get('location', ''),
                        'tel': poi.get('tel', ''),
                        'type': poi.get('type', ''),
                        'typecode': poi.get('typecode', ''),
                        'distance': int(float(poi.get('distance', 0))),
                        'biz_ext': poi.get('biz_ext', {})
                    }

                    # 解析评分和价格
                    biz_ext = restaurant['biz_ext']
                    restaurant['rating'] = float(biz_ext.get('rating', 0))
                    restaurant['avg_price'] = float(biz_ext.get('cost', 0))

                    results.append(restaurant)

                return results
            else:
                error_info = data.get('info', '未知错误')
                st.warning(f"API返回错误: {error_info}")

                # IP错误时返回模拟数据
                if 'IP' in error_info or 'USERKEY' in error_info:
                    st.info("使用模拟数据展示功能")
                    return self._get_mock_restaurants(keyword)

                return []

        except Exception as e:
            st.warning(f"地图API调用失败，使用模拟数据: {str(e)}")
            return self._get_mock_restaurants(keyword)

    def _get_mock_restaurants(self, keyword):
        """获取模拟餐厅数据"""
        import random

        # 更真实的餐厅名称库
        restaurant_templates = {
            "火锅": ["海底捞火锅", "小龙坎火锅", "蜀大侠火锅", "大龙燚火锅", "德庄火锅"],
            "川菜": ["眉州东坡", "陈麻婆豆腐", "巴国布衣", "蜀香园", "川味观"],
            "烤鸭": ["全聚德", "便宜坊", "大董烤鸭", "四季民福", "利群烤鸭"],
            "日料": ["将太无二", "鮨然", "隐泉日料", "一风堂拉面", "味千拉面"],
            "西餐": ["王品牛排", "豪客来", "必胜客", "萨莉亚", "新元素"],
            "烧烤": ["很久以前", "丰茂烤串", "聚点串吧", "木屋烧烤", "串越时光"],
            "粤菜": ["陶陶居", "广州酒家", "炳胜品味", "点都德", "稻香"],
            "江浙菜": ["外婆家", "绿茶餐厅", "新白鹿", "弄堂里", "小南国"]
        }

        # 默认餐厅名
        default_names = [
            f"老王{keyword}馆", f"{keyword}大师", f"正宗{keyword}",
            f"{keyword}食府", f"阿姨{keyword}店", f"{keyword}小院"
        ]

        # 选择合适的餐厅名
        mock_restaurants = []
        found_template = False

        for cuisine, names in restaurant_templates.items():
            if cuisine in keyword or any(k in keyword for k in names[0].split()):
                restaurant_names = names
                found_template = True
                break

        if not found_template:
            restaurant_names = default_names

        # 基于用户当前位置生成附近的餐厅
        base_lat, base_lng = self.user_location
        if isinstance(base_lat, list):
            base_lat = base_lat[0]
            base_lng = self.user_location[1]

        for i, name in enumerate(restaurant_names[:8]):
            # 在用户位置周围随机生成餐厅位置（约3公里范围内）
            angle = random.uniform(0, 2 * 3.14159)
            distance_km = random.uniform(0.2, 3)

            # 使用极坐标转换
            lat_offset = distance_km / 111 * random.uniform(-1, 1)
            lng_offset = distance_km / 111 * random.uniform(-1, 1)

            lat = base_lat + lat_offset
            lng = base_lng + lng_offset

            # 计算实际距离（米）
            actual_distance = int(((lat_offset ** 2 + lng_offset ** 2) ** 0.5) * 111000)

            # 生成更真实的地址
            districts = ['朝阳区', '海淀区', '东城区', '西城区', '丰台区']
            streets = ['建国路', '中关村大街', '王府井大街', '西单北大街', '三里屯路']

            mock_restaurants.append({
                'id': f'mock_{i}_{keyword}',
                'name': name,
                'address': f"{random.choice(districts)}{random.choice(streets)}{random.randint(1, 299)}号",
                'location': f"{lng},{lat}",
                'tel': f"010-{random.randint(60000000, 89999999)}",
                'rating': round(random.uniform(3.8, 4.9), 1),
                'avg_price': random.randint(50, 150),
                'distance': actual_distance,
                'type': '中餐厅;' + keyword,
                'biz_ext': {
                    'rating': str(round(random.uniform(3.8, 4.9), 1)),
                    'cost': str(random.randint(50, 150))
                }
            })

        # 按距离排序
        return sorted(mock_restaurants, key=lambda x: x['distance'])

    def _deduplicate_results(self, results):
        """去除重复餐厅"""
        seen = set()
        unique = []

        for restaurant in results:
            if restaurant['id'] not in seen:
                seen.add(restaurant['id'])
                unique.append(restaurant)

        return unique

    def _rank_results(self, results, dish_name, cuisine_info):
        """使用 AI 增强的排序算法"""
        scored_results = []

        for restaurant in results:
            score = 0

            # 基础评分逻辑
            name = restaurant.get('name', '')

            # 1. 餐厅类型匹配
            for restaurant_type in cuisine_info.get('restaurant_types', []):
                if restaurant_type in name:
                    score += 25
                    break

            # 2. 如果有推荐的餐厅名称模式，额外加分
            if cuisine_info.get('recommended_restaurant_names'):
                for pattern in cuisine_info['recommended_restaurant_names']:
                    if pattern in name:
                        score += 15
                        break

            # 3. 评分权重
            rating = float(restaurant.get('rating', 0))
            score += rating * 5

            # 4. 距离权重
            distance = int(restaurant.get('distance', 1000))
            score += max(0, 30 - distance / 100)

            # 5. 价格匹配（如果 AI 分析了价格区间）
            if cuisine_info.get('dish_characteristics', {}).get('price_range'):
                price_range = cuisine_info['dish_characteristics']['price_range']
                avg_price = restaurant.get('avg_price', 50)

                if price_range == '低' and avg_price < 50:
                    score += 10
                elif price_range == '中' and 50 <= avg_price <= 100:
                    score += 10
                elif price_range == '高' and avg_price > 100:
                    score += 10

            # 添加详细信息
            restaurant['match_score'] = score
            restaurant['suggested_for'] = dish_name
            restaurant['cuisine_match'] = cuisine_info['cuisine_type']

            # 如果有 AI 分析的置信度，也加入考虑
            if cuisine_info.get('confidence', 0) > 0.9:
                restaurant['ai_recommended'] = True

            scored_results.append(restaurant)

        # 按分数排序
        return sorted(scored_results, key=lambda x: x['match_score'], reverse=True)

    def _display_search_results(self):
        """显示增强的搜索结果"""
        st.markdown("#### 📍 推荐餐厅")

        results = st.session_state.search_results
        dish_name = st.session_state.search_dish
        cuisine_info = st.session_state.cuisine_info

        # 显示搜索解释（包含 AI 分析信息）
        with st.expander("🤖 AI 分析结果", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**搜索菜品**: {dish_name}")
                st.markdown(f"**识别菜系**: {cuisine_info['cuisine_type']}")
                st.markdown(
                    f"**分析方法**: {'AI智能分析' if cuisine_info.get('analysis_method') == 'deepseek_ai' else '规则匹配'}")
                st.markdown(f"**置信度**: {cuisine_info.get('confidence', 0) * 100:.1f}%")

            with col2:
                if cuisine_info.get('dish_characteristics'):
                    chars = cuisine_info['dish_characteristics']
                    st.markdown("**菜品特征**:")
                    if chars.get('spicy_level'):
                        st.markdown(f"- 辣度: {'🌶️' * int(chars['spicy_level'])}")
                    if chars.get('price_range'):
                        st.markdown(f"- 价格: {chars['price_range']}")
                    if chars.get('cooking_method'):
                        st.markdown(f"- 烹饪: {chars['cooking_method']}")

            if cuisine_info.get('similar_dishes'):
                st.markdown(f"**相似菜品**: {', '.join(cuisine_info['similar_dishes'][:5])}")

        st.info(f"📊 找到 {len(results)} 家相关餐厅")

        # 显示餐厅列表
        for idx, restaurant in enumerate(results[:10]):
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    # 如果是 AI 推荐的，加个标记
                    ai_badge = "🤖 " if restaurant.get('ai_recommended') else ""
                    st.markdown(f"**{ai_badge}{idx + 1}. {restaurant['name']}**")
                    st.caption(restaurant.get('address', '地址未知'))

                with col2:
                    rating = restaurant.get('rating', 0)
                    st.markdown(f"⭐ {rating}")
                    if 'avg_price' in restaurant:
                        st.markdown(f"💰 人均 ¥{restaurant['avg_price']}")

                with col3:
                    if 'distance' in restaurant:
                        distance = restaurant['distance']
                        if distance < 1000:
                            st.markdown(f"📍 {distance}m")
                        else:
                            st.markdown(f"📍 {distance / 1000:.1f}km")

                    # 显示匹配分数（调试用，可以注释掉）
                    # st.caption(f"匹配度: {restaurant['match_score']:.1f}")

                # 操作按钮
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"查看详情", key=f"detail_{idx}"):
                        self._show_restaurant_detail(restaurant)
                with col2:
                    if st.button(f"导航", key=f"nav_{idx}"):
                        self._navigate_to_restaurant(restaurant)
                with col3:
                    if st.button(f"收藏", key=f"fav_{idx}"):
                        self._add_to_favorites(restaurant)

                st.divider()

    def _render_map(self):
        """渲染地图"""
        st.markdown("#### 🗺️ 餐厅位置")

        # 添加城市选择和定位控制
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            city = st.selectbox(
                "选择城市",
                ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"],
                key="city_select"
            )

            # 根据城市更新位置
            city_locations = {
                "北京": [39.9042, 116.4074],
                "上海": [31.2304, 121.4737],
                "广州": [23.1291, 113.2644],
                "深圳": [22.5431, 114.0579],
                "杭州": [30.2741, 120.1551],
                "成都": [30.5728, 104.0668],
                "武汉": [30.5928, 114.3055],
                "西安": [34.2658, 108.9541]
            }

            if city in city_locations:
                self.user_location = city_locations[city]
                st.session_state.user_location = self.user_location

        with col2:
            # 添加手动输入位置
            if st.button("📍 使用当前位置", key="use_current_location"):
                st.info("浏览器定位功能需要HTTPS连接。请选择城市或输入地址。")

        with col3:
            # 地址输入
            address = st.text_input("或输入具体地址", placeholder="如：朝阳区建国路88号", key="address_input")
            if address and st.button("定位", key="locate_btn"):
                # 使用地理编码API
                if self.amap_key:
                    coords = self._geocode_address(address)
                    if coords:
                        self.user_location = coords
                        st.session_state.user_location = coords
                        st.success("定位成功！")
                        st.rerun()
                else:
                    st.info(f"定位到：{address}")

        # 创建地图
        m = folium.Map(
            location=self.user_location,
            zoom_start=13,
            tiles='OpenStreetMap',
            control_scale=True
        )

        # 添加用户位置标记
        folium.Marker(
            location=self.user_location,
            popup="您的位置",
            tooltip="您在这里",
            icon=folium.Icon(color='green', icon='user', prefix='fa')
        ).add_to(m)

        # 如果有搜索结果，添加标记
        if "search_results" in st.session_state and st.session_state.search_results:
            # 显示搜索信息
            st.info(f"🔍 在地图上显示 {len(st.session_state.search_results)} 个搜索结果")

            bounds = []

            for idx, restaurant in enumerate(st.session_state.search_results[:10]):
                # 解析位置
                if 'location' in restaurant:
                    location_str = restaurant['location']
                    try:
                        lng, lat = map(float, location_str.split(','))

                        # 创建HTML弹窗内容
                        html = f"""
                        <div style="font-family: Arial; width: 200px;">
                            <h4 style="color: #2196F3; margin: 5px 0;">{restaurant['name']}</h4>
                            <p style="margin: 5px 0;"><b>地址:</b> {restaurant.get('address', '未知')}</p>
                            <p style="margin: 5px 0;"><b>评分:</b> ⭐ {restaurant.get('rating', '暂无')}</p>
                            <p style="margin: 5px 0;"><b>人均:</b> ¥{restaurant.get('avg_price', '未知')}</p>
                            <p style="margin: 5px 0;"><b>推荐:</b> {restaurant.get('suggested_for', '')}</p>
                        </div>
                        """

                        # 创建弹窗
                        popup = folium.Popup(html=html, max_width=250)

                        # 前三个用红色标记，其他用蓝色
                        color = 'red' if idx < 3 else 'blue'

                        # 创建标记
                        folium.Marker(
                            location=[lat, lng],
                            popup=popup,
                            tooltip=f"{idx + 1}. {restaurant['name']}",
                            icon=folium.Icon(
                                color=color,
                                icon='cutlery',
                                prefix='fa'
                            )
                        ).add_to(m)

                        bounds.append([lat, lng])

                    except Exception as e:
                        st.warning(f"无法解析餐厅位置: {restaurant['name']} - {str(e)}")

            # 调整地图视野以包含所有标记
            if bounds:
                bounds.append(self.user_location)  # 包含用户位置
                m.fit_bounds(bounds)

        # 显示地图
        st_folium(m, width=700, height=500, key="restaurant_map")

    def _geocode_address(self, address):
        """将地址转换为坐标"""
        if not self.amap_key:
            st.error("需要API密钥才能使用地址定位功能")
            return None

        try:
            url = "https://restapi.amap.com/v3/geocode/geo"
            params = {
                'key': self.amap_key,
                'address': address,
                'city': st.session_state.get('city_select', '北京')
            }

            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == '1' and data['geocodes']:
                location = data['geocodes'][0]['location']
                lng, lat = map(float, location.split(','))
                return [lat, lng]
            else:
                st.error("无法定位该地址")
                return None

        except Exception as e:
            st.error(f"地址解析失败: {str(e)}")
            return None

    def _show_restaurant_detail(self, restaurant):
        """显示餐厅详情"""
        st.session_state.selected_restaurant = restaurant

        # 创建详情弹窗
        with st.expander(f"🍽️ {restaurant['name']} 详情", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**基本信息**")
                st.write(f"📍 地址: {restaurant.get('address', '未知')}")
                st.write(f"📞 电话: {restaurant.get('tel', '未知')}")
                st.write(f"⭐ 评分: {restaurant.get('rating', '暂无')}")
                st.write(f"💰 人均: ¥{restaurant.get('avg_price', '未知')}")

            with col2:
                st.markdown("**推荐信息**")
                st.write(f"🍽️ 推荐菜品: {restaurant.get('suggested_for', '')}")
                st.write(f"🏷️ 菜系匹配: {restaurant.get('cuisine_match', '')}")
                if restaurant.get('ai_recommended'):
                    st.write("🤖 AI推荐")
                if 'distance' in restaurant:
                    distance = restaurant['distance']
                    if distance < 1000:
                        st.write(f"📏 距离: {distance}m")
                    else:
                        st.write(f"📏 距离: {distance / 1000:.1f}km")

    def _navigate_to_restaurant(self, restaurant):
        """导航到餐厅"""
        if 'location' in restaurant:
            location = restaurant['location']
            restaurant_name = restaurant['name']

            # 提供多种导航选项
            st.markdown("**选择导航方式:**")
            col1, col2, col3 = st.columns(3)

            with col1:
                # 高德地图
                amap_url = f"https://uri.amap.com/navigation?to={location},{restaurant_name}&mode=car&policy=1&src=myapp&coordinate=gaode&callnative=0"
                st.markdown(f"[📍 高德导航]({amap_url})")

            with col2:
                # 百度地图
                lng, lat = location.split(',')
                baidu_url = f"http://api.map.baidu.com/direction?destination=latlng:{lat},{lng}|name:{restaurant_name}&mode=driving&src=webapp.baidu.openAPIdemo"
                st.markdown(f"[📍 百度导航]({baidu_url})")

            with col3:
                # 腾讯地图
                tx_url = f"https://apis.map.qq.com/uri/v1/routeplan?type=drive&to={restaurant_name}&tocoord={lat},{lng}"
                st.markdown(f"[📍 腾讯导航]({tx_url})")

    def _add_to_favorites(self, restaurant):
        """添加到收藏"""
        if 'favorites' not in st.session_state:
            st.session_state.favorites = []

        # 检查是否已收藏
        if not any(fav['id'] == restaurant['id'] for fav in st.session_state.favorites):
            st.session_state.favorites.append(restaurant)
            st.success(f"已收藏 {restaurant['name']}")

            # 如果用户已登录，保存到数据库
            if st.session_state.get('logged_in') and st.session_state.get('db_manager'):
                try:
                    # 创建收藏记录
                    favorite_data = {
                        'restaurant': restaurant,
                        'saved_at': datetime.now(),
                        'dish_searched': st.session_state.get('search_dish', ''),
                        'type': 'restaurant_favorite'
                    }
                    st.session_state.db_manager.save_recipe(
                        st.session_state.username,
                        favorite_data
                    )
                except Exception as e:
                    st.warning("收藏保存到云端失败，仅保存在本地")
        else:
            st.warning(f"{restaurant['name']} 已在收藏中")
