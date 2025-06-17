import os
import re
from pathlib import Path

# 定义敏感信息模式
SENSITIVE_PATTERNS = [
    (r'api[_-]?key\s*=\s*["\']?[a-zA-Z0-9_\-]{20,}', 'API密钥'),
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI密钥'),
    (r'mongodb\+srv://[^"\s]+', 'MongoDB连接串'),
    (r'password\s*=\s*["\'][^"\']+["\']', '密码'),
    (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', 'Secret密钥'),
]

# 要检查的文件类型
CHECK_EXTENSIONS = {'.py', '.js', '.json', '.yaml', '.yml', '.toml', '.txt', '.md'}

# 要排除的目录
EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'node_modules'}

# 要排除的文件
EXCLUDE_FILES = {'.gitignore', 'requirements.txt', 'README.md'}


def check_file(filepath):
    """检查单个文件"""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern, desc in SENSITIVE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # 排除注释和示例
                    if not any(marker in line for marker in ['#', '//', 'example', 'your_']):
                        issues.append({
                            'file': filepath,
                            'line': line_num,
                            'type': desc,
                            'content': line.strip()
                        })
    except:
        pass
    return issues


def main():
    print("🔍 检查敏感信息...\n")

    all_issues = []

    for root, dirs, files in os.walk('.'):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file in EXCLUDE_FILES:
                continue

            filepath = Path(root) / file
            if filepath.suffix in CHECK_EXTENSIONS:
                issues = check_file(filepath)
                all_issues.extend(issues)

    if all_issues:
        print(f"⚠️  发现 {len(all_issues)} 个可能的敏感信息：\n")
        for issue in all_issues:
            print(f"📍 文件: {issue['file']}")
            print(f"   行号: {issue['line']}")
            print(f"   类型: {issue['type']}")
            print(f"   内容: {issue['content'][:50]}...")
            print()
    else:
        print("✅ 未发现敏感信息！")

    # 检查敏感文件
    print("\n📁 检查敏感文件...")
    sensitive_files = ['.env', 'secrets.toml', '.streamlit/secrets.toml']
    found_sensitive = []

    for sensitive_file in sensitive_files:
        if Path(sensitive_file).exists():
            found_sensitive.append(sensitive_file)

    if found_sensitive:
        print(f"⚠️  发现敏感文件（确保已在.gitignore中）：")
        for f in found_sensitive:
            print(f"   - {f}")

        # 检查是否在git中
        print("\n🔍 检查这些文件是否会被提交...")
        import subprocess
        for f in found_sensitive:
            try:
                result = subprocess.run(['git', 'ls-files', f],
                                        capture_output=True, text=True)
                if result.stdout.strip():
                    print(f"   ❌ {f} 将会被提交！请运行: git rm --cached {f}")
                else:
                    print(f"   ✅ {f} 不会被提交")
            except:
                pass


if __name__ == "__main__":
    main()