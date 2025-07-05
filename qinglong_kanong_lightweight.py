#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
青龙面板 - 卡农论坛轻量级监控脚本
基于 HTTP 协议直接获取内容，大幅减少内存占用

特点:
1. 无需浏览器，内存占用仅 20-50MB
2. 基于 HTTP + BeautifulSoup 解析
3. 保持完整的 AI 分析和邮件功能
4. 适合资源受限的青龙面板环境
"""

import os
import sys
import json
import time
import smtplib
import requests
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

# 尝试导入 BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("⚠️ BeautifulSoup4 未安装，将使用正则表达式解析")

# ======================= 配置区 =======================

# 监控板块配置
FORUM_URLS = [
    {"name": "推荐热帖", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=225&filter=lastpost&orderby=lastpost"},
    {"name": "羊毛专区", "url": "https://www.51kanong.com/yh-282-1.htm"},
    {"name": "老哥生活", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=2603"},
    {"name": "数藏专区", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=15"},
    {"name": "下款线报", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=23"},
    {"name": "羊毛交流", "url": "https://www.51kanong.com/forum.php?mod=forumdisplay&fid=169&filter=lastpost&orderby=lastpost"},
]

# AI 分析配置
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
**正文**: {content}
---
"""

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = "2918627578@qq.com"
SENDER_PASSWORD = "djppyahldzyqdcdb"
RECEIVER_EMAIL = "txb528@163.com"

# 数据文件
SEEN_POSTS_FILE = os.path.join(os.path.dirname(__file__), 'seen_posts_51kanong.txt')

class LightweightKanongMonitor:
    """轻量级卡农论坛监控器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.seen_posts = self.load_seen_posts()
        
    def setup_session(self):
        """配置 HTTP 会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        # 设置超时
        self.session.timeout = 30
        
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
    
    def fetch_page(self, url: str) -> Optional[str]:
        """获取页面 HTML 内容"""
        try:
            print(f"📡 请求页面: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # 检查内容长度
            content_length = len(response.content)
            print(f"📄 响应大小: {content_length} 字节")

            # 尝试检测编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'

            html = response.text

            # 检查是否获取到正常内容
            if len(html) < 5000:
                print(f"⚠️ 页面内容较短: {len(html)} 字符")
                # 显示前200字符用于调试
                print(f"📄 内容预览: {html[:200]}")

            # 检查是否包含预期内容
            if '卡农' not in html and '51kanong' not in html and 'xyk-' not in html:
                print("⚠️ 页面可能被反爬虫拦截或内容异常")
                return None

            return html

        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败 {url}: {e}")
            return None
        except Exception as e:
            print(f"❌ 获取页面异常 {url}: {e}")
            return None
    
    def parse_time(self, time_str: str) -> Optional[datetime]:
        """智能解析时间字符串"""
        if not time_str:
            return None
            
        now = datetime.now()
        time_str = time_str.strip()
        
        # 处理相对时间
        if "分钟前" in time_str:
            match = re.search(r'(\d+)', time_str)
            if match:
                minutes = int(match.group(1))
                return now - timedelta(minutes=minutes)
        elif "小时前" in time_str:
            match = re.search(r'(\d+)', time_str)
            if match:
                hours = int(match.group(1))
                return now - timedelta(hours=hours)
        elif "昨天" in time_str:
            return now - timedelta(days=1)
        elif "前天" in time_str:
            return now - timedelta(days=2)
        
        # 处理绝对时间格式
        try:
            if re.match(r'\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{2}', time_str):
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            elif re.match(r'\d{1,2}-\d{1,2} \d{1,2}:\d{2}', time_str):
                current_year = now.year
                return datetime.strptime(f"{current_year}-{time_str}", '%Y-%m-%d %H:%M')
        except:
            pass
        
        return None
    
    def is_recent_post(self, post_time: Optional[datetime]) -> bool:
        """检查是否是最近24小时的帖子"""
        if not post_time:
            return True  # 如果没有时间信息，默认认为是最近的

        now = datetime.now()
        return (now - post_time).total_seconds() <= 24 * 3600
    
    def parse_post_list_bs4(self, html: str, board_name: str) -> List[Dict]:
        """使用 BeautifulSoup 解析帖子列表"""
        posts = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找帖子行
            post_rows = soup.select('tbody tr')
            
            for row in post_rows[:15]:  # 只处理前15个
                try:
                    # 查找标题链接
                    title_links = row.select('a[href*="thread"], a[href*="xyk-"]')
                    if not title_links:
                        continue
                    
                    title_link = title_links[0]
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href', '')
                    
                    if not url:
                        continue
                    
                    # 处理相对URL
                    if not url.startswith('http'):
                        url = urljoin('https://www.51kanong.com/', url)
                    
                    # 检查是否已处理
                    if url in self.seen_posts:
                        continue
                    
                    # 查找作者
                    author_links = row.select('a[href*="s-uid-"], a[href*="uid-"]')
                    author = author_links[0].get_text(strip=True) if author_links else "未知"
                    
                    # 查找时间
                    time_elements = row.select('em, span')
                    post_time = None
                    
                    for elem in time_elements:
                        text = elem.get_text(strip=True)
                        if any(keyword in text for keyword in ['分钟前', '小时前', '昨天', '2025', '2024']):
                            post_time = self.parse_time(text)
                            break
                    
                    # 暂时不过滤时间，获取所有帖子用于调试
                    posts.append({
                        'title': title,
                        'url': url,
                        'author': author,
                        'board': board_name,
                        'time': post_time.isoformat() if post_time else None,
                        'content': '',
                        'within_24h': True  # 暂时设为True
                    })
                        
                except Exception as e:
                    print(f"⚠️ 解析帖子行失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ BeautifulSoup 解析失败: {e}")
        
        return posts
    
    def parse_post_list_regex(self, html: str, board_name: str) -> List[Dict]:
        """使用正则表达式解析帖子列表（备用方案）"""
        posts = []

        try:
            # 调试信息（可选）
            print(f"🔍 HTML长度: {len(html)} 字符")

            # 多种帖子链接模式
            link_patterns = [
                r'<a[^>]*href="([^"]*(?:xyk-|thread-)[^"]*)"[^>]*>([^<]+)</a>',  # 原模式
                r'<a[^>]*href="([^"]*\.htm[^"]*)"[^>]*>([^<]+)</a>',  # .htm结尾
                r'<a[^>]*href="([^"]*\.html[^"]*)"[^>]*>([^<]+)</a>',  # .html结尾
                r'href="([^"]*(?:forum|thread|xyk)[^"]*)"[^>]*>([^<]+)<',  # 更宽泛的模式
            ]

            all_matches = []
            for pattern in link_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                all_matches.extend(matches)
                if len(matches) > 0:
                    print(f"🔍 匹配到 {len(matches)} 个链接")

            # 去重
            seen_urls = set()
            unique_matches = []
            for url, title in all_matches:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_matches.append((url, title))

            print(f"📋 总共发现 {len(unique_matches)} 个唯一链接")

            for url, title in unique_matches[:15]:  # 处理前15个
                # 过滤明显不是帖子的链接
                if any(skip in url.lower() for skip in ['javascript:', 'mailto:', '#', 'css', 'js']):
                    continue

                # 处理相对URL
                if not url.startswith('http'):
                    if url.startswith('/'):
                        url = f"https://www.51kanong.com{url}"
                    else:
                        url = f"https://www.51kanong.com/{url}"

                # 检查是否已处理
                if url in self.seen_posts:
                    continue

                # 清理标题
                title = re.sub(r'<[^>]+>', '', title).strip()
                if len(title) < 2 or len(title) > 100:  # 过滤异常标题
                    continue

                posts.append({
                    'title': title,
                    'url': url,
                    'author': "未知",
                    'board': board_name,
                    'time': None,
                    'content': '',
                    'within_24h': True  # 暂时不过滤时间
                })

                print(f"✅ 发现帖子: {title[:40]}...")

        except Exception as e:
            print(f"❌ 正则表达式解析失败: {e}")

        return posts
    
    def parse_post_content(self, html: str) -> str:
        """解析帖子内容 - 增强版，包含互动信息"""
        try:
            if BS4_AVAILABLE:
                return self.parse_content_with_bs4(html)
            else:
                return self.parse_content_with_regex(html)

        except Exception as e:
            print(f"⚠️ 解析帖子内容失败: {e}")

        return "内容提取失败"

    def parse_content_with_bs4(self, html: str) -> str:
        """使用BeautifulSoup解析完整内容"""
        soup = BeautifulSoup(html, 'html.parser')

        content_parts = []

        # 1. 获取主帖内容
        main_content = self.extract_main_content_bs4(soup)
        if main_content:
            content_parts.append(f"【主要内容】\n{main_content}")

        # 2. 获取回复内容（前几个有价值的回复）
        replies = self.extract_replies_bs4(soup)
        if replies:
            content_parts.append(f"【热门回复】\n{replies}")

        # 3. 获取统计信息
        stats = self.extract_post_stats_bs4(soup)
        if stats:
            content_parts.append(f"【互动统计】\n{stats}")

        return "\n\n".join(content_parts)[:1200]  # 限制总长度

    def extract_main_content_bs4(self, soup) -> str:
        """提取主帖内容"""
        content_selectors = [
            'td[id*="postmessage"]',
            '.t_msgfont',
            '.pcb',
            'div[class*="content"]'
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True)
                if len(content) > 20:
                    return content[:600]

        return ""

    def extract_replies_bs4(self, soup) -> str:
        """提取有价值的回复"""
        replies = []

        # 查找回复区域
        reply_selectors = [
            'table[id*="pid"] td[id*="postmessage"]',
            '.reply_content',
            '.post_content'
        ]

        for selector in reply_selectors:
            reply_elements = soup.select(selector)
            for elem in reply_elements[1:4]:  # 跳过主帖，取前3个回复
                reply_text = elem.get_text(strip=True)
                if len(reply_text) > 10 and len(reply_text) < 200:
                    replies.append(f"• {reply_text}")

        return "\n".join(replies[:3]) if replies else ""

    def extract_post_stats_bs4(self, soup) -> str:
        """提取帖子统计信息"""
        stats = []

        # 查找浏览量、回复数等
        stat_patterns = [
            ('浏览', r'浏览.*?(\d+)'),
            ('回复', r'回复.*?(\d+)'),
            ('点赞', r'点赞.*?(\d+)'),
        ]

        page_text = soup.get_text()
        for stat_name, pattern in stat_patterns:
            match = re.search(pattern, page_text)
            if match:
                stats.append(f"{stat_name}: {match.group(1)}")

        return " | ".join(stats) if stats else ""

    def parse_content_with_regex(self, html: str) -> str:
        """使用正则表达式解析完整内容"""
        content_parts = []

        # 1. 主帖内容
        main_content = self.extract_main_content_regex(html)
        if main_content:
            content_parts.append(f"【主要内容】\n{main_content}")

        # 2. 回复内容
        replies = self.extract_replies_regex(html)
        if replies:
            content_parts.append(f"【热门回复】\n{replies}")

        # 3. 统计信息
        stats = self.extract_post_stats_regex(html)
        if stats:
            content_parts.append(f"【互动统计】\n{stats}")

        return "\n\n".join(content_parts)[:1200]

    def extract_main_content_regex(self, html: str) -> str:
        """正则表达式提取主帖内容"""
        content_patterns = [
            r'<td[^>]*id="postmessage[^"]*"[^>]*>(.*?)</td>',
            r'<div[^>]*class="t_msgfont"[^>]*>(.*?)</div>',
            r'<div[^>]*class="pcb"[^>]*>(.*?)</div>'
        ]

        for pattern in content_patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                content = re.sub(r'<[^>]+>', '', match.group(1))
                content = re.sub(r'\s+', ' ', content).strip()
                if len(content) > 20:
                    return content[:600]

        return ""

    def extract_replies_regex(self, html: str) -> str:
        """正则表达式提取回复内容"""
        # 查找所有postmessage区域，跳过第一个（主帖）
        pattern = r'<td[^>]*id="postmessage[^"]*"[^>]*>(.*?)</td>'
        matches = re.findall(pattern, html, re.DOTALL)

        replies = []
        for match in matches[1:4]:  # 跳过主帖，取前3个回复
            reply_text = re.sub(r'<[^>]+>', '', match)
            reply_text = re.sub(r'\s+', ' ', reply_text).strip()
            if 10 < len(reply_text) < 200:
                replies.append(f"• {reply_text}")

        return "\n".join(replies) if replies else ""

    def extract_post_stats_regex(self, html: str) -> str:
        """正则表达式提取统计信息"""
        stats = []

        # 查找常见的统计信息
        stat_patterns = [
            ('浏览', r'浏览[^\d]*(\d+)'),
            ('回复', r'回复[^\d]*(\d+)'),
            ('查看', r'查看[^\d]*(\d+)'),
        ]

        for stat_name, pattern in stat_patterns:
            match = re.search(pattern, html)
            if match:
                stats.append(f"{stat_name}: {match.group(1)}")

        return " | ".join(stats) if stats else ""

    def analyze_with_ai(self, post: Dict) -> str:
        """使用 AI 分析帖子 - 优化版本"""
        try:
            # 简化的分析逻辑，避免网络超时
            title = post.get('title', '')
            content = post.get('content', '')

            # 如果内容太短，直接返回简单分析
            if len(content) < 10:
                return self.simple_analysis(title, content)

            # 检查网络连接
            if not self.test_ai_connection():
                print("⚠️ AI服务连接异常，使用简单分析")
                return self.simple_analysis(title, content)

            # 简化的提示词，减少token使用
            prompt = f"""请简要分析这个论坛帖子的价值：

标题：{title}
内容：{content[:200]}

请用一句话回答：
1. 核心价值是什么？
2. 评分(0-10分)？
3. 建议？"""

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
                    "temperature": 0.5,
                    "maxOutputTokens": 200,  # 大幅减少
                }
            }

            # 短超时时间，快速失败
            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    ai_content = result['candidates'][0]['content']['parts'][0]['text']
                    print("✅ AI分析成功")
                    return f"**AI分析**: {ai_content.strip()}"
            else:
                print(f"⚠️ AI API错误: {response.status_code}")

        except requests.exceptions.Timeout:
            print("⚠️ AI请求超时，使用简单分析")
        except requests.exceptions.ConnectionError:
            print("⚠️ AI连接失败，使用简单分析")
        except Exception as e:
            print(f"⚠️ AI分析异常: {str(e)[:50]}")

        # 如果AI分析失败，使用简单分析
        return self.simple_analysis(title, content)

    def test_ai_connection(self) -> bool:
        """快速测试AI连接"""
        try:
            # 非常快速的连接测试
            response = requests.get(f"{GEMINI_API_HOST}/", timeout=3)
            return True
        except:
            return False

    def simple_analysis(self, title: str, content: str) -> str:
        """简单的本地分析，当AI不可用时使用"""
        try:
            # 基于关键词的简单分析
            high_value_keywords = ['下款', '通过', '额度', '成功', '到账', '放款', '审核']
            medium_value_keywords = ['申请', '试试', '活动', '优惠', '福利', '红包']
            low_value_keywords = ['失败', '拒绝', '没有', '不行', '问题']

            text = (title + ' ' + content).lower()

            high_count = sum(1 for kw in high_value_keywords if kw in text)
            medium_count = sum(1 for kw in medium_value_keywords if kw in text)
            low_count = sum(1 for kw in low_value_keywords if kw in text)

            if high_count >= 2:
                score = 8
                value = "高价值下款/成功案例"
                suggestion = "建议关注"
            elif high_count >= 1:
                score = 6
                value = "可能的下款机会"
                suggestion = "可以尝试"
            elif medium_count >= 2:
                score = 4
                value = "一般活动信息"
                suggestion = "酌情参与"
            elif low_count >= 1:
                score = 2
                value = "负面信息或失败案例"
                suggestion = "谨慎对待"
            else:
                score = 3
                value = "普通讨论内容"
                suggestion = "了解即可"

            return f"""**本地分析**:
• 核心价值: {value}
• 价值评分: {score}/10
• 建议: {suggestion}"""

        except Exception as e:
            return f"**简单分析**: 标题包含关键信息，建议查看原帖"

    def scrape_board(self, board_name: str, board_url: str) -> List[Dict]:
        """抓取单个板块"""
        print(f"\n🎯 开始抓取板块: {board_name}")

        # 获取板块页面
        html = self.fetch_page(board_url)
        if not html:
            print(f"❌ 获取板块页面失败: {board_name}")
            return []

        # 解析帖子列表
        if BS4_AVAILABLE:
            posts = self.parse_post_list_bs4(html, board_name)
        else:
            posts = self.parse_post_list_regex(html, board_name)

        print(f"📋 发现 {len(posts)} 个最近帖子")

        # 获取帖子详细内容
        detailed_posts = []
        for post in posts[:5]:  # 只处理前5个帖子
            print(f"📖 获取帖子内容: {post['title'][:30]}...")

            content_html = self.fetch_page(post['url'])
            if content_html:
                post['content'] = self.parse_post_content(content_html)

                # AI 分析
                if post['content'] and len(post['content']) > 20:
                    analysis = self.analyze_with_ai(post)
                    post['ai_analysis'] = analysis
                else:
                    post['ai_analysis'] = "内容过短，无法分析"

                detailed_posts.append(post)
                self.seen_posts.add(post['url'])

                # 请求间隔
                time.sleep(2)
            else:
                print(f"⚠️ 获取帖子内容失败: {post['url']}")

        print(f"✅ {board_name} 完成，处理了 {len(detailed_posts)} 个帖子")
        return detailed_posts

    def send_integrated_email(self, posts: List[Dict]):
        """发送整合邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECEIVER_EMAIL
            msg['Subject'] = f"卡农论坛监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # 构建邮件内容
            email_content = f"""
# 🕷️ 卡农论坛监控报告 (轻量级版本)

**监控时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**发现新帖**: {len(posts)} 个
**运行模式**: HTTP协议直接获取 (内存占用 < 50MB)

---

"""

            for i, post in enumerate(posts, 1):
                email_content += f"""
## 📝 帖子 {i}: {post['title']}

**板块**: {post['board']}
**作者**: {post['author']}
**时间**: {post['time'] or '未知'}
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
- 内存占用: < 50MB (轻量级版本)
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*此邮件由青龙面板轻量级监控脚本自动发送*
"""

            msg.attach(MIMEText(email_content, 'plain', 'utf-8'))

            # 发送邮件
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            print("📧 整合邮件发送成功")

        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")

    def run_monitoring(self):
        """执行监控任务"""
        print("🕷️ 青龙面板 - 卡农论坛轻量级监控启动")
        print("=" * 60)
        print(f"💾 内存模式: 轻量级 (预计占用 < 50MB)")
        print(f"🔧 解析引擎: {'BeautifulSoup4' if BS4_AVAILABLE else '正则表达式'}")
        print("=" * 60)

        all_new_posts = []

        for forum in FORUM_URLS:
            board_name = forum['name']
            board_url = forum['url']

            try:
                posts = self.scrape_board(board_name, board_url)
                all_new_posts.extend(posts)

                # 板块间延迟
                time.sleep(3)

            except Exception as e:
                print(f"❌ 抓取板块 {board_name} 异常: {e}")

        # 发送邮件和保存数据
        if all_new_posts:
            self.send_integrated_email(all_new_posts)
            self.save_seen_posts()
            print(f"\n✅ 监控完成，发现 {len(all_new_posts)} 个新帖子")
        else:
            print("\nℹ️ 没有发现新帖子")

        print("=" * 60)

def main():
    """主函数"""
    # 检查依赖
    if not BS4_AVAILABLE:
        print("⚠️ 建议安装 BeautifulSoup4 以获得更好的解析效果:")
        print("💡 pip install beautifulsoup4 lxml")
        print("🔄 当前使用正则表达式解析模式\n")

    # 创建监控器并运行
    monitor = LightweightKanongMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()
