#!/bin/bash

# 青龙面板 - 卡农论坛监控脚本安装器
# 自动安装依赖并配置监控任务

echo "🚀 青龙面板 - 卡农论坛监控脚本安装器"
echo "=================================================="

# 检查是否在青龙面板环境中
if [ ! -d "/ql" ]; then
    echo "⚠️ 警告: 未检测到青龙面板环境"
    echo "💡 如果您确定在青龙面板中，请忽略此警告"
fi

# 设置脚本目录
SCRIPT_DIR="/ql/scripts"
if [ ! -d "$SCRIPT_DIR" ]; then
    SCRIPT_DIR="$(pwd)"
    echo "📁 使用当前目录: $SCRIPT_DIR"
else
    echo "📁 使用青龙脚本目录: $SCRIPT_DIR"
fi

echo ""
echo "🔧 开始安装依赖..."

# 更新 pip
echo "📦 更新 pip..."
python3 -m pip install --upgrade pip

# 安装基础依赖
echo "📦 安装基础依赖..."
pip3 install requests asyncio

# 安装 Playwright
echo "📦 安装 Playwright..."
pip3 install playwright

# 安装浏览器
echo "🌐 安装 Chromium 浏览器..."
playwright install chromium

# 检查安装结果
echo ""
echo "🔍 检查安装结果..."

# 检查 Python 模块
python3 -c "import requests; print('✅ requests 安装成功')" 2>/dev/null || echo "❌ requests 安装失败"
python3 -c "import asyncio; print('✅ asyncio 可用')" 2>/dev/null || echo "❌ asyncio 不可用"
python3 -c "from playwright.async_api import async_playwright; print('✅ playwright 安装成功')" 2>/dev/null || echo "❌ playwright 安装失败"

# 检查浏览器
if [ -d "$HOME/.cache/ms-playwright/chromium-*" ] || [ -d "/root/.cache/ms-playwright/chromium-*" ]; then
    echo "✅ Chromium 浏览器安装成功"
else
    echo "❌ Chromium 浏览器安装失败"
fi

echo ""
echo "📋 创建监控脚本..."

# 复制脚本到目标目录
if [ -f "qinglong_kanong_monitor.py" ]; then
    cp qinglong_kanong_monitor.py "$SCRIPT_DIR/"
    chmod +x "$SCRIPT_DIR/qinglong_kanong_monitor.py"
    echo "✅ 监控脚本已复制到: $SCRIPT_DIR/qinglong_kanong_monitor.py"
else
    echo "❌ 未找到 qinglong_kanong_monitor.py 文件"
fi

echo ""
echo "⚙️ 配置说明:"
echo "1. 脚本位置: $SCRIPT_DIR/qinglong_kanong_monitor.py"
echo "2. 在青龙面板中添加定时任务:"
echo "   - 名称: 卡农论坛监控"
echo "   - 命令: python3 $SCRIPT_DIR/qinglong_kanong_monitor.py"
echo "   - 定时规则: 0 */2 * * * (每2小时执行一次)"
echo ""
echo "3. 环境变量配置 (可选):"
echo "   - KANONG_API_KEY: Gemini API Key"
echo "   - KANONG_EMAIL: 接收邮箱"
echo "   - KANONG_HEADLESS: 是否无头模式 (true/false)"

echo ""
echo "🧪 测试运行..."
cd "$SCRIPT_DIR"
python3 qinglong_kanong_monitor.py &
TEST_PID=$!
sleep 10
kill $TEST_PID 2>/dev/null

echo ""
echo "✅ 安装完成!"
echo "=================================================="
echo "📝 下一步操作:"
echo "1. 在青龙面板中添加定时任务"
echo "2. 设置合适的执行频率 (建议每2-4小时)"
echo "3. 查看日志确认运行正常"
echo ""
echo "🔗 相关文件:"
echo "- 主脚本: $SCRIPT_DIR/qinglong_kanong_monitor.py"
echo "- 已处理帖子记录: $SCRIPT_DIR/seen_posts_51kanong.txt"
echo ""
echo "📧 邮件配置已使用您提供的设置:"
echo "- 发送邮箱: 2918627578@qq.com"
echo "- 接收邮箱: txb528@163.com"
echo "- SMTP服务器: smtp.qq.com:465"
echo ""
echo "🎉 享受自动化监控吧!"
