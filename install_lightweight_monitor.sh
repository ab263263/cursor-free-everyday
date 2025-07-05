#!/bin/bash

# 青龙面板 - 卡农论坛轻量级监控安装器
# 专为资源受限环境设计，无需浏览器，内存占用 < 50MB

echo "🚀 青龙面板 - 卡农论坛轻量级监控安装器"
echo "=================================================="
echo "💾 轻量级版本特点:"
echo "  🔹 无需浏览器，内存占用 < 50MB"
echo "  🔹 基于 HTTP 协议直接获取"
echo "  🔹 适合资源受限的青龙面板环境"
echo "=================================================="

# 检查青龙面板环境
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
echo "🔧 开始安装轻量级依赖..."

# 更新 pip
echo "📦 更新 pip..."
python3 -m pip install --upgrade pip

# 安装基础依赖
echo "📦 安装基础依赖..."
pip3 install requests

# 安装 HTML 解析库 (可选但推荐)
echo "📦 安装 HTML 解析库..."
pip3 install beautifulsoup4 lxml

echo ""
echo "🔍 检查安装结果..."

# 检查 Python 模块
python3 -c "import requests; print('✅ requests 安装成功')" 2>/dev/null || echo "❌ requests 安装失败"

# 检查 BeautifulSoup (可选)
python3 -c "from bs4 import BeautifulSoup; print('✅ BeautifulSoup4 安装成功')" 2>/dev/null || echo "⚠️ BeautifulSoup4 未安装，将使用正则表达式解析"

# 检查内置模块
python3 -c "import json, smtplib, re, datetime; print('✅ 内置模块正常')" 2>/dev/null || echo "❌ 内置模块异常"

echo ""
echo "📋 部署监控脚本..."

# 复制脚本到目标目录
if [ -f "qinglong_kanong_lightweight.py" ]; then
    cp qinglong_kanong_lightweight.py "$SCRIPT_DIR/"
    chmod +x "$SCRIPT_DIR/qinglong_kanong_lightweight.py"
    echo "✅ 轻量级监控脚本已部署: $SCRIPT_DIR/qinglong_kanong_lightweight.py"
else
    echo "❌ 未找到 qinglong_kanong_lightweight.py 文件"
fi

# 复制测试脚本
if [ -f "test_lightweight_config.py" ]; then
    cp test_lightweight_config.py "$SCRIPT_DIR/"
    chmod +x "$SCRIPT_DIR/test_lightweight_config.py"
    echo "✅ 测试脚本已部署: $SCRIPT_DIR/test_lightweight_config.py"
fi

echo ""
echo "⚙️ 青龙面板配置说明:"
echo "1. 脚本位置: $SCRIPT_DIR/qinglong_kanong_lightweight.py"
echo "2. 在青龙面板中添加定时任务:"
echo "   - 名称: 卡农论坛轻量级监控"
echo "   - 命令: python3 $SCRIPT_DIR/qinglong_kanong_lightweight.py"
echo "   - 定时规则: 0 */2 * * * (每2小时执行一次)"
echo ""
echo "3. 轻量级版本优势:"
echo "   - 内存占用: < 50MB (vs 浏览器版本 200-400MB)"
echo "   - 启动速度: 快 5-10 倍"
echo "   - 依赖简单: 仅需 requests + beautifulsoup4"
echo "   - 稳定性高: 无浏览器崩溃风险"

echo ""
echo "🧪 运行配置测试..."
cd "$SCRIPT_DIR"

if [ -f "test_lightweight_config.py" ]; then
    echo "正在运行配置测试..."
    python3 test_lightweight_config.py
else
    echo "⚠️ 测试脚本不存在，跳过自动测试"
fi

echo ""
echo "✅ 轻量级版本安装完成!"
echo "=================================================="
echo "📝 下一步操作:"
echo "1. 在青龙面板中添加定时任务"
echo "2. 设置执行频率 (建议每2-4小时)"
echo "3. 查看日志确认运行正常"
echo ""
echo "🔗 相关文件:"
echo "- 主脚本: $SCRIPT_DIR/qinglong_kanong_lightweight.py"
echo "- 测试脚本: $SCRIPT_DIR/test_lightweight_config.py"
echo "- 数据文件: $SCRIPT_DIR/seen_posts_51kanong.txt"
echo ""
echo "💾 内存对比:"
echo "- 浏览器版本: 200-400MB"
echo "- 轻量级版本: 20-50MB"
echo "- 节省内存: 80-90%"
echo ""
echo "📧 邮件配置:"
echo "- 发送邮箱: 2918627578@qq.com"
echo "- 接收邮箱: txb528@163.com"
echo "- 通知方式: 整合邮件 (避免刷屏)"
echo ""
echo "🎉 享受轻量级自动化监控吧!"
