#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
喜报/悲报生成器
用于生成喜报或悲报风格的图片，支持自定义文本内容和样式
"""

import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Dict, Optional, Literal

class NewsGenerator:
    """喜报/悲报生成器类"""
    
    def __init__(self, assets_dir: str = None):
        """
        初始化生成器
        
        Args:
            assets_dir: 素材目录路径，默认为当前文件所在目录下的assets
        """
        # 设置素材目录
        if assets_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.assets_dir = os.path.join(current_dir, 'assets')
        else:
            self.assets_dir = assets_dir
            
        # 模板配置
        self.templates = {
            'good': {
                'image': os.path.join(self.assets_dir, 'good_news.jpg'),
                'font_color': (220, 48, 35),  # 红色
                'stroke_color': (170, 0, 0),  # 深红色
                'stroke_width': 0
            },
            'bad': {
                'image': os.path.join(self.assets_dir, 'bad_news.jpg'),
                'font_color': (90, 90, 90),  # 灰色
                'stroke_color': (89, 88, 87),      # 黑色
                'stroke_width': 0
            }
        }
        
        # 默认字体设置
        self.default_font_path = os.path.join(self.assets_dir, 'font.ttf')
        
    def _get_font(self, size: int, font_path: str = None) -> ImageFont.FreeTypeFont:
        """
        获取字体对象
        
        Args:
            size: 字体大小
            font_path: 字体文件路径，默认使用黑体
            
        Returns:
            字体对象
        """
        if font_path is None:
            font_path = self.default_font_path
            
        try:
            return ImageFont.truetype(font_path, size)
        except IOError:
            # 如果找不到指定字体，尝试使用系统默认字体
            try:
                # 尝试使用系统默认字体
                return ImageFont.load_default()
            except:
                raise Exception("无法加载字体文件")
    
    def _calculate_font_size(self, text: str, max_width: int, max_height: int, 
                            initial_font_size: int = 100, 
                            min_font_size: int = 20,
                            font_path: str = None) -> Tuple[int, int]:
        """
        计算适合的字体大小和行数
        
        Args:
            text: 要显示的文本
            max_width: 最大宽度
            max_height: 最大高度
            initial_font_size: 初始字体大小
            min_font_size: 最小字体大小
            font_path: 字体文件路径
            
        Returns:
            (字体大小, 每行字符数)
        """
        font_size = initial_font_size
        chars_per_line = len(text)
        
        while font_size >= min_font_size:
            font = self._get_font(font_size, font_path)
            
            # 尝试不同的每行字符数
            for cpl in range(len(text), 0, -1):
                lines = textwrap.wrap(text, width=cpl)
                
                # 计算文本总宽度和高度
                max_line_width = 0
                for line in lines:
                    line_width = font.getlength(line)
                    max_line_width = max(max_line_width, line_width)
                
                text_height = len(lines) * font_size * 1.5  # 1.5为行间距系数
                
                # 如果文本能够适应指定区域，返回当前字体大小和每行字符数
                if max_line_width <= max_width and text_height <= max_height:
                    return font_size, cpl
            
            # 如果当前字体大小下无法适应，减小字体大小
            font_size -= 5
        
        # 如果无法找到合适的字体大小，返回最小字体大小和尽可能多的每行字符数
        return min_font_size, max(1, len(text) // ((max_height // (min_font_size * 1.5)) or 1))
    
    def generate(self, 
                text: str, 
                news_type: Literal['good', 'bad'] = 'good',
                output_path: str = None,
                font_path: str = None) -> Image.Image:
        """
        生成喜报/悲报图片
        
        Args:
            text: 要显示的文本内容
            news_type: 图片类型，'good'表示喜报，'bad'表示悲报
            output_path: 输出文件路径，如果为None则不保存文件
            font_path: 字体文件路径，默认使用内置字体
            
        Returns:
            生成的图片对象
        """
        # 获取模板配置
        template = self.templates.get(news_type)
        if not template:
            raise ValueError(f"不支持的图片类型: {news_type}")
        
        # 打开背景图片
        try:
            img = Image.open(template['image'])
        except Exception as e:
            raise Exception(f"无法打开背景图片: {e}")
        
        # 创建绘图对象
        draw = ImageDraw.Draw(img)
        
        # 计算文本区域大小（图片宽度的80%，高度的60%）
        img_width, img_height = img.size
        text_max_width = int(img_width * 0.8)
        text_max_height = int(img_height * 0.6)
        
        # 计算合适的字体大小和每行字符数
        font_size, chars_per_line = self._calculate_font_size(
            text, text_max_width, text_max_height, 
            initial_font_size=100, min_font_size=20, 
            font_path=font_path
        )
        
        # 获取字体对象
        font = self._get_font(font_size, font_path)
        
        # 分行处理文本
        lines = textwrap.wrap(text, width=chars_per_line)
        
        # 计算文本总高度
        line_height = font_size * 1.5
        text_height = len(lines) * line_height
        
        # 计算起始Y坐标（居中显示）
        y = (img_height - text_height) / 2
        
        # 绘制每一行文本
        for line in lines:
            # 计算行宽度
            line_width = font.getlength(line)
            
            # 计算X坐标（居中显示）
            x = (img_width - line_width) / 2
            
            # 绘制文本（带描边效果）
            draw.text(
                (x, y), 
                line, 
                fill=template['font_color'], 
                font=font,
                stroke_width=template['stroke_width'],
                stroke_fill=template['stroke_color']
            )
            
            # 更新Y坐标到下一行
            y += line_height
        
        # 保存图片（如果指定了输出路径）
        if output_path:
            img.save(output_path)
        
        return img

# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成喜报/悲报图片")
    parser.add_argument("text", help="要显示的文本内容")
    parser.add_argument("--type", choices=["good", "bad"], default="good", help="图片类型，good表示喜报，bad表示悲报")
    parser.add_argument("--output", default="output.jpg", help="输出文件路径")
    parser.add_argument("--assets", help="素材目录路径")
    parser.add_argument("--font", help="字体文件路径")
    
    args = parser.parse_args()
    
    generator = NewsGenerator(assets_dir=args.assets)
    generator.generate(args.text, news_type=args.type, output_path=args.output, font_path=args.font)
    
    print(f"图片已生成: {args.output}")
