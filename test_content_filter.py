#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容过滤功能测试脚本（独立版本）
"""

import re
from typing import List, Tuple

class ContentFilter:
    """
    内容过滤器，用于检测和过滤违禁词汇和露骨文案
    """
    
    def __init__(self):
        # 违禁词汇列表
        self.forbidden_words = {
            '睡', '睡觉', '拥抱', '双修', '采补', '吸精', '吸精气', '乱摸', '乱动', 
            '赤裸裸', '风韵', '韵味', '味道', '服侍', '爆浆', '口味', '尝鲜', '床上', 
            '大宝贝', '勾引', '色情', '偷人', '欲望', '互动', '鼎炉', '温柔', '温热', 
            '目光', '润湿', '洗澡', '不轨', '大腿', '怀孕', '抱起', '姿势', '春药', 
            '媚药', '软床', '丝袜', '诱惑', '催情', '允吸', '怀里', '亲吻', '毒品', 
            '上床', '强暴', '性欲', '上吊', '自杀', '跳楼', '尸体'
        }
        
        # 联想性词汇
        self.suggestive_words = {
            '内心空虚', '挤眉弄眼', '衣衫不整', '脸色潮红', '蹭了蹭', '双腿间', 
            '生命大和谐', '欲望上头', '房间互动', '皮肤发烫', '浑身燥热', '轻轻划过', 
            '躺在床上', '抱入怀中', '完美S型身材', '几乎将衣服撑爆'
        }
        
        # 禁用句式模式
        self.forbidden_patterns = [
            r'我想和你在一起',
            r'和.*一起睡',
            r'抱着.*睡觉',
            r'不喜欢和别人睡',
            r'沾了.*身子',
            r'贴在.*包裹下',
            r'身体.*起浮',
            r'面部发烫',
            r'将.*搂在怀中'
        ]
        
        # 敏感词替换映射
        self.word_replacements = {
            '睡': '休息',
            '睡觉': '休息',
            '罪犯': '嫌疑人',
            '通缉犯': 'TJ',
            '警察': 'jc',
            '监狱': '牢狱',
            '遗体': 'YT',
            '死': 'S',
            '上吊': 'SD',
            '自杀': 'ZS',
            '跳楼': 'TL',
            '尸体': 'ST'
        }
    
    def check_content(self, content: str) -> Tuple[bool, List[str]]:
        """
        检查内容是否包含违禁词汇或露骨文案
        
        Args:
            content: 要检查的内容
            
        Returns:
            Tuple[bool, List[str]]: (是否安全, 发现的问题列表)
        """
        issues = []
        
        # 检查违禁词汇
        for word in self.forbidden_words:
            if word in content:
                issues.append(f"包含违禁词汇: {word}")
        
        # 检查联想性词汇
        for phrase in self.suggestive_words:
            if phrase in content:
                issues.append(f"包含联想性词汇: {phrase}")
        
        # 检查禁用句式
        for pattern in self.forbidden_patterns:
            if re.search(pattern, content):
                issues.append(f"包含禁用句式: {pattern}")
        
        return len(issues) == 0, issues
    
    def filter_content(self, content: str) -> str:
        """
        过滤内容中的敏感词汇
        
        Args:
            content: 原始内容
            
        Returns:
            str: 过滤后的内容
        """
        filtered_content = content
        
        # 替换敏感词汇
        for original, replacement in self.word_replacements.items():
            filtered_content = filtered_content.replace(original, replacement)
        
        return filtered_content

def test_content_filter():
    """
    测试内容过滤器的各项功能
    """
    print("=== 内容过滤器测试开始 ===")
    
    # 初始化内容过滤器
    content_filter = ContentFilter()
    
    # 测试用例
    test_cases = [
        {
            "name": "正常内容",
            "content": "主角走进房间，开始调查案件的线索。",
            "expected_safe": True
        },
        {
            "name": "包含违禁词汇",
            "content": "主角和女主角一起睡觉，然后开始调查罪犯的行踪。",
            "expected_safe": False
        },
        {
            "name": "包含联想性词汇",
            "content": "她衣衫不整地从房间里走出来，脸色潮红。",
            "expected_safe": False
        },
        {
            "name": "包含禁用句式",
            "content": "我想和你在一起，永远不分离。",
            "expected_safe": False
        },
        {
            "name": "包含违法词汇",
            "content": "警察抓捕了这名罪犯，将其关进监狱。",
            "expected_safe": False
        }
    ]
    
    print("\n1. 测试内容安全检查功能:")
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {case['name']}")
        print(f"内容: {case['content']}")
        
        is_safe, issues = content_filter.check_content(case['content'])
        print(f"检查结果: {'安全' if is_safe else '不安全'}")
        
        if not is_safe:
            print(f"发现问题: {', '.join(issues)}")
        
        # 验证结果是否符合预期
        if is_safe == case['expected_safe']:
            print("✓ 测试通过")
        else:
            print("✗ 测试失败")
    
    print("\n2. 测试内容过滤功能:")
    filter_test_cases = [
        "主角回房睡觉，准备明天继续调查。",
        "警察逮捕了罪犯，案件终于告破。",
        "嫌疑人被关进监狱，等待审判。",
        "调查员发现了重要线索。"
    ]
    
    for i, content in enumerate(filter_test_cases, 1):
        print(f"\n过滤测试 {i}:")
        print(f"原始内容: {content}")
        
        filtered_content = content_filter.filter_content(content)
        print(f"过滤后内容: {filtered_content}")
        
        # 检查过滤后的内容是否安全
        is_safe, issues = content_filter.check_content(filtered_content)
        print(f"过滤后安全性: {'安全' if is_safe else '不安全'}")
        
        if not is_safe:
            print(f"仍存在问题: {', '.join(issues)}")
    
    print("\n=== 内容过滤器测试完成 ===")

if __name__ == "__main__":
    test_content_filter()