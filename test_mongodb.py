from pymongo import MongoClient


import streamlit as st
import os

# 从环境变量或 Streamlit secrets 获取
MONGODB_URI = st.secrets.get("MONGODB_URI", os.getenv("MONGODB_URI"))

# 不要在代码中硬编码任何密码！

try:
    # 连接到 MongoDB
    client = MongoClient(MONGODB_URI)

    # 测试连接
    db = client.recipe_db

    # 插入测试数据
    test_collection = db.test
    test_doc = {"test": "Hello MongoDB Atlas!", "timestamp": "2024-12-12"}
    result = test_collection.insert_one(test_doc)

    print(f"✅ 连接成功！")
    print(f"插入的文档 ID: {result.inserted_id}")

    # 读取数据
    found_doc = test_collection.find_one({"test": "Hello MongoDB Atlas!"})
    print(f"找到的文档: {found_doc}")

    # 清理测试数据
    test_collection.delete_one({"_id": result.inserted_id})

    client.close()

except Exception as e:
    print(f"❌ 连接失败: {e}")