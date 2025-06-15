#!/usr/bin/env python3
"""
Recipe App - 完全集成版本
集成所有原有功能的Flask应用
"""

from flask import Flask, render_template, request, jsonify, session, send_file
import os
import sys
import json
import traceback
from datetime import datetime
import base64
import io
from werkzeug.utils import secure_filename

# 添加父目录到路径，导入原有模块
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

try:
    from mongodb_manager import MongoDBManager
    from llm_interface import LLMInterface  
    from nutrition_analyzer import NutritionAnalyzer
    from components.image_input_modal import ImageInputModal
    print("✅ Successfully imported all original modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Will use fallback implementations")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'recipe-app-integrated-2025')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 初始化服务
services = {}

def initialize_services():
    """初始化所有服务"""
    global services
    
    try:
        # MongoDB连接
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/recipe_app')
        services['db'] = MongoDBManager(mongodb_uri)
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        services['db'] = None
    
    try:
        # DeepSeek API
        deepseek_key = os.getenv('DEEPSEEK_API_KEY', 'fallback-key')
        services['llm'] = LLMInterface(deepseek_key)
        print("✅ LLM interface initialized")
    except Exception as e:
        print(f"⚠️  LLM initialization failed: {e}")
        services['llm'] = None
    
    try:
        # 营养分析器
        services['nutrition'] = NutritionAnalyzer()
        print("✅ Nutrition analyzer ready")
    except Exception as e:
        print(f"⚠️  Nutrition analyzer failed: {e}")
        services['nutrition'] = None
    
    try:
        # 图像识别
        services['image'] = ImageInputModal()
        print("✅ Image recognition ready")
    except Exception as e:
        print(f"⚠️  Image recognition failed: {e}")
        services['image'] = None

# 启动时初始化服务
initialize_services()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/test', methods=['GET'])
def api_test():
    """API测试端点"""
    return jsonify({
        "status": "success",
        "message": "Integrated Flask app is running!",
        "services": {
            "database": services['db'] is not None,
            "llm": services['llm'] is not None,
            "nutrition": services['nutrition'] is not None,
            "image": services['image'] is not None
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录 - 使用原有数据库验证"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"success": False, "message": "请输入用户名和密码"})
    
    try:
        if services['db']:
            # 使用原有数据库验证
            user = services['db'].verify_user(username, password)
            if user:
                session['logged_in'] = True
                session['username'] = username
                session['user_data'] = user
                return jsonify({
                    "success": True, 
                    "message": f"欢迎回来，{username}！",
                    "user": {
                        "username": username,
                        "email": user.get('email', ''),
                        "language": user.get('language', 'zh')
                    }
                })
            else:
                return jsonify({"success": False, "message": "用户名或密码错误"})
        else:
            # 降级处理：简单验证
            if username == "demo" and password == "demo":
                session['logged_in'] = True
                session['username'] = username
                return jsonify({
                    "success": True,
                    "message": f"演示模式登录成功！",
                    "user": {"username": username, "language": "zh"}
                })
            else:
                return jsonify({"success": False, "message": "演示模式请使用 demo/demo"})
                
    except Exception as e:
        print(f"Login error: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"登录错误: {str(e)}"})

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()
    language = data.get('language', 'zh')
    
    if not all([username, password]):
        return jsonify({"success": False, "message": "用户名和密码不能为空"})
    
    try:
        if services['db']:
            # 检查用户是否已存在
            existing_user = services['db'].get_user(username)
            if existing_user:
                return jsonify({"success": False, "message": "用户名已存在"})
            
            # 创建新用户
            result = services['db'].create_user(username, password, language, email)
            if result:
                return jsonify({"success": True, "message": "注册成功！请登录"})
            else:
                return jsonify({"success": False, "message": "注册失败，请重试"})
        else:
            return jsonify({"success": False, "message": "数据库服务不可用"})
            
    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({"success": False, "message": f"注册错误: {str(e)}"})

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({"success": True, "message": "已成功登出"})

@app.route('/api/generate-recipe', methods=['POST'])
def generate_recipe():
    """生成食谱 - 使用原有AI功能"""
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "请先登录"})
    
    data = request.json
    username = session.get('username')
    
    # 提取参数
    ingredients = data.get('input', data.get('ingredients', ''))
    diet = data.get('diet', '')
    goal = data.get('goal', '')
    language = data.get('language', 'zh')
    cuisine = data.get('cuisine', '')
    cooking_time = data.get('prepTime', data.get('cooking_time', ''))
    difficulty = data.get('difficulty', '')
    servings = data.get('servings', 4)
    
    if not ingredients:
        return jsonify({"success": False, "message": "请输入食材或描述"})
    
    try:
        if services['llm']:
            # 使用原有的LLM接口生成食谱
            recipe_result = services['llm'].generate_recipe_and_nutrition(
                ingredients=ingredients,
                diet=diet,
                goal=goal,
                language=language,
                cuisine=cuisine,
                cooking_time=cooking_time,
                difficulty=difficulty,
                servings=servings
            )
            
            # 处理营养信息
            nutrition_info = ""
            if services['nutrition'] and recipe_result:
                try:
                    nutrition_info = services['nutrition'].parse_nutrition(recipe_result)
                except Exception as e:
                    print(f"Nutrition parsing error: {e}")
            
            # 格式化食谱显示
            if isinstance(recipe_result, dict):
                recipe_html = format_recipe_html(recipe_result, nutrition_info)
            else:
                recipe_html = f"<div class='recipe-card'>{recipe_result}</div>"
            
            # 保存到数据库
            if services['db']:
                try:
                    recipe_data = {
                        'title': ingredients[:50] + ('...' if len(ingredients) > 50 else ''),
                        'content': recipe_result,
                        'nutrition': nutrition_info,
                        'generated_at': datetime.now(),
                        'parameters': {
                            'ingredients': ingredients,
                            'diet': diet,
                            'goal': goal,
                            'cuisine': cuisine,
                            'difficulty': difficulty,
                            'servings': servings
                        }
                    }
                    services['db'].save_recipe(username, recipe_data)
                except Exception as e:
                    print(f"Save recipe error: {e}")
            
            return jsonify({
                "success": True,
                "recipe": recipe_html,
                "raw_data": recipe_result
            })
            
        else:
            # 降级处理：返回模拟食谱
            sample_recipe = generate_fallback_recipe(ingredients, language)
            return jsonify({
                "success": True,
                "recipe": sample_recipe
            })
            
    except Exception as e:
        print(f"Generate recipe error: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "message": f"生成食谱时出错: {str(e)}"
        })

@app.route('/api/image-recognition', methods=['POST'])
def image_recognition():
    """图像识别 - 使用原有功能"""
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "请先登录"})
    
    try:
        files = request.files.getlist('images')
        language = request.form.get('language', 'zh')
        
        if not files or not files[0].filename:
            return jsonify({"success": False, "message": "请上传图片"})
        
        if services['image']:
            # 使用原有的图像识别功能
            results = services['image'].call_siliconflow_api(files, language)
            return jsonify({
                "success": True,
                "ingredients": results
            })
        else:
            # 降级处理：返回示例食材
            return jsonify({
                "success": True,
                "ingredients": ["番茄", "洋葱", "大蒜", "胡萝卜"],
                "message": "图像识别服务不可用，返回示例食材"
            })
            
    except Exception as e:
        print(f"Image recognition error: {e}")
        return jsonify({
            "success": False,
            "message": f"图像识别失败: {str(e)}"
        })

@app.route('/api/my-recipes', methods=['GET'])
def get_my_recipes():
    """获取用户的食谱"""
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "请先登录"})
    
    username = session.get('username')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    skip = (page - 1) * limit
    
    try:
        if services['db']:
            recipes = services['db'].get_user_recipes(username, limit, skip)
            return jsonify({
                "success": True,
                "recipes": recipes,
                "page": page,
                "limit": limit
            })
        else:
            # 降级处理：从本地存储获取
            return jsonify({
                "success": True,
                "recipes": [],
                "message": "数据库不可用，请使用本地存储"
            })
            
    except Exception as e:
        print(f"Get recipes error: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取用户统计数据"""
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "请先登录"})
    
    username = session.get('username')
    
    try:
        if services['db']:
            stats = services['db'].get_recipe_statistics(username)
            return jsonify({
                "success": True,
                "statistics": stats
            })
        else:
            # 降级处理：返回示例统计
            return jsonify({
                "success": True,
                "statistics": {
                    "total_recipes": 0,
                    "average_rating": 0,
                    "favorite_cuisine": "未知",
                    "monthly_recipes": 0
                }
            })
            
    except Exception as e:
        print(f"Get statistics error: {e}")
        return jsonify({"success": False, "message": str(e)})

def format_recipe_html(recipe_data, nutrition_info=""):
    """格式化食谱为HTML"""
    if isinstance(recipe_data, dict):
        title = recipe_data.get('title', '美味食谱')
        ingredients = recipe_data.get('ingredients', [])
        instructions = recipe_data.get('instructions', [])
        
        html = f"""
        <div class="recipe-card">
            <h3>🍳 {title}</h3>
            
            <div class="ingredients">
                <h4>📝 食材:</h4>
                <ul>
        """
        
        for ingredient in ingredients:
            html += f"<li>{ingredient}</li>"
        
        html += """
                </ul>
            </div>
            
            <div class="instructions">
                <h4>👩‍🍳 制作步骤:</h4>
                <ol>
        """
        
        for step in instructions:
            html += f"<li>{step}</li>"
        
        html += "</ol></div>"
        
        if nutrition_info:
            html += f"""
            <div class="nutrition">
                <h4>🥗 营养信息:</h4>
                <div class="nutrition-content">{nutrition_info}</div>
            </div>
            """
        
        html += "</div>"
        return html
    else:
        return f"<div class='recipe-card'>{recipe_data}</div>"

def generate_fallback_recipe(ingredients, language="zh"):
    """生成降级食谱"""
    if language == 'zh':
        return f"""
        <div class="recipe-card">
            <h3>🍳 基于 "{ingredients}" 的简易食谱</h3>
            <p><strong>食材:</strong> {ingredients}</p>
            
            <div class="ingredients">
                <h4>📝 建议食材:</h4>
                <ul>
                    <li>主要食材: {ingredients}</li>
                    <li>调味料: 盐、胡椒粉、生抽</li>
                    <li>配菜: 根据个人喜好添加</li>
                </ul>
            </div>
            
            <div class="instructions">
                <h4>👩‍🍳 制作步骤:</h4>
                <ol>
                    <li>清洗并准备所有食材</li>
                    <li>根据食材特性选择合适的烹饪方法</li>
                    <li>加入调味料，调节口味</li>
                    <li>装盘享用</li>
                </ol>
            </div>
            
            <p><em>注意: 这是系统生成的基础食谱，AI服务暂时不可用。</em></p>
        </div>
        """
    else:
        return f"""
        <div class="recipe-card">
            <h3>🍳 Simple Recipe with "{ingredients}"</h3>
            <p><strong>Main ingredient:</strong> {ingredients}</p>
            
            <div class="ingredients">
                <h4>📝 Suggested ingredients:</h4>
                <ul>
                    <li>Main: {ingredients}</li>
                    <li>Seasonings: salt, pepper, soy sauce</li>
                    <li>Additional: add as preferred</li>
                </ul>
            </div>
            
            <div class="instructions">
                <h4>👩‍🍳 Instructions:</h4>
                <ol>
                    <li>Clean and prepare all ingredients</li>
                    <li>Choose appropriate cooking method</li>
                    <li>Season to taste</li>
                    <li>Serve and enjoy</li>
                </ol>
            </div>
            
            <p><em>Note: This is a basic recipe. AI service is temporarily unavailable.</em></p>
        </div>
        """

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🍳 Recipe App - 完全集成版本启动中...")
    print("📊 服务状态检查:")
    for service_name, service in services.items():
        status = "✅ 已连接" if service else "❌ 不可用"
        print(f"   • {service_name}: {status}")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
