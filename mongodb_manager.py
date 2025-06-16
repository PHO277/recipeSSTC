from pymongo import MongoClient
from datetime import datetime
import hashlib


class MongoDBManager:
    def __init__(self, connection_string):
        """初始化 MongoDB 连接"""
        self.client = MongoClient(connection_string)
        self.db = self.client['recipe_db']
        self.users_collection = self.db['users']
        self.recipes_collection = self.db['recipes']

        # 创建索引
        self._create_indexes()

    def _create_indexes(self):
        """创建数据库索引"""
        try:
            self.users_collection.create_index("username", unique=True)
            self.recipes_collection.create_index([("username", 1), ("created", -1)])
        except:
            pass

    def hash_password(self, password):
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password, language="zh", email=None):
        """创建新用户"""
        try:
            user_doc = {
                "username": username,
                "password": self.hash_password(password),
                "email": email,
                "language": language,
                "created": datetime.utcnow(),
                "last_login": None
            }

            self.users_collection.insert_one(user_doc)
            return True, "注册成功"

        except Exception as e:
            if "duplicate key" in str(e):
                return False, "用户名已存在"
            return False, f"注册失败: {str(e)}"

    def verify_user(self, username, password):
        """验证用户登录"""
        user = self.users_collection.find_one({"username": username})
        if not user:
            return False, None

        if user["password"] == self.hash_password(password):
            # 更新最后登录时间
            self.users_collection.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            return True, user

        return False, None

    def get_user(self, username):
        """获取用户信息"""
        return self.users_collection.find_one({"username": username})

    def update_user_language(self, username, language):
        """更新用户语言"""
        self.users_collection.update_one(
            {"username": username},
            {"$set": {"language": language}}
        )

    def save_recipe(self, username, recipe_data):
        """保存食谱"""
        recipe_doc = {
            "username": username,
            "title": recipe_data.get("title", ""),
            "description": recipe_data.get("description", ""),
            "ingredients": recipe_data.get("ingredients", []),
            "instructions": recipe_data.get("instructions", []),
            "nutrition_info": recipe_data.get("nutrition", ""),
            "serves": recipe_data.get("serves", ""),
            "prep_time": recipe_data.get("prep_time", ""),
            "cook_time": recipe_data.get("cook_time", ""),
            "difficulty": recipe_data.get("difficulty", ""),
            "cuisine": recipe_data.get("cuisine", ""),
            "diet": recipe_data.get("diet", ""),
            "goal": recipe_data.get("goal", ""),
            "created": datetime.utcnow(),
            "rating": recipe_data.get("rating", 0),
            "tags": recipe_data.get("tags", []),
            "notes": recipe_data.get("notes", ""),
            # 保持向后兼容性
            "recipe_text": recipe_data.get("recipe_text", ""),
            "nutrition": recipe_data.get("nutrition", "")
        }

        result = self.recipes_collection.insert_one(recipe_doc)
        return str(result.inserted_id)

    def get_user_recipes(self, username, limit=50, skip=0):
        """获取用户的食谱"""
        recipes = self.recipes_collection.find(
            {"username": username}
        ).sort("created", -1).skip(skip).limit(limit)

        return list(recipes)

    def delete_recipe(self, recipe_id):
        """删除食谱"""
        from bson import ObjectId
        result = self.recipes_collection.delete_one({"_id": ObjectId(recipe_id)})
        return result.deleted_count > 0

    def search_recipes(self, username, query):
        """搜索食谱"""
        search_filter = {
            "username": username,
            "$or": [
                {"ingredients": {"$regex": query, "$options": "i"}},
                {"recipe_text": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}}
            ]
        }

        return list(self.recipes_collection.find(search_filter).sort("created", -1))

    def get_recipe_statistics(self, username):
        """获取用户食谱统计"""
        pipeline = [
            {"$match": {"username": username}},
            {"$group": {
                "_id": None,
                "total_recipes": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
                "most_used_diet": {"$push": "$diet"},
                "most_used_goal": {"$push": "$goal"}
            }}
        ]

        stats = list(self.recipes_collection.aggregate(pipeline))
        return stats[0] if stats else {}