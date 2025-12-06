#!/usr/bin/env python3
"""
慢查询分析脚本
用于分析数据库慢查询并生成优化建议
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from shared.database.connection import get_async_session
from loguru import logger


async def analyze_slow_queries():
    """分析慢查询"""
    async for db in get_async_session():
        try:
            # 检查是否启用了 pg_stat_statements
            check_result = await db.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements')")
            )
            has_extension = check_result.scalar()
            
            if not has_extension:
                logger.warning("pg_stat_statements 扩展未启用")
                logger.info("要启用，请执行: CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
                return
            
            # 获取慢查询统计
            query = text("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    stddev_exec_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_exec_time > 100  -- 平均执行时间超过 100ms
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """)
            
            result = await db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                logger.info("✅ 没有发现慢查询（平均执行时间 > 100ms）")
                return
            
            logger.info(f"🔍 发现 {len(rows)} 个慢查询：\n")
            
            for i, row in enumerate(rows, 1):
                logger.info(f"\n--- 慢查询 #{i} ---")
                logger.info(f"平均执行时间: {row.mean_exec_time:.2f} ms")
                logger.info(f"总执行时间: {row.total_exec_time:.2f} ms")
                logger.info(f"最大执行时间: {row.max_exec_time:.2f} ms")
                logger.info(f"调用次数: {row.calls}")
                logger.info(f"返回行数: {row.rows}")
                logger.info(f"查询: {row.query[:200]}...")
                
                # 生成优化建议
                suggestions = []
                if row.calls > 1000:
                    suggestions.append("考虑添加缓存")
                if "WHERE" in row.query and "JOIN" in row.query:
                    suggestions.append("检查是否需要添加索引")
                if row.mean_exec_time > 1000:
                    suggestions.append("考虑优化查询逻辑或添加索引")
                
                if suggestions:
                    logger.info(f"💡 优化建议: {', '.join(suggestions)}")
            
            # 分析索引使用情况
            logger.info("\n\n📊 索引使用情况分析：\n")
            index_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0  -- 未使用的索引
                ORDER BY schemaname, tablename
                LIMIT 20
            """)
            
            index_result = await db.execute(index_query)
            unused_indexes = index_result.fetchall()
            
            if unused_indexes:
                logger.warning(f"⚠️  发现 {len(unused_indexes)} 个未使用的索引：")
                for idx in unused_indexes:
                    logger.warning(f"  - {idx.schemaname}.{idx.tablename}.{idx.indexname}")
                logger.info("💡 建议：考虑删除未使用的索引以节省空间")
            else:
                logger.info("✅ 所有索引都在使用中")
            
        except Exception as e:
            logger.error(f"分析慢查询时出错: {e}")
        finally:
            await db.close()
            break


async def analyze_table_statistics():
    """分析表统计信息"""
    async for db in get_async_session():
        try:
            query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC
            """)
            
            result = await db.execute(query)
            tables = result.fetchall()
            
            logger.info("\n\n📈 表统计信息：\n")
            for table in tables:
                logger.info(f"\n表: {table.tablename}")
                logger.info(f"  行数: {table.live_rows:,}")
                logger.info(f"  死行数: {table.dead_rows:,}")
                logger.info(f"  插入: {table.inserts:,}")
                logger.info(f"  更新: {table.updates:,}")
                logger.info(f"  删除: {table.deletes:,}")
                
                if table.dead_rows > table.live_rows * 0.1:
                    logger.warning(f"  ⚠️  死行数较多，建议执行 VACUUM")
                
                if not table.last_autovacuum and not table.last_vacuum:
                    logger.warning(f"  ⚠️  从未执行过 VACUUM")
                
        except Exception as e:
            logger.error(f"分析表统计信息时出错: {e}")
        finally:
            await db.close()
            break


if __name__ == "__main__":
    logger.info("🔍 开始分析慢查询...")
    asyncio.run(analyze_slow_queries())
    asyncio.run(analyze_table_statistics())
    logger.info("\n✅ 分析完成！")

