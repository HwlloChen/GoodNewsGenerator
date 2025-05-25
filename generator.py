#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
喜报/悲报生成器
用于生成喜报或悲报风格的图片，支持自定义文本内容和样式，支持Emoji和特殊字符
"""

import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Dict, Optional, Literal
import unicodedata

# 尝试导入pilmoji，如果没有安装则使用备用方案
try:
    from pilmoji import Pilmoji
    PILMOJI_AVAILABLE = True
except ImportError:
    PILMOJI_AVAILABLE = False
    print("警告: pilmoji库未安装，Emoji显示可能不正常。建议运行: pip install pilmoji")

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
                'stroke_color': (89, 88, 87),  # 黑色
                'stroke_width': 0
            }
        }
        
        # 默认字体设置
        self.default_font_path = os.path.join(self.assets_dir, 'font.ttf')
        self.emoji_font_path = os.path.join(self.assets_dir, 'NotoColorEmoji.ttf')
        
    def _has_emoji(self, text: str) -> bool:
        """
        检查文本是否包含Emoji
        
        Args:
            text: 要检查的文本
            
        Returns:
            是否包含Emoji
        """
        for char in text:
            if unicodedata.category(char) == 'So' or '\U0001F000' <= char <= '\U0001F9FF':
                return True
        return False
        
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
                return ImageFont.load_default()
            except:
                raise Exception("无法加载字体文件")
    
    def _get_text_size_pilmoji(self, text: str, font_size: int, font_path: str = None) -> Tuple[float, float]:
        """
        使用Pilmoji获取文本尺寸（支持Emoji）
        
        Args:
            text: 文本内容
            font_size: 字体大小
            font_path: 字体文件路径
            
        Returns:
            (宽度, 高度)
        """
        if not PILMOJI_AVAILABLE:
            # 如果没有pilmoji，使用备用方案
            font = self._get_font(font_size, font_path)
            return font.getlength(text), font_size
            
        # 创建临时图片来测量文本尺寸
        temp_img = Image.new('RGB', (1000, 1000), 'white')
        
        # 使用Pilmoji测量文本
        if font_path and os.path.exists(font_path):
            main_font = ImageFont.truetype(font_path, font_size)
        else:
            main_font = ImageFont.truetype(self.default_font_path, font_size)
        with Pilmoji(temp_img, emoji_scale_factor=1.3) as pilmoji:
            # 获取文本边界框
            bbox = pilmoji.getsize(text, font=main_font)
            return bbox[0], bbox[1]
    
    def _calculate_font_size(self, text: str, max_width: int, max_height: int, 
                        initial_font_size: int = 100, 
                        min_font_size: int = 20,
                        font_path: str = None) -> Tuple[int, int]:
        """
        计算适合的字体大小和行数（最多三行）
        优先通过缩小字体来适应单行文本；仅当字体达到最小值且文本过长时，才增加行数并重新计算字体大小。
        
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
        def get_text_width(text: str, font_size: int) -> float:
            """获取指定字体大小下文本的宽度"""
            if has_emoji and PILMOJI_AVAILABLE:
                width, _ = self._get_text_size_pilmoji(text, font_size, font_path)
            else:
                font = self._get_font(font_size, font_path)
                width = font.getlength(text)
            return width
            
        has_emoji = self._has_emoji(text)
        current_line_count = 1
        
        while current_line_count <= 3:
            # 每增加一行，都从初始字体大小重新开始计算
            font_size = initial_font_size
            chars_per_line = (len(text) + current_line_count - 1) // current_line_count
            
            while font_size >= min_font_size:
                # 尝试调整每行字符数
                for cpl_adjust in [0, -1, 1, -2, 2]:
                    cpl = max(1, chars_per_line + cpl_adjust)
                    lines = textwrap.wrap(text, width=cpl, break_long_words=True, break_on_hyphens=False)
                    
                    # 检查行数是否符合要求
                    if len(lines) != current_line_count:
                        continue
                    
                    # 计算最大行宽度
                    max_line_width = 0
                    for line in lines:
                        line_width = get_text_width(line, font_size)
                        max_line_width = max(max_line_width, line_width)
                    
                    text_height = current_line_count * font_size * 1.5  # 1.5为行间距系数
                    
                    # 如果文本能够适应指定区域，返回结果
                    if max_line_width <= max_width and text_height <= max_height:
                        return font_size, cpl
                
                # 当前字体大小不合适，继续缩小
                font_size -= 5
            
            # 如果使用最小字体仍然无法适应当前行数，增加行数重试
            current_line_count += 1
        
        # 如果三行都无法适应，使用最小字体和三行
        return min_font_size, max(1, (len(text) + 2) // 3)
    
    def _draw_text_with_emoji(self, img: Image.Image, text: str, x: float, y: float, 
                             font_size: int, font_color: tuple, stroke_width: int = 0, 
                             stroke_color: tuple = None, font_path: str = None):
        """
        绘制支持Emoji的文本
        
        Args:
            img: 图片对象
            text: 文本内容
            x: X坐标
            y: Y坐标
            font_size: 字体大小
            font_color: 字体颜色
            stroke_width: 描边宽度
            stroke_color: 描边颜色
            font_path: 字体文件路径
        """
        if PILMOJI_AVAILABLE and self._has_emoji(text):
            # 使用Pilmoji绘制文本（支持Emoji）
            if font_path and os.path.exists(font_path):
                main_font = ImageFont.truetype(font_path, font_size)
            else:
                main_font = ImageFont.truetype(self.default_font_path, font_size)
            with Pilmoji(img, emoji_scale_factor=1.3) as pilmoji:
                pilmoji.text(
                    (int(x), int(y)),
                    text,
                    fill=font_color,
                    font=main_font,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_color
                )
        else:
            # 使用传统方式绘制文本
            draw = ImageDraw.Draw(img)
            font = self._get_font(font_size, font_path)
            draw.text(
                (x, y),
                text,
                fill=font_color,
                font=font,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )
    
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
            img = Image.open(template['image']).convert('RGBA')  # 转换为RGBA以支持透明度
        except Exception as e:
            raise Exception(f"无法打开背景图片: {e}")
        
        # 计算文本区域大小（图片宽度的80%，高度的60%）
        img_width, img_height = img.size
        text_max_width = int(img_width * 0.8)
        text_max_height = int(img_height * 0.6)
        
        # 计算合适的字体大小和每行字符数
        font_size, chars_per_line = self._calculate_font_size(
        text, text_max_width, text_max_height, 
        initial_font_size=90, min_font_size=70, 
        font_path=font_path
    )
        
        # 分行处理文本
        lines = textwrap.wrap(text, width=chars_per_line, break_long_words=True, break_on_hyphens=False)
        if len(lines) > 3:
            # 如果超过三行，重新计算每行字符数强制分成三行
            chars_per_line = max(1, (len(text) + 2) // 3)
            lines = textwrap.wrap(text, width=chars_per_line, break_long_words=True, break_on_hyphens=False)
            lines = lines[:3]  # 确保不超过三行
        
        # 如果wrap后没有分行（可能是因为单个词太长），强制分行
        if not lines and text:
            lines = [text]
        
        # 计算文本总高度
        line_height = font_size * 1.5
        text_height = len(lines) * line_height
        
        # 计算起始Y坐标（居中显示）
        y = (img_height - text_height) / 2
        
        # 绘制每一行文本
        for line in lines:
            if not line.strip():  # 跳过空行
                y += line_height
                continue
                
            # 计算行宽度
            if self._has_emoji(line) and PILMOJI_AVAILABLE:
                line_width, _ = self._get_text_size_pilmoji(line, font_size, font_path)
            else:
                font = self._get_font(font_size, font_path)
                line_width = font.getlength(line)
            
            # 计算X坐标（居中显示）
            x = (img_width - line_width) / 2
            
            # 绘制文本
            self._draw_text_with_emoji(
                img, line, x, y, font_size,
                template['font_color'],
                template['stroke_width'],
                template['stroke_color'],
                font_path
            )
            
            # 更新Y坐标到下一行
            y += line_height
        
        # 转换回RGB模式（如果需要保存为JPEG）
        if output_path and output_path.lower().endswith(('.jpg', '.jpeg')):
            # 创建白色背景
            rgb_img = Image.new('RGB', img.size, 'white')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # 保存图片（如果指定了输出路径）
        if output_path:
            img.save(output_path, quality=95)
        
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