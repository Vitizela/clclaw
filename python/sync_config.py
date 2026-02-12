#!/usr/bin/env python3
"""
一次性配置同步工具
从 config.json 同步到 config.yaml
"""
import yaml
import json
from pathlib import Path
from datetime import datetime

def sync_config():
    """同步配置"""
    # 读取 config.json
    json_path = Path(__file__).parent.parent / "config.json"
    yaml_path = Path(__file__).parent / "config.yaml"

    if not json_path.exists():
        print("❌ config.json 不存在")
        return

    if not yaml_path.exists():
        print("❌ config.yaml 不存在")
        return

    print("正在同步配置...")

    with open(json_path, 'r', encoding='utf-8') as f:
        nodejs_config = json.load(f)

    with open(yaml_path, 'r', encoding='utf-8') as f:
        python_config = yaml.safe_load(f)

    # 同步作者列表
    python_config['followed_authors'] = [
        {
            'name': author,
            'added_date': datetime.now().strftime('%Y-%m-%d'),
            'last_update': None,
            'total_posts': 0,
            'total_images': 0,
            'total_videos': 0,
            'tags': ['synced_from_nodejs'],
            'notes': '从 config.json 同步'
        }
        for author in nodejs_config.get('followedAuthors', [])
    ]

    # 保存
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(python_config, f, allow_unicode=True, sort_keys=False, indent=2)

    print(f"\n✅ 同步完成！已同步 {len(python_config['followed_authors'])} 位作者：")
    for author in python_config['followed_authors']:
        print(f"  - {author['name']}")

if __name__ == '__main__':
    sync_config()
