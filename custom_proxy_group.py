#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subconverter 配置生成脚本 v2
读取现有 pref.ini，根据 ruleset 自动生成 custom_proxy_group
"""

import re
import configparser
from typing import List, Dict, Set
from pathlib import Path


class Config:
    """配置常量"""

    # 节点类型
    NODE_TYPES = ['标准', '解锁', '原生']

    # 付费等级
    TIER_LEVELS = ['Light', 'Premium', 'Exclusive']

    # 预设地区配置
    REGIONS = {
        '香港': {'emoji': '🇭🇰', 'regex': '香港'},
        '台湾': {'emoji': '🇹🇼', 'regex': '台湾'},
        '日本': {'emoji': '🇯🇵', 'regex': '日本'},
        '韩国': {'emoji': '🇰🇷', 'regex': '韩国'},
        '新加坡': {'emoji': '🇸🇬', 'regex': '新加坡'},
        '美国': {'emoji': '🇺🇸', 'regex': '美国'},
        # '英国': {'emoji': '🇬🇧', 'regex': '(英国|UK|England|United\\s*Kingdom|英)'},
        # '德国': {'emoji': '🇩🇪', 'regex': '(德国|DE|Germany|德)'},
        # '法国': {'emoji': '🇫🇷', 'regex': '(法国|FR|France|法)'},
        # '加拿大': {'emoji': '🇨🇦', 'regex': '(加拿大|CA|Canada|加)'},
        # '澳大利亚': {'emoji': '🇦🇺', 'regex': '(澳大利亚|澳洲|AU|Australia|澳)'},
        # '俄罗斯': {'emoji': '🇷🇺', 'regex': '(俄罗斯|RU|Russia|俄)'},
        # '荷兰': {'emoji': '🇳🇱', 'regex': '(荷兰|NL|Netherlands)'},
        # '印度': {'emoji': '🇮🇳', 'regex': '(印度|IN|India)'},
        # '泰国': {'emoji': '🇹🇭', 'regex': '(泰国|TH|Thailand|泰)'},
        # '越南': {'emoji': '🇻🇳', 'regex': '(越南|VN|Vietnam|越)'},
        # '菲律宾': {'emoji': '🇵🇭', 'regex': '(菲律宾|PH|Philippines|菲)'},
        # '马来西亚': {'emoji': '🇲🇾', 'regex': '(马来西亚|MY|Malaysia)'},
        # '土耳其': {'emoji': '🇹🇷', 'regex': '(土耳其|TR|Turkey|土)'},
    }

    # Emoji 映射
    EMOJIS = {
        'type': {
            '标准': '📡',
            '解锁': '🔓',
            '原生': '🎯',
        },
        'tier': {
            'Light': '🌙',
            'Premium': '⭐',
            'Exclusive': '👑',
        },
        'other': '🌐',
    }

    # 特殊规则集配置（不需要节点选择的）
    SPECIAL_RULESETS = {
        '全球直连': {'type': 'DIRECT', 'options': ['[]DIRECT']},
        '全球拦截': {'type': 'REJECT', 'options': ['[]REJECT', '[]DIRECT']},
        '应用拦截': {'type': 'REJECT', 'options': ['[]REJECT', '[]DIRECT']},
        '广告拦截': {'type': 'REJECT', 'options': ['[]REJECT', '[]DIRECT']},
    }


class PrefIniParser:
    """pref.ini 解析器"""

    def __init__(self, ini_file: str):
        self.ini_file = ini_file
        self.rulesets = []

    def parse(self) -> List[Dict]:
        """解析 ruleset 配置"""
        rulesets = []

        with open(self.ini_file, 'r', encoding='utf-8') as f:
            in_ruleset_section = False

            for line in f:
                line = line.strip()

                # 检测 [ruleset] 段
                if line == '[ruleset]':
                    in_ruleset_section = True
                    continue
                elif line.startswith('[') and line.endswith(']'):
                    in_ruleset_section = False
                    continue

                # 解析 ruleset
                if in_ruleset_section and line and not line.startswith(';'):
                    if line.startswith('surge_ruleset='):
                        parts = line.replace('surge_ruleset=', '').split(',', 1)
                        if len(parts) >= 1:
                            ruleset_name = parts[0].strip()
                            rulesets.append({
                                'name': ruleset_name,
                                'line': line
                            })

        self.rulesets = rulesets
        return rulesets


class ProxyGroupGenerator:
    """代理组生成器"""

    def __init__(self):
        self.all_proxy_groups = []

    def generate_all_groups(self) -> List[str]:
        """生成所有代理组配置"""
        configs = []

        # 2. 地区分组
        configs.extend(self._generate_region_groups())

        # 3. 类型分组
        configs.extend(self._generate_type_groups())

        # 4. 付费等级分组
        configs.extend(self._generate_tier_groups())

        # 6. 详细分组（地区+类型+等级）
        configs.extend(self._generate_detailed_groups())

        # 5. 其他地区分组
        configs.extend(self._generate_other_region_groups())

        # 保存所有代理组名称（用于规则集引用）
        self.all_proxy_groups = self._extract_group_names(configs)

        return configs

    def _generate_base_groups(self) -> List[str]:
        """生成基础全局组"""
        return [
            "custom_proxy_group=🚀 节点选择`select`[]♻️ 自动选择`[]🎯 全球直连`.*",
            "custom_proxy_group=♻️ 自动选择`url-test`.*`http://www.gstatic.com/generate_204`300,5,50",
        ]

    def _generate_region_groups(self) -> List[str]:
        """生成地区分组"""
        groups = []

        for region, info in Config.REGIONS.items():
            emoji = info['emoji']
            regex = info['regex']
            groups.append(
                f"custom_proxy_group={emoji} {region}`select`{regex}"
            )

        return groups

    def _generate_type_groups(self) -> List[str]:
        """生成类型分组"""
        groups = []

        for node_type in Config.NODE_TYPES:
            emoji = Config.EMOJIS['type'][node_type]
            groups.append(
                f"custom_proxy_group={emoji} {node_type}`select`.*{node_type}.*"
            )

        return groups

    def _generate_tier_groups(self) -> List[str]:
        """生成付费等级分组"""
        groups = []

        for tier in Config.TIER_LEVELS:
            emoji = Config.EMOJIS['tier'][tier]
            groups.append(
                f"custom_proxy_group={emoji} {tier}`select`.*{tier}.*"
            )

        return groups

    def _generate_other_region_groups(self) -> List[str]:
        """生成其他地区分组"""
        groups = []

        # 构建排除预设地区的正则（否定前瞻）
        exclude_patterns = []
        for region_info in Config.REGIONS.values():
            # 提取正则中的关键词
            regex = region_info['regex']
            # 去掉外层括号，提取关键词
            keywords = regex.strip('()').split('|')
            exclude_patterns.extend(keywords)

        # 构建否定前瞻正则：(?!.*(香港|HK|日本|JP|...))
        negative_lookahead = f"(?!.*({'|'.join(exclude_patterns)}))"

        # 构建排除预设地区的正则
        exclude_patterns = []
        for region_info in Config.REGIONS.values():
            exclude_patterns.append(region_info['regex'])

        # 其他地区 + 各类型
        for node_type in Config.NODE_TYPES:
            type_emoji = Config.EMOJIS['type'][node_type]
            # 匹配包含类型但不包含预设地区的节点
            groups.append(
                f"custom_proxy_group={Config.EMOJIS['other']} 其他-{type_emoji}{node_type}`select`{negative_lookahead}.*{node_type}.*"
            )

        # 其他地区 + 各等级
        for tier in Config.TIER_LEVELS:
            tier_emoji = Config.EMOJIS['tier'][tier]
            groups.append(
                f"custom_proxy_group={Config.EMOJIS['other']} 其他-{tier_emoji}{tier}`select`{negative_lookahead}.*{tier}.*"
            )

        # 其他地区 + 类型 + 等级组合
        for node_type in Config.NODE_TYPES:
            for tier in Config.TIER_LEVELS:
                type_emoji = Config.EMOJIS['type'][node_type]
                tier_emoji = Config.EMOJIS['tier'][tier]
                groups.append(
                    f"custom_proxy_group={Config.EMOJIS['other']} 其他-{type_emoji}{node_type}-{tier_emoji}{tier}`select`{negative_lookahead}.*{node_type}.*{tier}.*"
                )

        return groups

    def _generate_detailed_groups(self) -> List[str]:
        """生成详细分组（地区+类型+等级），使用 url-test"""
        groups = []

        # 预设地区的详细分组
        for region, region_info in Config.REGIONS.items():
            region_emoji = region_info['emoji']
            region_regex = region_info['regex']

            # 地区 + 类型
            for node_type in Config.NODE_TYPES:
                type_emoji = Config.EMOJIS['type'][node_type]
                regex = f"{region_regex}.*{node_type}"
                groups.append(
                    f"custom_proxy_group={region_emoji}{region}-{type_emoji}{node_type}`url-test`{regex}`http://www.gstatic.com/generate_204`300,5,50"
                )

            # 地区 + 等级
            for tier in Config.TIER_LEVELS:
                tier_emoji = Config.EMOJIS['tier'][tier]
                regex = f"{region_regex}.*{tier}"
                groups.append(
                    f"custom_proxy_group={region_emoji}{region}-{tier_emoji}{tier}`url-test`{regex}`http://www.gstatic.com/generate_204`300,5,50"
                )

            # 地区 + 类型 + 等级
            for node_type in Config.NODE_TYPES:
                for tier in Config.TIER_LEVELS:
                    type_emoji = Config.EMOJIS['type'][node_type]
                    tier_emoji = Config.EMOJIS['tier'][tier]
                    regex = f"{region_regex}.*{node_type}.*{tier}"
                    groups.append(
                        f"custom_proxy_group={region_emoji}{region}-{type_emoji}{node_type}-{tier_emoji}{tier}`url-test`{regex}`http://www.gstatic.com/generate_204`300,5,50"
                    )

        return groups

    def _generate_ruleset_groups(self, rulesets: List[Dict]) -> List[str]:
        """根据 ruleset 生成对应的规则组"""
        groups = []
        processed_names = set()

        for ruleset in rulesets:
            name = ruleset['name']

            # 去重
            if name in processed_names:
                continue
            processed_names.add(name)

            # 检查是否是特殊规则集
            is_special = False
            for special_name, special_config in Config.SPECIAL_RULESETS.items():
                if special_name in name:
                    options = '`'.join(special_config['options'])
                    groups.append(f"custom_proxy_group={name}`select`{options}")
                    is_special = True
                    break

            if is_special:
                continue

            # 普通规则集：提供所有节点组选项
            options = self._build_ruleset_options(name)
            groups.append(f"custom_proxy_group={name}`select`{options}")

        return groups

    def _build_ruleset_options(self, ruleset_name: str) -> str:
        """构建规则集的选项列表"""
        options = []

        # 基础选项
        options.extend([
            '[]🚀 节点选择',
            '[]♻️ 自动选择',
            '[]🎯 全球直连',
        ])

        # 添加地区组
        for region, info in Config.REGIONS.items():
            emoji = info['emoji']
            options.append(f'[]{emoji} {region}')

        # 添加类型组
        for node_type in Config.NODE_TYPES:
            emoji = Config.EMOJIS['type'][node_type]
            options.append(f'[]{emoji} {node_type}')

        # 添加等级组
        for tier in Config.TIER_LEVELS:
            emoji = Config.EMOJIS['tier'][tier]
            options.append(f'[]{emoji} {tier}')

        # 添加其他地区组（只添加主要的）
        for node_type in Config.NODE_TYPES:
            type_emoji = Config.EMOJIS['type'][node_type]
            options.append(f'[]{Config.EMOJIS["other"]} 其他-{type_emoji}{node_type}')

        # 特殊规则集优化
        if '媒体' in ruleset_name or 'NETFLIX' in ruleset_name or 'YouTube' in ruleset_name:
            # 媒体类优先推荐原生节点
            options.insert(3, f'[]{Config.EMOJIS["type"]["原生"]} 原生')

        if '电报' in ruleset_name or 'Telegram' in ruleset_name:
            # 电报优先推荐新加坡和香港
            if '新加坡' in Config.REGIONS:
                options.insert(3, f'[]{Config.REGIONS["新加坡"]["emoji"]} 新加坡')
            if '香港' in Config.REGIONS:
                options.insert(3, f'[]{Config.REGIONS["香港"]["emoji"]} 香港')

        # 添加通配符（匹配所有节点）
        options.append('.*')

        return '`'.join(options)

    def _extract_group_names(self, configs: List[str]) -> List[str]:
        """提取所有代理组名称"""
        names = []
        for config in configs:
            match = re.match(r'custom_proxy_group=([^`]+)`', config)
            if match:
                names.append(match.group(1))
        return names


def main():
    """主函数"""

    output_file = 'pref_generated.ini'

    # 生成代理组
    generator = ProxyGroupGenerator()
    group_configs = generator.generate_all_groups()

    # 构建新的 clash_proxy_group 段
    new_clash_section = "[clash_proxy_group]\n"
    new_clash_section += ";自动生成的代理组配置\n"
    new_clash_section += ";生成时间: " + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
    new_clash_section += f";共 {len(group_configs)} 个代理组\n\n"
    new_clash_section += '\n'.join(group_configs) + "\n"

    # 写入新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_clash_section)

    print(f"\n✅ 配置生成完成!")
    print(f"📊 统计信息:")
    print(f"  - 生成代理组: {len(group_configs)} 个")
    print(f"  - 预设地区: {len(Config.REGIONS)} 个")
    print(f"  - 节点类型: {len(Config.NODE_TYPES)} 个")
    print(f"  - 付费等级: {len(Config.TIER_LEVELS)} 个")
    print(f"📝 输出文件: {output_file}")


if __name__ == "__main__":
    main()