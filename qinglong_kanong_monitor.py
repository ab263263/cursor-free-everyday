#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
青龙面板 - 卡农论坛监控脚本
适配青龙面板环境，整合浏览器自动化 + AI分析 + 邮件通知

功能特点:
1. 浏览器自动化抓取论坛最新帖子
2. AI智能分析帖子价值
3. 整合所有分析结果发送一封邮件
4. 数据持久化避免重复处理
5. 适配青龙面板运行环境
"""

import os
import sys
import json
import time
import smtplib
import requests
import asyncio
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from pathlib import Path

# 尝试导入 playwright，如果失败则提示安装
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright 未安装，将使用简化模式")

# ======================= 1. 用户配置区 =======================

# --- 爬虫配置 ---
FORUM_URLS = [
    {"name": "推荐热帖", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=225&filter=lastpost&orderby=lastpost"},
    {"name": "羊毛专区", "url": "https://www.51kanong.com/yh-282-1.htm"},
    {"name": "老哥生活", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=2603"},
    {"name": "数藏专区", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=15"},
    {"name": "下款线报", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=23"},
    {"name": "羊毛交流", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=169&filter=lastpost&orderby=lastpost"},
]

# --- 论坛登录配置 ---
FORUM_USERNAME = ""
FORUM_PASSWORD = ""

# --- 浏览器配置 ---
HEADLESS_MODE = True
PAGE_LOAD_WAIT = 5
ENABLE_CACHE = True

# --- AI 分析配置 ---
GEMINI_API_HOST = "https://generativelanguage.googleapis.com"
GEMINI_API_KEY = "AIzaSyBAapmvw5zq9s3ro2EjGH4NgY0BNhAODgw"

AI_PROMPT_TEMPLATE = """
作为一名专业的论坛"羊毛"价值分析师，请你严格、客观地分析以下论坛帖子的内容，并以清晰、简洁、有条理的方式输出。

**分析要求:**
1.  **核心价值判断**: 一句话精准总结这个帖子的核心价值是什么？
2.  **关键信息提取**:
    *   **活动/福利**: 如果是活动或福利，说明具体是什么？
    *   **参与方式**: 如何参与这个活动？
    *   **限制条件**: 有什么限制？
3.  **价值评分**: 从0到10分，给这个帖子的价值打分，并简单说明理由。
4.  **总结建议**: 根据以上分析，给用户一个明确的、可执行的建议。

**输出格式:**
请严格按照以下Markdown格式返回：

```markdown
**AI分析报告**

*   **核心价值**: 
*   **关键信息**:
    *   **福利详情**: 
    *   **参与路径**: 
    *   **限制条件**: 
*   **价值评分**: 
*   **总结建议**: 
```

**原始帖子内容:**
---
**标题**: {title}

**正文**: 
{content}
---
"""

# --- 邮件通知配置 ---
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = "2918627578@qq.com"
SENDER_PASSWORD = "djppyahldzyqdcdb"
RECEIVER_EMAIL = "txb528@163.com"

# --- 数据持久化文件 ---
SEEN_POSTS_FILE = os.path.join(os.path.dirname(__file__), 'seen_posts_51kanong.txt')

class QinglongKanongMonitor:
    """青龙面板卡农论坛监控器"""
    
    def __init__(self):
        self.seen_posts = self.load_seen_posts()
        self.new_posts = []
        self.analysis_results = []
        
    def load_seen_posts(self) -> set:
        """加载已处理的帖子URL"""
        if os.path.exists(SEEN_POSTS_FILE):
            try:
                with open(SEEN_POSTS_FILE, 'r', encoding='utf-8') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                print(f"⚠️ 加载已处理帖子列表失败: {e}")
        return set()
    
    def save_seen_posts(self):
        """保存已处理的帖子URL"""
        try:
            with open(SEEN_POSTS_FILE, 'w', encoding='utf-8') as f:
                for url in self.seen_posts:
                    f.write(f"{url}\n")
        except Exception as e:
            print(f"⚠️ 保存已处理帖子列表失败: {e}")
    
    async def scrape_with_playwright(self, board_url: str, board_name: str) -> List[Dict]:
        """使用 Playwright 抓取帖子"""
        if not PLAYWRIGHT_AVAILABLE:
            return []
        
        posts = []
        playwright = None
        browser = None
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=HEADLESS_MODE,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            page = await browser.new_page()
            await page.goto(board_url, timeout=30000)
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # 提取帖子列表
            post_rows = await page.query_selector_all('tbody tr')
            
            for row in post_rows[:10]:  # 只处理前10个帖子
                try:
                    title_link = await row.query_selector('a[href*="thread"], a[href*="xyk-"]')
                    if not title_link:
                        continue
                    
                    title = await title_link.inner_text()
                    url = await title_link.get_attribute('href')
                    
                    if url and not url.startswith('http'):
                        url = f"https://www.51kanong.com/{url}"
                    
                    # 检查是否已处理过
                    if url in self.seen_posts:
                        continue
                    
                    # 提取时间信息
                    time_elements = await row.query_selector_all('em, span')
                    post_time = None
                    
                    for elem in time_elements:
                        text = await elem.inner_text()
                        if any(keyword in text for keyword in ['分钟前', '小时前', '昨天', '2025']):
                            post_time = text
                            break
                    
                    # 检查是否是最近的帖子
                    if self.is_recent_post(post_time):
                        posts.append({
                            'title': title.strip(),
                            'url': url,
                            'board': board_name,
                            'time': post_time,
                            'content': ''
                        })
                        
                except Exception as e:
                    print(f"⚠️ 提取帖子信息失败: {e}")
                    continue
            
            # 提取帖子内容
            for post in posts[:5]:  # 只提取前5个帖子的详细内容
                try:
                    await page.goto(post['url'], timeout=30000)
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    
                    content_elem = await page.query_selector('td[id*="postmessage"], .t_msgfont, .pcb')
                    if content_elem:
                        content = await content_elem.inner_text()
                        post['content'] = content.strip()[:500]  # 限制长度
                    
                    await asyncio.sleep(2)  # 避免请求过快
                    
                except Exception as e:
                    print(f"⚠️ 提取帖子内容失败 {post['url']}: {e}")
                    post['content'] = "内容提取失败"
        
        except Exception as e:
            print(f"❌ 浏览器抓取失败 {board_name}: {e}")
        
        finally:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
        
        return posts
    
    def is_recent_post(self, time_str: str) -> bool:
        """判断是否是最近的帖子"""
        if not time_str:
            return False
        
        # 简单的时间判断逻辑
        recent_keywords = ['分钟前', '小时前', '昨天']
        return any(keyword in time_str for keyword in recent_keywords)
    
    def analyze_with_ai(self, post: Dict) -> str:
        """使用 AI 分析帖子"""
        try:
            prompt = AI_PROMPT_TEMPLATE.format(
                title=post['title'],
                content=post['content']
            )

            # 更新为正确的 Gemini API 端点
            url = f"{GEMINI_API_HOST}/v1beta/models/gemini-1.5-flash:generateContent"
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': GEMINI_API_KEY
            }

            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content.strip()
            else:
                print(f"AI API 错误: {response.status_code} - {response.text}")

            return f"AI分析失败: HTTP {response.status_code}"

        except Exception as e:
            return f"AI分析异常: {str(e)}"
    
    async def monitor_forums(self):
        """监控所有论坛板块"""
        print("🕷️ 开始监控卡农论坛...")
        
        all_new_posts = []
        
        for forum in FORUM_URLS:
            board_name = forum['name']
            board_url = forum['url']
            
            print(f"📋 正在抓取: {board_name}")
            
            try:
                posts = await self.scrape_with_playwright(board_url, board_name)
                
                for post in posts:
                    if post['url'] not in self.seen_posts:
                        print(f"📝 发现新帖: {post['title'][:30]}...")
                        
                        # AI 分析
                        if post['content']:
                            analysis = self.analyze_with_ai(post)
                            post['ai_analysis'] = analysis
                        else:
                            post['ai_analysis'] = "内容为空，无法分析"
                        
                        all_new_posts.append(post)
                        self.seen_posts.add(post['url'])
                        
                        # 避免API请求过快
                        await asyncio.sleep(3)
                
                # 板块间延迟
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"❌ 抓取板块 {board_name} 失败: {e}")
        
        # 发送整合邮件
        if all_new_posts:
            self.send_integrated_email(all_new_posts)
            self.save_seen_posts()
            print(f"✅ 处理完成，发现 {len(all_new_posts)} 个新帖子")
        else:
            print("ℹ️ 没有发现新帖子")
    
    def send_integrated_email(self, posts: List[Dict]):
        """发送整合的邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECEIVER_EMAIL
            msg['Subject'] = f"卡农论坛监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 构建邮件内容
            email_content = f"""
# 🕷️ 卡农论坛监控报告

**监控时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**发现新帖**: {len(posts)} 个

---

"""
            
            for i, post in enumerate(posts, 1):
                email_content += f"""
## 📝 帖子 {i}: {post['title']}

**板块**: {post['board']}
**时间**: {post['time']}
**链接**: {post['url']}

**内容预览**:
{post['content'][:200]}...

**AI 分析结果**:
{post['ai_analysis']}

---

"""
            
            email_content += f"""
**统计信息**:
- 总计新帖: {len(posts)} 个
- 监控板块: {len(FORUM_URLS)} 个
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*此邮件由青龙面板自动发送*
"""
            
            msg.attach(MIMEText(email_content, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            
            print("📧 整合邮件发送成功")
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")

async def main():
    """主函数"""
    print("🚀 青龙面板 - 卡农论坛监控启动")
    print("=" * 50)
    
    # 检查环境
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️ 警告: Playwright 未安装，功能受限")
        print("💡 安装命令: pip install playwright && playwright install chromium")
        return
    
    if not GEMINI_API_KEY:
        print("❌ 错误: 未配置 Gemini API Key")
        return
    
    # 创建监控器并运行
    monitor = QinglongKanongMonitor()
    await monitor.monitor_forums()
    
    print("✅ 监控任务完成")

if __name__ == "__main__":
    asyncio.run(main())
