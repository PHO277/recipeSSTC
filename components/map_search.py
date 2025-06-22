# components/map_search.py
import streamlit as st
import folium
from utils.translations import get_translation
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime
import random


class MapSearch:
    def __init__(self):
        # 地图API密钥
        try:
            self.amap_key = st.secrets.get("AMAP_API_KEY", "")
        except:
            self.amap_key = ""

        # 初始化 DeepSeek
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

        # 初始化搜索状态
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'search_dish' not in st.session_state:
            st.session_state.search_dish = ""
        if 'cuisine_info' not in st.session_state:
            st.session_state.cuisine_info = {}

    def render_map_page(self):
        """渲染地图搜索页面"""
        lang = st.session_state.get('language', 'zh')
        
        st.title(f"🗺️ {get_translation('map_search_title', lang)}")
        st.markdown(f"### {get_translation('map_search_subtitle', lang)}")

        if not self.amap_key:
            st.info(f"ℹ️ {get_translation('mock_data_notice', lang)}")

        # 创建两列布局
        col1, col2 = st.columns([1, 2])

        with col1:
            self._render_search_panel(lang)

        with col2:
            self._render_map(lang)

        # 在主区域显示搜索结果
        self._render_search_results(lang)

    def _render_search_panel(self, lang):
        """渲染搜索面板"""
        st.markdown(f"#### 🔍 {get_translation('search_dishes', lang)}")

        # 搜索输入
        dish_name = st.text_input(
            get_translation('dish_name_input', lang),
            placeholder=get_translation('dish_placeholder', lang),
            key="dish_search_input"
        )

        # 搜索选项
        with st.expander(get_translation('advanced_options', lang), expanded=False):
            search_radius = st.slider(
                get_translation('search_radius', lang),
                min_value=1,
                max_value=10,
                value=3,
                key="search_radius"
            )

            price_range = st.select_slider(
                get_translation('price_range', lang),
                options=["💰", "💰💰", "💰💰💰", "💰💰💰💰"],
                value="💰💰",
                key="price_range"
            )

            min_rating = st.slider(
                get_translation('min_rating', lang),
                min_value=0.0,
                max_value=5.0,
                value=3.5,
                step=0.5,
                key="min_rating"
            )

        # 搜索按钮
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button(f"🔍 {get_translation('search_restaurants', lang)}", type="primary", use_container_width=True):
                if dish_name:
                    with st.spinner(get_translation('searching_restaurants', lang)):
                        self._execute_search(dish_name, st.session_state.get('search_radius', 3), lang)
                else:
                    st.warning(get_translation('enter_dish_name', lang))

        with btn_col2:
            if st.button(f"🎲 {get_translation('random_recommend', lang)}", use_container_width=True):
                random_dishes = get_translation('random_dishes_list', lang).split(',')
                random_dish = random.choice(random_dishes)
                st.info(f"🎲 {get_translation('random_recommendation', lang)}: {random_dish}")
                with st.spinner(f"{get_translation('searching_for', lang)} {random_dish} {get_translation('related_restaurants', lang)}"):
                    self._execute_search(random_dish, st.session_state.get('search_radius', 3), lang)

    def _execute_search(self, dish_name, radius, lang):
        """执行搜索"""
        try:
            # 1. AI分析菜品
            cuisine_info = self._analyze_dish_cuisine(dish_name, lang)
            
            # 2. 构建搜索关键词
            keywords = self._build_search_keywords(dish_name, cuisine_info)
            
            # 3. 搜索餐厅
            all_results = []
            for keyword in keywords[:3]:
                results = self._call_map_api(keyword, radius)
                all_results.extend(results)
            
            # 4. 去重并排序
            unique_results = self._deduplicate_results(all_results)
            ranked_results = self._rank_results(unique_results, dish_name, cuisine_info)
            
            # 5. 保存结果
            st.session_state.search_results = ranked_results
            st.session_state.search_dish = dish_name
            st.session_state.cuisine_info = cuisine_info
            
            if ranked_results:
                st.success(f"{get_translation('found_count', lang)} {len(ranked_results)} {get_translation('related_restaurants', lang)}！")
            else:
                st.warning(get_translation('no_restaurants_found', lang))
                
        except Exception as e:
            st.error(f"{get_translation('search_failed', lang)}: {str(e)}")
            st.session_state.search_results = []

    def _analyze_dish_cuisine(self, dish_name, lang):
        """分析菜品类型"""
        if self.llm:
            try:
                return self._ai_analyze_dish(dish_name, lang)
            except:
                return self._fallback_analyze_dish(dish_name, lang)
        else:
            return self._fallback_analyze_dish(dish_name, lang)

    def _ai_analyze_dish(self, dish_name, lang):
        """AI分析菜品"""
        if lang == 'zh':
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
                "recommended_restaurant_names": ["推荐的餐厅名称模式"]
            }}
            只返回JSON，不要其他说明。
            """
        else:
            prompt = f"""
            Please analyze the dish "{dish_name}" and return the result in JSON format:
            {{
                "cuisine_type": "cuisine type (e.g., Chinese, Japanese, Korean, Western, Hotpot, etc.)",
                "restaurant_types": ["list of recommended restaurant types, at least 3"],
                "search_keywords": ["list of search keywords for finding related restaurants"],
                "dish_characteristics": {{
                    "spicy_level": "spice level (0-5)",
                    "price_range": "price range (Low/Medium/High)",
                    "cooking_method": "cooking method"
                }},
                "similar_dishes": ["list of similar dishes"],
                "recommended_restaurant_names": ["recommended restaurant name patterns"]
            }}
            Return only JSON, no other explanations.
            """

        response = self.llm.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": get_translation('ai_food_expert_prompt', lang)},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        result = response.choices[0].message.content.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]

        cuisine_info = json.loads(result.strip())
        cuisine_info['confidence'] = 0.95
        cuisine_info['analysis_method'] = 'deepseek_ai'
        
        return cuisine_info

    def _fallback_analyze_dish(self, dish_name, lang):
        """备用分析方法"""
        if lang == 'zh':
            cuisine_rules = {
                "中餐": ["炒", "煮", "蒸", "炖", "烧", "宫保", "鱼香", "麻婆", "糖醋", "红烧", "麻辣"],
                "日料": ["寿司", "刺身", "拉面", "天妇罗", "照烧", "味增", "日本", "日式"],
                "韩餐": ["泡菜", "烤肉", "石锅", "冷面", "拌饭", "韩国", "韩式"],
                "西餐": ["披萨", "意面", "汉堡", "牛排", "沙拉", "薯条", "西式"],
                "火锅": ["火锅", "串串", "麻辣烫", "冒菜"]
            }
        else:
            cuisine_rules = {
                "Chinese": ["stir-fry", "fried", "steamed", "braised", "kung pao", "mapo", "sweet and sour"],
                "Japanese": ["sushi", "sashimi", "ramen", "tempura", "teriyaki", "miso", "japanese"],
                "Korean": ["kimchi", "bbq", "stone bowl", "bibimbap", "korean"],
                "Western": ["pizza", "pasta", "burger", "steak", "salad", "fries", "western"],
                "Hotpot": ["hotpot", "hot pot", "spicy pot"]
            }

        detected_cuisine = get_translation('chinese_cuisine', lang)
        restaurant_types = [get_translation('chinese_restaurant', lang), get_translation('china_restaurant', lang)]

        for cuisine, keywords in cuisine_rules.items():
            if any(keyword.lower() in dish_name.lower() for keyword in keywords):
                detected_cuisine = cuisine
                if cuisine in ["中餐", "Chinese"]:
                    restaurant_types = [get_translation('chinese_restaurant', lang), get_translation('china_restaurant', lang), get_translation('home_cooking', lang), get_translation('sichuan_cuisine', lang)]
                elif cuisine in ["日料", "Japanese"]:
                    restaurant_types = [get_translation('japanese_restaurant', lang), get_translation('japanese_cuisine', lang), get_translation('sushi_restaurant', lang)]
                elif cuisine in ["韩餐", "Korean"]:
                    restaurant_types = [get_translation('korean_restaurant', lang), get_translation('korean_cuisine', lang), get_translation('bbq_restaurant', lang)]
                elif cuisine in ["西餐", "Western"]:
                    restaurant_types = [get_translation('western_restaurant', lang), get_translation('steakhouse', lang), get_translation('pizza_restaurant', lang)]
                elif cuisine in ["火锅", "Hotpot"]:
                    restaurant_types = [get_translation('hotpot_restaurant', lang), get_translation('hotpot', lang), get_translation('spicy_hotpot', lang)]
                break

        return {
            "cuisine_type": detected_cuisine,
            "restaurant_types": restaurant_types,
            "search_keywords": restaurant_types,
            "confidence": 0.85,
            "analysis_method": "rule_based"
        }

    def _build_search_keywords(self, dish_name, cuisine_info):
        """构建搜索关键词"""
        keywords = []
        
        if cuisine_info.get('search_keywords'):
            keywords.extend(cuisine_info['search_keywords'][:3])
        
        keywords.extend(cuisine_info["restaurant_types"][:2])
        keywords.append(cuisine_info["cuisine_type"])
        
        if cuisine_info.get('recommended_restaurant_names'):
            keywords.extend(cuisine_info['recommended_restaurant_names'][:2])
        
        return list(dict.fromkeys(keywords))

    def _call_map_api(self, keyword, radius):
        """调用地图API"""
        if not self.amap_key:
            return self._get_mock_restaurants(keyword)

        try:
            radius = float(radius) if radius else 3
            url = "https://restapi.amap.com/v3/place/around"
            
            lat, lng = self.user_location
            
            params = {
                'key': self.amap_key,
                'keywords': keyword,
                'location': f"{lng},{lat}",
                'radius': int(radius * 1000),
                'types': '050000',
                'sortrule': 'distance',
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
                    restaurant = {
                        'id': poi.get('id', ''),
                        'name': poi.get('name', ''),
                        'address': poi.get('address', ''),
                        'location': poi.get('location', ''),
                        'tel': poi.get('tel', ''),
                        'distance': int(float(poi.get('distance', 0))),
                        'biz_ext': poi.get('biz_ext', {})
                    }
                    
                    biz_ext = restaurant['biz_ext']
                    restaurant['rating'] = float(biz_ext.get('rating', 0)) if biz_ext.get('rating') else random.uniform(3.5, 5.0)
                    restaurant['avg_price'] = float(biz_ext.get('cost', 0)) if biz_ext.get('cost') else random.randint(30, 200)
                    
                    results.append(restaurant)
                
                return results
            else:
                return self._get_mock_restaurants(keyword)

        except Exception as e:
            return self._get_mock_restaurants(keyword)

    def _get_mock_restaurants(self, keyword):
        """生成模拟餐厅数据"""
        lang = st.session_state.get('language', 'zh')
        
        if lang == 'zh':
            restaurant_templates = {
                "火锅": ["海底捞火锅", "小龙坎火锅", "蜀大侠火锅", "大龙燚火锅", "德庄火锅"],
                "川菜": ["眉州东坡", "陈麻婆豆腐", "巴国布衣", "蜀香园", "川味观"],
                "日料": ["将太无二", "鮨然", "隐泉日料", "一风堂拉面", "味千拉面"],
                "西餐": ["王品牛排", "豪客来", "必胜客", "萨莉亚", "新元素"],
                "中餐": ["老北京炸酱面", "东来顺", "全聚德", "便宜坊", "花家怡园"]
            }
            default_names = [f"老王{keyword}馆", f"{keyword}大师", f"正宗{keyword}", f"{keyword}食府"]
        else:
            restaurant_templates = {
                "hotpot": ["Haidilao Hotpot", "Xiaolongkan Hotpot", "Shu Daxia Hotpot", "Da Longyi Hotpot", "Dezhuang Hotpot"],
                "chinese": ["Meizhou Dongpo", "Chen Mapo Tofu", "Baguo Buyi", "Shuxiang Garden", "Chuanwei Guan"],
                "japanese": ["Jiangtai Wu Er", "Sushi Ran", "Hidden Spring Japanese", "Ippudo Ramen", "Ajisen Ramen"],
                "western": ["Wang Steak", "Houcaller", "Pizza Hut", "Saizeriya", "Element Fresh"],
                "korean": ["Seoul Kitchen", "Gangnam BBQ", "Kimchi House", "Stone Bowl", "Korea Town"]
            }
            default_names = [f"{keyword} House", f"{keyword} Master", f"Authentic {keyword}", f"{keyword} Palace"]
        
        restaurant_names = default_names
        for cuisine, names in restaurant_templates.items():
            if cuisine.lower() in keyword.lower():
                restaurant_names = names
                break

        mock_restaurants = []
        base_lat, base_lng = self.user_location

        for i, name in enumerate(restaurant_names[:8]):
            lat_offset = random.uniform(-0.03, 0.03)
            lng_offset = random.uniform(-0.03, 0.03)
            
            lat = base_lat + lat_offset
            lng = base_lng + lng_offset
            distance = int(((lat - base_lat) ** 2 + (lng - base_lng) ** 2) ** 0.5 * 111000)

            mock_restaurants.append({
                'id': f'mock_{keyword}_{i}',
                'name': name,
                'address': f"{get_translation('mock_address', lang)} - {random.choice(get_translation('street_suffixes', lang).split(','))}{random.randint(1, 999)}{get_translation('number_suffix', lang)}",
                'location': f"{lng},{lat}",
                'tel': f"{random.choice(['010', '021', '020', '0755'])}-{random.randint(10000000, 99999999)}",
                'rating': round(random.uniform(3.5, 5.0), 1),
                'avg_price': random.randint(30, 200),
                'distance': distance
            })

        return mock_restaurants

    def _deduplicate_results(self, results):
        """去重"""
        seen = set()
        unique = []
        for restaurant in results:
            restaurant_id = restaurant.get('id', restaurant.get('name', ''))
            if restaurant_id not in seen:
                seen.add(restaurant_id)
                unique.append(restaurant)
        return unique

    def _rank_results(self, results, dish_name, cuisine_info):
        """智能排序"""
        for restaurant in results:
            score = 0
            name = restaurant.get('name', '')

            # 餐厅类型匹配
            for restaurant_type in cuisine_info.get('restaurant_types', []):
                if restaurant_type in name:
                    score += 25
                    break

            # AI推荐餐厅名称模式
            if cuisine_info.get('recommended_restaurant_names'):
                for pattern in cuisine_info['recommended_restaurant_names']:
                    if pattern in name:
                        score += 15
                        break

            # 评分权重
            rating = float(restaurant.get('rating', 0))
            score += rating * 5

            # 距离权重
            distance = int(restaurant.get('distance', 1000))
            score += max(0, 30 - distance / 100)

            # 价格匹配
            if cuisine_info.get('dish_characteristics', {}).get('price_range'):
                price_range = cuisine_info['dish_characteristics']['price_range']
                avg_price = restaurant.get('avg_price', 50)

                if price_range in ['低', 'Low'] and avg_price < 50:
                    score += 10
                elif price_range in ['中', 'Medium'] and 50 <= avg_price <= 100:
                    score += 10
                elif price_range in ['高', 'High'] and avg_price > 100:
                    score += 10

            restaurant['match_score'] = score
            restaurant['suggested_for'] = dish_name
            restaurant['cuisine_match'] = cuisine_info['cuisine_type']

            if cuisine_info.get('confidence', 0) > 0.9:
                restaurant['ai_recommended'] = True

        return sorted(results, key=lambda x: x['match_score'], reverse=True)

    def _render_map(self, lang):
        """渲染地图"""
        st.markdown(f"#### 🗺️ {get_translation('restaurant_locations', lang)}")

        # 城市选择
        cities = get_translation('cities_list', lang).split(',')
        city = st.selectbox(get_translation('select_city', lang), cities, key="city_select")

        city_locations = {
            get_translation('beijing', lang): [39.9042, 116.4074],
            get_translation('shanghai', lang): [31.2304, 121.4737],
            get_translation('guangzhou', lang): [23.1291, 113.2644],
            get_translation('shenzhen', lang): [22.5431, 114.0579],
            get_translation('hangzhou', lang): [30.2741, 120.1551],
            get_translation('chengdu', lang): [30.5728, 104.0668],
            get_translation('wuhan', lang): [30.5928, 114.3055],
            get_translation('xian', lang): [34.2658, 108.9541]
        }

        if city in city_locations:
            self.user_location = city_locations[city]
            st.session_state.user_location = self.user_location

        # 创建地图
        m = folium.Map(
            location=self.user_location,
            zoom_start=13,
            tiles='OpenStreetMap',
            control_scale=True
        )

        # 用户位置标记
        folium.Marker(
            location=self.user_location,
            popup=get_translation('your_location', lang),
            tooltip=get_translation('you_are_here', lang),
            icon=folium.Icon(color='green', icon='user', prefix='fa')
        ).add_to(m)

        # 餐厅标记
        if st.session_state.search_results:
            st.info(f"🔍 {get_translation('showing_on_map', lang)} {len(st.session_state.search_results)} {get_translation('search_results_count', lang)}")
            
            bounds = []
            for idx, restaurant in enumerate(st.session_state.search_results[:10]):
                if 'location' in restaurant:
                    try:
                        lng, lat = map(float, restaurant['location'].split(','))
                        
                        html = f"""
                        <div style="font-family: Arial; width: 200px;">
                            <h4 style="color: #2196F3; margin: 5px 0;">{restaurant['name']}</h4>
                            <p style="margin: 5px 0;"><b>{get_translation('address', lang)}:</b> {restaurant.get('address', get_translation('unknown', lang))}</p>
                            <p style="margin: 5px 0;"><b>{get_translation('rating', lang)}:</b> ⭐ {restaurant.get('rating', get_translation('no_rating', lang))}</p>
                            <p style="margin: 5px 0;"><b>{get_translation('avg_price', lang)}:</b> ¥{restaurant.get('avg_price', get_translation('unknown', lang))}</p>
                            <p style="margin: 5px 0;"><b>{get_translation('recommendation', lang)}:</b> {restaurant.get('suggested_for', '')}</p>
                        </div>
                        """

                        popup = folium.Popup(html=html, max_width=250)
                        color = 'red' if idx < 3 else 'blue'

                        folium.Marker(
                            location=[lat, lng],
                            popup=popup,
                            tooltip=f"{idx + 1}. {restaurant['name']}",
                            icon=folium.Icon(color=color, icon='cutlery', prefix='fa')
                        ).add_to(m)

                        bounds.append([lat, lng])

                    except Exception as e:
                        st.warning(f"{get_translation('location_parse_error', lang)}: {restaurant['name']}")

            if bounds:
                bounds.append(self.user_location)
                m.fit_bounds(bounds)

        # 显示地图
        st_folium(m, width=700, height=500, key="restaurant_map")

    def _render_search_results(self, lang):
        """渲染搜索结果"""
        if not st.session_state.search_results:
            return

        st.markdown("---")
        st.markdown(f"## 🍽️ {get_translation('search_results', lang)}")

        # AI分析结果
        if st.session_state.cuisine_info:
            cuisine_info = st.session_state.cuisine_info
            dish_name = st.session_state.search_dish

            with st.expander(f"🤖 {get_translation('ai_analysis_results', lang)}", expanded=True):
                ai_col1, ai_col2 = st.columns(2)
                
                with ai_col1:
                    st.markdown(f"**{get_translation('searched_dish', lang)}**: {dish_name}")
                    st.markdown(f"**{get_translation('identified_cuisine', lang)}**: {cuisine_info['cuisine_type']}")
                    analysis_method = get_translation('ai_analysis', lang) if cuisine_info.get('analysis_method') == 'deepseek_ai' else get_translation('rule_matching', lang)
                    st.markdown(f"**{get_translation('analysis_method', lang)}**: {analysis_method}")
                    st.markdown(f"**{get_translation('confidence_level', lang)}**: {cuisine_info.get('confidence', 0) * 100:.1f}%")

                with ai_col2:
                    if cuisine_info.get('dish_characteristics'):
                        chars = cuisine_info['dish_characteristics']
                        st.markdown(f"**{get_translation('dish_characteristics', lang)}**:")
                        if chars.get('spicy_level'):
                            try:
                                spicy_num = int(float(chars['spicy_level']))
                                st.markdown(f"- {get_translation('spicy_level', lang)}: {'🌶️' * spicy_num}")
                            except:
                                st.markdown(f"- {get_translation('spicy_level', lang)}: {chars['spicy_level']}")
                        if chars.get('price_range'):
                            st.markdown(f"- {get_translation('price', lang)}: {chars['price_range']}")
                        if chars.get('cooking_method'):
                            st.markdown(f"- {get_translation('cooking_method', lang)}: {chars['cooking_method']}")

                if cuisine_info.get('similar_dishes'):
                    st.markdown(f"**{get_translation('similar_dishes', lang)}**: {', '.join(cuisine_info['similar_dishes'][:5])}")

        # 餐厅列表
        st.info(f"📊 {get_translation('found_count', lang)} {len(st.session_state.search_results)} {get_translation('related_restaurants', lang)}")

        for idx, restaurant in enumerate(st.session_state.search_results[:10]):
            with st.container():
                # 餐厅标题
                ai_badge = "🤖 " if restaurant.get('ai_recommended') else ""
                st.markdown(f"### {ai_badge}{idx + 1}. {restaurant['name']}")
                
                # 餐厅信息
                info_parts = []
                info_parts.append(f"📍 {restaurant.get('address', get_translation('unknown_address', lang))}")
                info_parts.append(f"⭐ {restaurant.get('rating', 'N/A')}")
                info_parts.append(f"💰 {get_translation('avg_price', lang)} ¥{restaurant.get('avg_price', 'N/A')}")
                
                if 'distance' in restaurant:
                    distance = restaurant['distance']
                    if distance < 1000:
                        info_parts.append(f"📏 {distance}m")
                    else:
                        info_parts.append(f"📏 {distance / 1000:.1f}km")
                
                st.markdown(" | ".join(info_parts))

                # 操作按钮
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                
                with btn_col1:
                    if st.button(f"📋 {get_translation('view_details', lang)}", key=f"detail_btn_{idx}"):
                        self._show_restaurant_detail(restaurant, idx, lang)
                
                with btn_col2:
                    if st.button(f"🧭 {get_translation('navigation', lang)}", key=f"nav_btn_{idx}"):
                        self._show_navigation(restaurant, idx, lang)
                
                with btn_col3:
                    if st.button(f"⭐ {get_translation('favorite', lang)}", key=f"fav_btn_{idx}"):
                        self._add_to_favorites(restaurant, lang)
                
                with btn_col4:
                    if restaurant.get('tel'):
                        st.markdown(f"📞 {restaurant['tel']}")

                st.divider()

    def _show_restaurant_detail(self, restaurant, idx, lang):
        """显示餐厅详情"""
        with st.expander(f"🍽️ {restaurant['name']} - {get_translation('detailed_info', lang)}", expanded=True):
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown(f"**{get_translation('basic_info', lang)}**")
                st.write(f"📍 {get_translation('address', lang)}: {restaurant.get('address', get_translation('unknown', lang))}")
                st.write(f"📞 {get_translation('phone', lang)}: {restaurant.get('tel', get_translation('unknown', lang))}")
                st.write(f"⭐ {get_translation('rating', lang)}: {restaurant.get('rating', get_translation('no_rating', lang))}")
                st.write(f"💰 {get_translation('avg_price', lang)}: ¥{restaurant.get('avg_price', get_translation('unknown', lang))}")

            with detail_col2:
                st.markdown(f"**{get_translation('recommendation_info', lang)}**")
                st.write(f"🍽️ {get_translation('recommended_dish', lang)}: {restaurant.get('suggested_for', '')}")
                st.write(f"🏷️ {get_translation('cuisine_match', lang)}: {restaurant.get('cuisine_match', '')}")
                if restaurant.get('ai_recommended'):
                    st.write(f"🤖 {get_translation('ai_recommended', lang)}")
                if 'distance' in restaurant:
                    distance = restaurant['distance']
                    if distance < 1000:
                        st.write(f"📏 {get_translation('distance', lang)}: {distance}m")
                    else:
                        st.write(f"📏 {get_translation('distance', lang)}: {distance / 1000:.1f}km")

    def _show_navigation(self, restaurant, idx, lang):
        """显示导航选项"""
        if 'location' in restaurant:
            location = restaurant['location']
            restaurant_name = restaurant['name']
            
            with st.expander(f"🚗 {restaurant_name} - {get_translation('navigation_options', lang)}", expanded=True):
                st.markdown(f"**{get_translation('choose_navigation', lang)}:**")

                lng, lat = location.split(',')
                amap_url = f"https://uri.amap.com/navigation?to={location},{restaurant_name}&mode=car&policy=1&src=myapp&coordinate=gaode&callnative=0"
                baidu_url = f"http://api.map.baidu.com/direction?destination=latlng:{lat},{lng}|name:{restaurant_name}&mode=driving&src=webapp.baidu.openAPIdemo"
                tx_url = f"https://apis.map.qq.com/uri/v1/routeplan?type=drive&to={restaurant_name}&tocoord={lat},{lng}"

                st.markdown(f"- [📍 {get_translation('amap_navigation', lang)}]({amap_url})")
                st.markdown(f"- [📍 {get_translation('baidu_navigation', lang)}]({baidu_url})")
                st.markdown(f"- [📍 {get_translation('tencent_navigation', lang)}]({tx_url})")

    def _add_to_favorites(self, restaurant, lang):
        """添加到收藏"""
        if 'favorites' not in st.session_state:
            st.session_state.favorites = []

        if not any(fav['id'] == restaurant['id'] for fav in st.session_state.favorites):
            st.session_state.favorites.append(restaurant)
            st.success(f"{get_translation('favorited', lang)} {restaurant['name']}")

            # 如果用户已登录，保存到数据库
            if st.session_state.get('logged_in') and st.session_state.get('db_manager'):
                try:
                    favorite_data = {
                        'restaurant': restaurant,
                        'saved_at': datetime.now(),
                        'dish_searched': st.session_state.get('search_dish', ''),
                        'type': 'restaurant_favorite'
                    }
                    st.session_state.db_manager.save_recipe(st.session_state.username, favorite_data)
                except Exception as e:
                    st.warning(get_translation('cloud_save_failed', lang))
        else:
            st.warning(f"{restaurant['name']} {get_translation('already_favorited', lang)}")
