#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
青龙面板配置测试脚本
用于验证环境配置和API连接是否正常

运行此脚本可以快速检测:
1. Python 依赖是否安装正确
2. Playwright 浏览器是否可用
3. Gemini AI API 是否连接正常
4. 邮件发送是否配置正确
5. 网络连接是否正常
"""

import sys
import json
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText

# 配置信息 (与主脚本保持一致)
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
    
    # 检查基础模块
    try:
        import asyncio
        print("✅ asyncio 模块可用")
    except ImportError:
        print("❌ asyncio 模块不可用")
        return False
    
    try:
        import requests
        print("✅ requests 模块可用")
    except ImportError:
        print("❌ requests 模块不可用")
        return False
    
    return True

def test_playwright():
    """测试 Playwright 环境"""
    print("\n🎭 测试 Playwright 环境...")
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright 模块已安装")
        
        # 测试浏览器启动
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.baidu.com", timeout=10000)
            title = page.title()
            browser.close()
            
            if title:
                print(f"✅ 浏览器测试成功: {title}")
                return True
            else:
                print("❌ 浏览器测试失败: 无法获取页面标题")
                return False
                
    except ImportError:
        print("❌ Playwright 模块未安装")
        print("💡 安装命令: pip install playwright && playwright install chromium")
        return False
    except Exception as e:
        print(f"❌ Playwright 测试失败: {e}")
        return False

def test_gemini_api():
    """测试 Gemini AI API"""
    print("\n🤖 测试 Gemini AI API...")

    try:
        # 更新为正确的 Gemini API 端点
        url = f"{GEMINI_API_HOST}/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': GEMINI_API_KEY
        }

        data = {
            "contents": [{
                "parts": [{"text": "请回复'测试成功'"}]
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
                print(f"响应内容: {response.text}")
                return False
        else:
            print(f"❌ Gemini API 请求失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Gemini API 测试异常: {e}")
        return False

def test_email_config():
    """测试邮件配置"""
    print("\n📧 测试邮件配置...")
    
    try:
        msg = MIMEText("这是青龙面板卡农论坛监控的测试邮件", 'plain', 'utf-8')
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"青龙面板测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        print("✅ 邮件发送测试成功")
        print(f"📬 测试邮件已发送到: {RECEIVER_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送测试失败: {e}")
        return False

def test_network_connectivity():
    """测试网络连接"""
    print("\n🌐 测试网络连接...")
    
    test_urls = [
        ("卡农论坛", "https://www.51kanong.com"),
        ("Gemini API", GEMINI_API_HOST),
        ("QQ邮箱", "https://mail.qq.com")
    ]
    
    all_success = True
    
    for name, url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name} 连接正常")
            else:
                print(f"⚠️ {name} 连接异常: HTTP {response.status_code}")
                all_success = False
        except Exception as e:
            print(f"❌ {name} 连接失败: {e}")
            all_success = False
    
    return all_success

def test_forum_access():
    """测试论坛访问"""
    print("\n🕷️ 测试论坛页面访问...")
    
    test_forum_urls = [
        "https://www.51kanong.com/yh-169-1.htm",  # 羊毛交流
        "https://www.51kanong.com/yh-282-1.htm",  # 羊毛专区
    ]
    
    for url in test_forum_urls:
        try:
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                if "卡农论坛" in response.text or "51kanong" in response.text:
                    print(f"✅ 论坛页面访问正常: {url}")
                else:
                    print(f"⚠️ 论坛页面内容异常: {url}")
            else:
                print(f"❌ 论坛页面访问失败: {url} (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"❌ 论坛页面访问异常: {url} ({e})")

def generate_test_report(results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📋 测试报告总结")
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
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！您的环境配置完全正常。")
        print("💡 可以开始使用青龙面板监控脚本了。")
    else:
        print("\n⚠️ 部分测试失败，请根据上述信息修复问题。")
        print("💡 建议先解决失败的测试项，再运行监控脚本。")

def main():
    """主测试函数"""
    print("🧪 青龙面板 - 卡农论坛监控配置测试")
    print("="*60)
    print("此脚本将测试您的环境配置是否正确")
    print("测试项目: Python环境、Playwright、Gemini API、邮件配置、网络连接")
    print("="*60)
    
    # 执行各项测试
    test_results = {}
    
    test_results["Python环境"] = test_python_environment()
    test_results["Playwright"] = test_playwright()
    test_results["Gemini API"] = test_gemini_api()
    test_results["邮件配置"] = test_email_config()
    test_results["网络连接"] = test_network_connectivity()
    
    # 额外测试
    test_forum_access()
    
    # 生成报告
    generate_test_report(test_results)
    
    print("\n" + "="*60)
    print("测试完成！")
    
    # 如果是在青龙面板环境中，提供额外信息
    try:
        import os
        if os.path.exists("/ql"):
            print("\n🐉 检测到青龙面板环境")
            print("📁 脚本目录: /ql/scripts")
            print("📋 建议定时规则: 0 */2 * * * (每2小时执行)")
            print("📧 邮件通知: 已配置为整合发送")
    except:
        pass

if __name__ == "__main__":
    main()
