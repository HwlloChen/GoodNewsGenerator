#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
喜报/悲报生成器 Langbot插件
用于在Langbot中响应"喜报 xxx"或"悲报 xxx"关键词，生成并发送对应风格的图片
"""

import os
import re
import tempfile
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类
from pkg.platform.types import *

# 导入生成器模块
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from generator import NewsGenerator

@register(name="GoodNewsGenerator", 
          description="喜报/悲报生成器插件，根据关键词生成并发送喜报或悲报图片", 
          version="0.1.0", 
          author="HwlloChen")

class GoodNewsGenerator(BasePlugin):
    """喜报/悲报生成器插件类"""
    
    def __init__(self, host: APIHost):
        """
        初始化插件
        
        Args:
            host: API主机对象
        """
        # 插件加载时触发
        self.ap = host
        self.generator = None
        
        # 临时目录，用于存储生成的图片
        self.temp_dir = tempfile.mkdtemp()
        print(f"临时目录创建: {self.temp_dir}")
        
        # 正则表达式，用于匹配"喜报 xxx"或"悲报 xxx"格式的消息
        self.good_news_pattern = re.compile(r'^喜报\s+(.+)$')
        self.bad_news_pattern = re.compile(r'^悲报\s+(.+)$')
    
    async def initialize(self):
        """异步初始化"""
        # 初始化生成器
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            assets_dir = os.path.join(current_dir, 'assets')
            self.generator = NewsGenerator(assets_dir=assets_dir)
            print("生成器初始化成功")
        except Exception as e:
            print(f"生成器初始化失败: {e}")
    
    @handler(PersonMessageReceived)
    @handler(GroupMessageReceived)
    async def message_received(self, ctx: EventContext):
        """
        处理私聊消息
        
        Args:
            ctx: 事件上下文
        """
        msg = str(ctx.event.message_chain).strip()
        # 尝试匹配喜报格式
        good_match = self.good_news_pattern.match(msg)
        if good_match:
            content = good_match.group(1)
            print(f"匹配到喜报内容: {content}")
            await self._generate_and_send_image(ctx, content, "good")
            return
        # 尝试匹配悲报格式
        bad_match = self.bad_news_pattern.match(msg)
        if bad_match:
            content = bad_match.group(1)
            print(f"匹配到悲报内容: {content}")
            await self._generate_and_send_image(ctx, content, "bad")
            return
    
    async def _generate_and_send_image(self, ctx: EventContext, content: str, news_type: str):
        """
        生成并发送图片
        
        Args:
            ctx: 事件上下文
            content: 图片内容
            news_type: 图片类型，'good'表示喜报，'bad'表示悲报
        """
        if not self.generator:
            print("生成器未初始化")
            await ctx.send_message(
                ctx.event.launcher_type,
                str(ctx.event.launcher_id),
                "生成器初始化失败，无法生成图片"
            )
            return
        try:
            # 生成图片
            output_path = os.path.join(self.temp_dir, f"{news_type}_{ctx.event.launcher_id}.jpg")
            self.generator.generate(content, news_type=news_type, output_path=output_path)
            # 构建消息链并发送图片
            message_chain = [Image(path=output_path)]
            await ctx.send_message(
                ctx.event.launcher_type,
                str(ctx.event.launcher_id),
                message_chain
            )
            ctx.prevent_default()
        except Exception as e:
            print(f"生成或发送图片失败: {e}")
            error_message = f"生成图片失败: {str(e)}"
            await ctx.send_message(
                ctx.event.launcher_type,
                str(ctx.event.launcher_id),
                error_message
            )
    
    def __del__(self):
        """插件卸载时触发"""
        # 清理临时目录
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"临时目录已清理: {self.temp_dir}")
        except Exception as e:
            print(f"清理临时目录失败: {e}")
