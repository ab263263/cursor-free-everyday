#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
轻量级版本配置测试脚本
测试 HTTP 协议版本的环境配置

测试项目:
1. Python 基础环境
2. HTTP 请求功能
3. HTML 解析能力
4. Gemini AI API
5. 邮件发送功能
6. 论坛访问测试
"""

import sys
import json
import smtplib
import requests
import re
from datetime import datetime
from email.mime.text import MIMEText

# 配置信息
GEMINI_API_HOST = "https://generativelanguage.googleapis.com"
GEMINI_API_KEY = "AIzaSyBAapmvw5zq9s3ro2EjGH4NgY0BNhAODgw"

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = "2918627578@qq.com"
SENDER_PASSWORD = "djppyahldzyqdcdb"
RECEIVER_EMAIL = "txb528@163.com"

def test_python_environment():
    """测试 Python 环境"""
    print("🐍 测试 Python 环境...")
    
    # 检查 Python 版本
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"❌ Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        return False
    
    # 检查必需模块
    required_modules = ['requests', 'json', 'smtplib', 're', 'datetime']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} 模块可用")
        except ImportError:
            print(f"❌ {module} 模块不可用")
            return False
    
    return True

def test_beautifulsoup():
    """测试 BeautifulSoup 环境"""
    print("\n🍲 测试 HTML 解析环境...")
    
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup4 已安装")
        
        # 测试解析功能
        test_html = '<div><a href="/test">测试链接</a></div>'
        soup = BeautifulSoup(test_html, 'html.parser')
        link = soup.find('a')
        
        if link and link.get_text() == '测试链接':
            print("✅ HTML 解析功能正常")
            return True
        else:
            print("❌ HTML 解析功能异常")
            return False
            
    except ImportError:
        print("⚠️ BeautifulSoup4 未安装，将使用正则表达式解析")
        print("💡 安装命令: pip install beautifulsoup4 lxml")
        
        # 测试正则表达式解析
        test_html = '<a href="/test">测试链接</a>'
        pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>'
        match = re.search(pattern, test_html)
        
        if match and match.group(2) == '测试链接':
            print("✅ 正则表达式解析功能正常")
            return True
        else:
            print("❌ 正则表达式解析功能异常")
            return False

def test_http_requests():
    """测试 HTTP 请求功能"""
    print("\n🌐 测试 HTTP 请求功能...")
    
    try:
        # 创建会话
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 测试基本请求
        response = session.get('https://httpbin.org/get', timeout=10)
        if response.status_code == 200:
            print("✅ HTTP 请求功能正常")
        else:
            print(f"❌ HTTP 请求异常: {response.status_code}")
            return False
        
        # 测试中文编码
        response = session.get('https://www.baidu.com', timeout=10)
        if response.status_code == 200 and '百度' in response.text:
            print("✅ 中文编码处理正常")
        else:
            print("⚠️ 中文编码处理可能有问题")
        
        return True
        
    except Exception as e:
        print(f"❌ HTTP 请求测试失败: {e}")
        return False

def test_forum_access():
    """测试论坛访问"""
    print("\n🕷️ 测试卡农论坛访问...")
    
    test_urls = [
        "https://www.51kanong.com/",
        "https://www.51kanong.com/yh-169-1.htm",
        "https://www.51kanong.com/yh-282-1.htm"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    success_count = 0
    
    for url in test_urls:
        try:
            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                # 检查页面内容
                if any(keyword in response.text for keyword in ['卡农', '51kanong', '论坛']):
                    print(f"✅ 论坛访问正常: {url}")
                    success_count += 1
                else:
                    print(f"⚠️ 论坛页面内容异常: {url}")
            else:
                print(f"❌ 论坛访问失败: {url} (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"❌ 论坛访问异常: {url} ({e})")
    
    return success_count >= 2  # 至少2个URL访问成功

def test_html_parsing():
    """测试 HTML 解析能力"""
    print("\n📋 测试 HTML 解析能力...")
    
    # 模拟论坛页面结构
    test_html = '''
    <table>
        <tbody>
            <tr>
                <td><a href="/xyk-123456-1.htm">测试帖子标题</a></td>
                <td><a href="/s-uid-789">测试作者</a></td>
                <td><em>2小时前</em></td>
            </tr>
        </tbody>
    </table>
    '''
    
    try:
        # 尝试 BeautifulSoup 解析
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(test_html, 'html.parser')
            
            title_link = soup.select_one('a[href*="xyk-"]')
            author_link = soup.select_one('a[href*="s-uid-"]')
            time_elem = soup.select_one('em')
            
            if (title_link and title_link.get_text() == '测试帖子标题' and
                author_link and author_link.get_text() == '测试作者' and
                time_elem and time_elem.get_text() == '2小时前'):
                print("✅ BeautifulSoup 解析测试通过")
                return True
            else:
                print("❌ BeautifulSoup 解析测试失败")
                
        except ImportError:
            # 使用正则表达式解析
            title_pattern = r'<a[^>]*href="([^"]*xyk-[^"]*)"[^>]*>([^<]+)</a>'
            author_pattern = r'<a[^>]*href="([^"]*s-uid-[^"]*)"[^>]*>([^<]+)</a>'
            time_pattern = r'<em>([^<]+)</em>'
            
            title_match = re.search(title_pattern, test_html)
            author_match = re.search(author_pattern, test_html)
            time_match = re.search(time_pattern, test_html)
            
            if (title_match and title_match.group(2) == '测试帖子标题' and
                author_match and author_match.group(2) == '测试作者' and
                time_match and time_match.group(1) == '2小时前'):
                print("✅ 正则表达式解析测试通过")
                return True
            else:
                print("❌ 正则表达式解析测试失败")
        
        return False
        
    except Exception as e:
        print(f"❌ HTML 解析测试异常: {e}")
        return False

def test_gemini_api():
    """测试 Gemini AI API"""
    print("\n🤖 测试 Gemini AI API...")
    
    try:
        url = f"{GEMINI_API_HOST}/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': GEMINI_API_KEY
        }
        
        data = {
            "contents": [{
                "parts": [{"text": "请简单回复'轻量级测试成功'"}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 50,
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Gemini API 测试成功: {content.strip()}")
                return True
            else:
                print("❌ Gemini API 响应格式异常")
                return False
        else:
            print(f"❌ Gemini API 请求失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API 测试异常: {e}")
        return False

def test_email_config():
    """测试邮件配置"""
    print("\n📧 测试邮件配置...")
    
    try:
        msg = MIMEText("这是青龙面板轻量级监控的测试邮件", 'plain', 'utf-8')
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"青龙面板轻量级测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        print("✅ 邮件发送测试成功")
        print(f"📬 测试邮件已发送到: {RECEIVER_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送测试失败: {e}")
        return False

def calculate_memory_usage():
    """估算内存使用量"""
    print("\n💾 估算内存使用量...")
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"✅ 当前进程内存使用: {memory_mb:.1f} MB")
        
        if memory_mb < 100:
            print("✅ 内存使用量符合轻量级要求 (< 100MB)")
            return True
        else:
            print("⚠️ 内存使用量偏高，但仍在可接受范围")
            return True
            
    except ImportError:
        print("ℹ️ psutil 未安装，无法精确测量内存使用")
        print("💡 预估内存使用: 20-50MB (轻量级版本)")
        return True

def generate_test_report(results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📋 轻量级版本测试报告")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"总测试项: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n💾 内存优势:")
    print("  🔹 无需浏览器: 节省 200-300MB 内存")
    print("  🔹 轻量级解析: 仅需 20-50MB 内存")
    print("  🔹 适合青龙面板: 资源占用极低")
    
    if passed_tests >= total_tests * 0.8:  # 80% 通过率
        print("\n🎉 轻量级版本配置良好！可以正常使用。")
        print("💡 建议在青龙面板中设置定时任务。")
    else:
        print("\n⚠️ 部分测试失败，请根据上述信息修复问题。")

def main():
    """主测试函数"""
    print("🧪 青龙面板 - 卡农论坛轻量级监控配置测试")
    print("="*60)
    print("轻量级版本特点:")
    print("  🔹 基于 HTTP 协议直接获取")
    print("  🔹 无需浏览器，内存占用 < 50MB")
    print("  🔹 适合资源受限的青龙面板环境")
    print("="*60)
    
    # 执行测试
    test_results = {}
    
    test_results["Python环境"] = test_python_environment()
    test_results["HTML解析"] = test_beautifulsoup()
    test_results["HTTP请求"] = test_http_requests()
    test_results["论坛访问"] = test_forum_access()
    test_results["HTML解析能力"] = test_html_parsing()
    test_results["Gemini API"] = test_gemini_api()
    test_results["邮件配置"] = test_email_config()
    test_results["内存使用"] = calculate_memory_usage()
    
    # 生成报告
    generate_test_report(test_results)
    
    print("\n" + "="*60)
    print("测试完成！")
    
    # 青龙面板环境检测
    try:
        import os
        if os.path.exists("/ql"):
            print("\n🐉 检测到青龙面板环境")
            print("📁 建议脚本路径: /ql/scripts/qinglong_kanong_lightweight.py")
            print("📋 建议定时规则: 0 */2 * * * (每2小时执行)")
            print("💾 内存优势: 轻量级版本仅需 20-50MB")
    except:
        pass

if __name__ == "__main__":
    main()
