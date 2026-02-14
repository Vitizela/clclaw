#!/usr/bin/env python3
"""
Phase 3 数据库模块综合测试

测试所有核心功能：
- 数据库初始化
- 模型 CRUD 操作
- 触发器和统计
- 查询函数
- 同步功能
- 完整性检查
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加 python 目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'python'))

# 导入数据库模块
from src.database import (
    # 核心
    DatabaseConnection,
    get_default_connection,
    Author,
    Post,
    Media,

    # 查询
    get_global_stats,
    get_author_ranking,
    get_monthly_stats,
    get_hourly_distribution,
    get_author_detail_stats,
    search_posts,

    # 完整性
    fix_statistics,
    check_orphaned_records,
    verify_database_structure,
)


# =============================================================================
# 测试配置
# =============================================================================

TEST_DB_PATH = 'python/data/test_phase3.db'
TEST_PASSED = 0
TEST_FAILED = 0


def test_header(title):
    """打印测试标题"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def test_step(description):
    """打印测试步骤"""
    print(f"\n→ {description}")


def test_success(message):
    """测试成功"""
    global TEST_PASSED
    TEST_PASSED += 1
    print(f"  ✓ {message}")


def test_failure(message):
    """测试失败"""
    global TEST_FAILED
    TEST_FAILED += 1
    print(f"  ✗ {message}")


def assert_equal(actual, expected, message):
    """断言相等"""
    if actual == expected:
        test_success(f"{message}: {actual}")
    else:
        test_failure(f"{message}: expected {expected}, got {actual}")


def assert_true(condition, message):
    """断言为真"""
    if condition:
        test_success(message)
    else:
        test_failure(message)


# =============================================================================
# 测试函数
# =============================================================================

def test_1_database_initialization():
    """测试 1: 数据库初始化"""
    test_header("测试 1: 数据库初始化")

    # 删除旧的测试数据库
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    test_step("创建数据库连接")
    db = DatabaseConnection.get_instance(TEST_DB_PATH)
    test_success("数据库连接创建成功")

    test_step("初始化数据库结构")
    success = db.initialize_database()
    assert_true(success, "数据库初始化成功")

    test_step("验证数据库是否已初始化")
    is_init = db.is_initialized()
    assert_true(is_init, "数据库已初始化")

    test_step("获取数据库信息")
    info = db.get_db_info()
    assert_equal(info['table_count'], 5, "表数量")  # 包括 sqlite_sequence
    assert_true(info['index_count'] >= 10, f"索引数量 >= 10 (实际: {info['index_count']})")
    assert_equal(info['view_count'], 2, "视图数量")
    assert_equal(info['trigger_count'], 3, "触发器数量")

    test_step("验证数据库结构")
    structure = verify_database_structure(db)
    assert_true(structure['is_valid'], "数据库结构完整")
    assert_true('authors' in structure['tables'], "authors 表存在")
    assert_true('posts' in structure['tables'], "posts 表存在")
    assert_true('media' in structure['tables'], "media 表存在")

    return db


def test_2_author_model(db):
    """测试 2: Author 模型"""
    test_header("测试 2: Author 模型 CRUD")

    # 设置模型使用的数据库
    Author._db = db
    Post._db = db
    Media._db = db

    test_step("创建作者 1")
    author1 = Author.create(
        name="测试作者A",
        added_date="2026-02-10",
        url="https://test.com/@测试作者A",
        forum_total_posts=100,
        tags=["测试", "示例"],
        notes="这是第一个测试作者"
    )
    assert_true(author1.id is not None, "作者 1 创建成功")

    test_step("创建作者 2")
    author2 = Author.create(
        name="测试作者B",
        added_date="2026-02-11",
        url="https://test.com/@测试作者B",
        forum_total_posts=80,
        tags=["测试"]
    )
    assert_true(author2.id is not None, "作者 2 创建成功")

    test_step("创建作者 3")
    author3 = Author.create(
        name="测试作者C",
        added_date="2026-02-12",
        forum_total_posts=50
    )
    assert_true(author3.id is not None, "作者 3 创建成功")

    test_step("根据名称查询作者")
    found = Author.get_by_name("测试作者A")
    assert_equal(found.name, "测试作者A", "查询作者成功")
    assert_equal(found.tags, ["测试", "示例"], "tags 解析正确")

    test_step("查询所有作者")
    all_authors = Author.get_all()
    assert_equal(len(all_authors), 3, "作者总数")

    test_step("更新作者信息")
    author1.update(notes="更新后的备注", forum_total_posts=120)
    updated = Author.get_by_name("测试作者A")
    assert_equal(updated.notes, "更新后的备注", "notes 更新成功")
    assert_equal(updated.forum_total_posts, 120, "forum_total_posts 更新成功")

    return [author1, author2, author3]


def test_3_post_model(db, authors):
    """测试 3: Post 模型和触发器"""
    test_header("测试 3: Post 模型和触发器")

    author1, author2, author3 = authors

    test_step("为作者 A 创建 5 篇帖子")
    posts_a = []
    for i in range(1, 6):
        post = Post.create(
            author_id=author1.id,
            url=f"https://test.com/post/{i}.html",
            url_hash=f"hash{i:04d}",
            title=f"测试帖子 A-{i}",
            file_path=f"/archive/测试作者A/2026/02/帖子{i}",
            archived_date="2026-02-14",
            publish_date=f"2026-02-{10+i} 15:30:00",
            image_count=i * 2,
            video_count=i % 2,
            content_length=1000 + i * 100,
            word_count=500 + i * 50,
            file_size_bytes=5000000 + i * 1000000
        )
        posts_a.append(post)
        test_success(f"帖子 A-{i} 创建成功 (图片: {i*2}, 视频: {i%2})")

    test_step("检查触发器：作者 A 的统计应自动更新")
    author1_updated = Author.get_by_id(author1.id)
    assert_equal(author1_updated.total_posts, 5, "total_posts 自动更新")
    assert_equal(author1_updated.total_images, 2+4+6+8+10, "total_images 自动更新")  # 30
    assert_equal(author1_updated.total_videos, 1+0+1+0+1, "total_videos 自动更新")  # 3

    test_step("为作者 B 创建 3 篇帖子")
    posts_b = []
    for i in range(1, 4):
        post = Post.create(
            author_id=author2.id,
            url=f"https://test.com/author2/post{i}.html",
            url_hash=f"hashb{i:03d}",
            title=f"测试帖子 B-{i}",
            file_path=f"/archive/测试作者B/2026/02/帖子{i}",
            archived_date="2026-02-14",
            publish_date=f"2026-02-{12+i} 10:00:00",
            image_count=i * 3,
            video_count=i,
            content_length=1500,
            word_count=700,
            file_size_bytes=6000000
        )
        posts_b.append(post)

    test_step("检查触发器：作者 B 的统计")
    author2_updated = Author.get_by_id(author2.id)
    assert_equal(author2_updated.total_posts, 3, "作者 B total_posts")
    assert_equal(author2_updated.total_images, 3+6+9, "作者 B total_images")  # 18

    test_step("为作者 C 创建 1 篇帖子")
    post_c = Post.create(
        author_id=author3.id,
        url=f"https://test.com/author3/post1.html",
        url_hash="hashc001",
        title="测试帖子 C-1",
        file_path="/archive/测试作者C/2026/02/帖子1",
        archived_date="2026-02-14",
        publish_date="2026-02-13 08:00:00",
        image_count=10,
        video_count=2,
        content_length=2000,
        word_count=1000,
        file_size_bytes=8000000
    )

    test_step("测试 Post.exists()")
    assert_true(Post.exists(posts_a[0].url), "Post.exists() 正常工作")
    assert_true(not Post.exists("https://nonexist.com"), "不存在的帖子返回 False")

    test_step("测试 Post.get_by_author()")
    author_posts = Post.get_by_author(author1.id)
    assert_equal(len(author_posts), 5, "get_by_author() 返回正确数量")

    test_step("测试时间冗余字段")
    assert_equal(posts_a[0].publish_year, 2026, "publish_year 正确")
    assert_equal(posts_a[0].publish_month, 2, "publish_month 正确")

    return posts_a + posts_b + [post_c]


def test_4_media_model(db, posts):
    """测试 4: Media 模型"""
    test_header("测试 4: Media 模型")

    test_step("为第一篇帖子添加媒体")
    post = posts[0]

    media_list = []
    for i in range(1, 4):
        media = Media.create(
            post_id=post.id,
            type='image',
            url=f"https://test.com/img{i}.jpg",
            file_name=f"img_{i}.jpg",
            file_path=f"/archive/photo/img_{i}.jpg",
            file_size_bytes=500000 + i * 10000,
            width=1920,
            height=1080
        )
        media_list.append(media)

    media_video = Media.create(
        post_id=post.id,
        type='video',
        url="https://test.com/video1.mp4",
        file_name="video_1.mp4",
        file_path="/archive/video/video_1.mp4",
        file_size_bytes=10000000,
        duration=120
    )
    media_list.append(media_video)

    test_success(f"创建了 3 张图片和 1 个视频")

    test_step("测试 Media.get_by_post()")
    all_media = Media.get_by_post(post.id)
    assert_equal(len(all_media), 4, "get_by_post() 返回所有媒体")

    images = Media.get_by_post(post.id, media_type='image')
    assert_equal(len(images), 3, "按类型过滤图片")

    videos = Media.get_by_post(post.id, media_type='video')
    assert_equal(len(videos), 1, "按类型过滤视频")

    test_step("测试 post.get_media()")
    post_media = post.get_media()
    assert_equal(len(post_media), 4, "post.get_media() 正常工作")

    return media_list


def test_5_query_functions(db):
    """测试 5: 查询函数"""
    test_header("测试 5: 查询函数")

    test_step("get_global_stats() - 全局统计")
    stats = get_global_stats(db)
    assert_equal(stats['total_authors'], 3, "总作者数")
    assert_equal(stats['total_posts'], 9, "总帖子数 (5+3+1)")
    assert_equal(stats['total_images'], 30+18+10, "总图片数")  # 58
    assert_equal(stats['total_videos'], 3+6+2, "总视频数")  # 11
    assert_true(stats['total_size_bytes'] > 0, "总大小 > 0")
    print(f"    平均每作者帖子数: {stats['avg_posts_per_author']}")
    print(f"    平均每帖图片数: {stats['avg_images_per_post']}")

    test_step("get_author_ranking() - 作者排行榜")
    ranking = get_author_ranking(order_by='posts', limit=10, db=db)
    assert_equal(len(ranking), 3, "排行榜返回 3 位作者")
    assert_equal(ranking[0]['name'], '测试作者A', "第 1 名是作者 A")
    assert_equal(ranking[0]['post_count'], 5, "作者 A 有 5 篇帖子")
    assert_equal(ranking[1]['name'], '测试作者B', "第 2 名是作者 B")

    test_step("get_monthly_stats() - 月度统计")
    monthly = get_monthly_stats(db=db)
    assert_true(len(monthly) > 0, "月度统计有数据")
    print(f"    2026年2月统计: {monthly[0]}")

    test_step("get_hourly_distribution() - 时间分布")
    hourly = get_hourly_distribution(db=db)
    assert_equal(len(hourly), 24, "返回 24 小时分布")
    print(f"    早上 10 点: {hourly[10]} 篇")
    print(f"    下午 15 点: {hourly[15]} 篇")

    test_step("get_author_detail_stats() - 作者详细统计")
    detail = get_author_detail_stats("测试作者A", db=db)
    assert_true(detail is not None, "返回详细统计")
    assert_equal(detail['basic_info']['name'], '测试作者A', "基本信息正确")
    assert_equal(detail['archive_stats']['total_posts'], 5, "归档统计正确")
    print(f"    归档进度: {detail['archive_stats']['archive_progress']}%")

    test_step("search_posts() - 帖子搜索")
    results = search_posts(keyword="测试帖子 A", db=db)
    assert_true(len(results) >= 5, "搜索到作者 A 的帖子")

    results = search_posts(author_name="测试作者B", db=db)
    assert_equal(len(results), 3, "按作者过滤")

    results = search_posts(has_images=True, db=db)
    assert_equal(len(results), 9, "所有帖子都有图片")


def test_6_integrity_checks(db):
    """测试 6: 完整性检查"""
    test_header("测试 6: 完整性检查")

    test_step("check_orphaned_records() - 检测孤立记录")
    orphaned = check_orphaned_records(db)
    assert_equal(len(orphaned['orphaned_posts']), 0, "没有孤立帖子")
    assert_equal(len(orphaned['orphaned_media']), 0, "没有孤立媒体")

    test_step("fix_statistics() - 修复统计字段")
    fixed_count = fix_statistics(db)
    assert_equal(fixed_count, 3, "修复了 3 个作者的统计")

    test_step("验证统计修复后的正确性")
    author = Author.get_by_name("测试作者A")
    assert_equal(author.total_posts, 5, "修复后 total_posts 正确")
    assert_equal(author.total_images, 30, "修复后 total_images 正确")


def test_7_model_relationships(db):
    """测试 7: 模型关联和级联删除"""
    test_header("测试 7: 模型关联和级联删除")

    test_step("测试 author.get_posts()")
    author = Author.get_by_name("测试作者A")
    posts = author.get_posts()
    assert_equal(len(posts), 5, "get_posts() 返回正确数量")

    test_step("测试 author.get_stats()")
    stats = author.get_stats()
    assert_true('post_count' in stats, "stats 包含 post_count")
    assert_true('avg_images_per_post' in stats, "stats 包含平均值")

    test_step("删除一篇帖子")
    post_to_delete = posts[0]
    old_count = author.total_posts
    post_to_delete.delete()

    test_step("验证触发器：删除帖子后作者统计自动更新")
    author_updated = Author.get_by_id(author.id)
    assert_equal(author_updated.total_posts, old_count - 1, "删除后 total_posts 自动减少")

    test_step("创建测试作者并删除（测试级联删除）")
    test_author = Author.create(
        name="待删除作者",
        added_date="2026-02-14"
    )

    test_post = Post.create(
        author_id=test_author.id,
        url="https://delete.com/post1.html",
        url_hash="del00001",
        title="待删除帖子",
        file_path="/delete/post1",
        archived_date="2026-02-14",
        image_count=5
    )

    test_media = Media.create(
        post_id=test_post.id,
        type='image',
        url="https://delete.com/img.jpg",
        file_name="img.jpg",
        file_path="/delete/img.jpg",
        file_size_bytes=100000
    )

    test_step("删除作者（应级联删除帖子和媒体）")
    test_author.delete()

    # 验证帖子和媒体也被删除
    deleted_post = Post.get_by_id(test_post.id)
    deleted_media = Media.get_by_id(test_media.id)
    assert_true(deleted_post is None, "帖子被级联删除")
    assert_true(deleted_media is None, "媒体被级联删除")


def test_8_edge_cases(db):
    """测试 8: 边界情况"""
    test_header("测试 8: 边界情况")

    test_step("创建没有发布日期的帖子")
    author = Author.get_by_name("测试作者C")
    post = Post.create(
        author_id=author.id,
        url="https://test.com/no-date.html",
        url_hash="nodate01",
        title="无日期帖子",
        file_path="/archive/no-date",
        archived_date="2026-02-14",
        publish_date=None,  # 没有发布日期
        image_count=0,
        video_count=0
    )
    assert_true(post.id is not None, "无日期帖子创建成功")
    assert_true(post.publish_year is None, "publish_year 为 None")

    test_step("创建空标签的作者")
    author_no_tags = Author.create(
        name="无标签作者",
        added_date="2026-02-14",
        tags=None
    )
    assert_true(author_no_tags.tags is None, "tags 为 None")

    test_step("更新不存在的字段（应抛出异常）")
    try:
        author.update(nonexistent_field="test")
        test_failure("应该抛出异常但没有")
    except Exception:
        test_success("正确抛出异常")


def print_summary():
    """打印测试摘要"""
    print(f"\n{'=' * 70}")
    print(f"  测试摘要")
    print(f"{'=' * 70}")
    print(f"  ✓ 通过: {TEST_PASSED}")
    print(f"  ✗ 失败: {TEST_FAILED}")
    print(f"  总计: {TEST_PASSED + TEST_FAILED}")

    if TEST_FAILED == 0:
        print(f"\n  🎉 所有测试通过！")
    else:
        print(f"\n  ⚠️  有 {TEST_FAILED} 个测试失败")

    print(f"{'=' * 70}\n")


# =============================================================================
# 主测试流程
# =============================================================================

def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("  Phase 3 数据库模块综合测试")
    print("=" * 70)

    try:
        # 测试 1: 数据库初始化
        db = test_1_database_initialization()

        # 测试 2: Author 模型
        authors = test_2_author_model(db)

        # 测试 3: Post 模型和触发器
        posts = test_3_post_model(db, authors)

        # 测试 4: Media 模型
        media = test_4_media_model(db, posts)

        # 测试 5: 查询函数
        test_5_query_functions(db)

        # 测试 6: 完整性检查
        test_6_integrity_checks(db)

        # 测试 7: 模型关联
        test_7_model_relationships(db)

        # 测试 8: 边界情况
        test_8_edge_cases(db)

        # 打印摘要
        print_summary()

        # 清理
        print("清理测试数据库...")
        db.close()
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        print("✓ 清理完成\n")

        return TEST_FAILED == 0

    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
