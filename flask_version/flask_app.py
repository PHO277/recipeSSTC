from flask import Flask, render_template, request, jsonify, session
import os
import sys

# 添加父目录到路径，这样可以导入原来的模块
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# 将来可以导入你原来的组件
# from components.generate_recipe import generate_recipe_logic
# from components.auth import authenticate_user

app = Flask(__name__)
app.secret_key = 'recipe-app-secret-key-2025'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "success", "message": "Flask version running in recipesstc!"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # TODO: 集成原来的 components/auth.py
    if username and password:
        session['logged_in'] = True
        session['username'] = username
        return jsonify({"success": True, "message": "Login successful"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"})

@app.route('/api/generate-recipe', methods=['POST'])
def generate_recipe():
    data = request.json
    user_input = data.get('input', '')
    
    # TODO: 集成原来的 components/generate_recipe.py
    sample_recipe = f"""
    <div class="recipe-card">
        <h3>🤖 AI Generated Recipe</h3>
        <p><strong>Based on:</strong> {user_input}</p>
        <div class="ingredients">
            <h4>📝 Ingredients:</h4>
            <ul>
                <li>Fresh ingredients based on your input</li>
                <li>Seasonal vegetables</li>
                <li>Quality proteins</li>
            </ul>
        </div>
        <div class="instructions">
            <h4>👩‍🍳 Instructions:</h4>
            <ol>
                <li>Prepare all ingredients</li>
                <li>Follow cooking method</li>
                <li>Plate and enjoy!</li>
            </ol>
        </div>
    </div>
    """
    
    return jsonify({"success": True, "recipe": sample_recipe})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
