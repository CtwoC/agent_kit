"""
核心流程编排模块
负责按顺序执行三个主要job：Load Profile -> Chat Processor -> Store Profile
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

from utils.logger import get_logger
from utils.status_codes import ChatStatus, create_status_info, StatusManager
from .load_profile import LoadProfile
from .chat_processor import ChatProcessor
from .store_profile import StoreProfile

logger = get_logger(__name__)

class CoreFlow:
    """
    核心流程编排器
    简化版本，使用异步方式顺序执行三个job
    """
    
    def __init__(self):
        """初始化核心处理组件"""
        self.load_profile = LoadProfile()
        self.chat_processor = ChatProcessor()
        self.store_profile = StoreProfile()
        
        logger.info("📦 CoreFlow初始化完成")
    
    async def run(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整的对话处理流程
        
        Args:
            request_data: 包含uid、message等基础请求信息的字典
            
        Returns:
            Dict[str, Any]: 包含完整处理结果的字典
        """
        uid = request_data.get("uid")
        session_id = request_data.get("session_id")
        
        logger.info(f"🚀 开始核心流程处理: {uid}")
        
        # 初始化流程上下文
        flow_context = {
            **request_data,
            "flow_start_time": datetime.now(),
            "flow_errors": [],
            "status": create_status_info(
                ChatStatus.PENDING,
                message=f"开始处理客户 {uid} 的请求",
                progress=0.0
            )
        }
        
        try:
            # 步骤1: 加载客户Profile
            logger.info(f"📋 步骤1: 加载客户Profile - {uid}")
            enhanced_data = await self._execute_with_error_handling(
                self.load_profile.process,
                flow_context,
                "LoadProfile"
            )
            
            # 检查加载是否成功
            if enhanced_data.get("load_error"):
                logger.warning(f"Profile加载有错误，但继续处理: {enhanced_data['load_error']}")
            
            # 步骤2: 处理AI对话
            logger.info(f"💬 步骤2: 处理AI对话 - {uid}")
            completion_data = await self._execute_with_error_handling(
                self.chat_processor.process,
                enhanced_data,
                "ChatProcessor"
            )
            
            # 检查对话是否成功
            if completion_data.get("processing_error"):
                logger.warning(f"对话处理有错误: {completion_data['processing_error']}")
                # 对话失败时，仍然尝试存储基础信息
            
            # 步骤3: 存储客户Profile
            logger.info(f"💾 步骤3: 存储客户Profile - {uid}")
            final_result = await self._execute_with_error_handling(
                self.store_profile.process,
                completion_data,
                "StoreProfile"
            )
            
            # 检查存储是否成功
            if final_result.get("storage_error"):
                logger.warning(f"Profile存储有错误: {final_result['storage_error']}")
            
            # 计算流程总耗时
            flow_duration = (datetime.now() - flow_context["flow_start_time"]).total_seconds()
            
            # 构建最终响应
            final_response = {
                **final_result,
                "flow_duration": flow_duration,
                "flow_errors": flow_context["flow_errors"],
                "flow_completed": True,
                "status": create_status_info(
                    ChatStatus.COMPLETED,
                    message=f"客户 {uid} 的请求处理完成",
                    progress=1.0
                )
            }
            
            logger.info(f"✅ 核心流程完成: {uid}, 耗时: {flow_duration:.2f}s")
            
            return final_response
            
        except Exception as e:
            logger.error(f"❌ 核心流程失败 {uid}: {str(e)}")
            
            # 构建错误响应
            flow_duration = (datetime.now() - flow_context["flow_start_time"]).total_seconds()
            
            error_response = {
                **flow_context,
                "flow_duration": flow_duration,
                "flow_error": str(e),
                "flow_completed": False,
                "status": create_status_info(
                    ChatStatus.ERROR,
                    message=f"客户 {uid} 的请求处理失败: {str(e)}",
                    error_details=str(e)
                )
            }
            
            return error_response
    
    async def _execute_with_error_handling(
        self, 
        job_func, 
        input_data: Dict[str, Any], 
        job_name: str
    ) -> Dict[str, Any]:
        """
        带错误处理的job执行包装器
        
        Args:
            job_func: 要执行的job函数
            input_data: 输入数据
            job_name: job名称（用于日志）
            
        Returns:
            Dict[str, Any]: job执行结果
        """
        start_time = datetime.now()
        
        try:
            logger.debug(f"🔄 开始执行 {job_name}")
            
            result = await job_func(input_data)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"✅ {job_name} 执行完成，耗时: {duration:.2f}s")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"{job_name} 执行失败: {str(e)}"
            
            logger.error(f"❌ {error_msg}, 耗时: {duration:.2f}s")
            
            # 记录错误到流程上下文
            input_data["flow_errors"].append({
                "job": job_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "duration": duration
            })
            
            # 返回包含错误信息的数据
            return {
                **input_data,
                f"{job_name.lower()}_error": str(e),
                f"{job_name.lower()}_duration": duration
            }


class ParallelCoreFlow:
    """
    并行核心流程编排器
    在保持数据依赖的前提下，尽可能并行执行独立任务
    """
    
    def __init__(self):
        """初始化并行处理组件"""
        self.load_profile = LoadProfile()
        self.chat_processor = ChatProcessor()
        self.store_profile = StoreProfile()
        
        logger.info("🔄 ParallelCoreFlow初始化完成")
    
    async def run(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行并行优化的对话处理流程
        
        Args:
            request_data: 包含uid、message等基础请求信息的字典
            
        Returns:
            Dict[str, Any]: 包含完整处理结果的字典
        """
        uid = request_data.get("uid")
        
        logger.info(f"⚡ 开始并行核心流程处理: {uid}")
        
        flow_context = {
            **request_data,
            "flow_start_time": datetime.now(),
            "flow_errors": []
        }
        
        try:
            # 阶段1: Profile加载（必须先执行）
            enhanced_data = await self.load_profile.process(flow_context)
            
            # 阶段2: 对话处理（依赖Profile数据）
            completion_data = await self.chat_processor.process(enhanced_data)
            
            # 阶段3: 并行执行存储任务
            # 注意：这里可以将存储任务分解为多个独立的并行任务
            storage_tasks = [
                self._store_conversation_history(completion_data),
                self._update_profile_data(completion_data),
                self._cleanup_and_analytics(completion_data)
            ]
            
            storage_results = await asyncio.gather(*storage_tasks, return_exceptions=True)
            
            # 处理存储结果
            storage_errors = [r for r in storage_results if isinstance(r, Exception)]
            if storage_errors:
                logger.warning(f"部分并行存储任务失败: {[str(e) for e in storage_errors]}")
            
            # 构建最终结果
            flow_duration = (datetime.now() - flow_context["flow_start_time"]).total_seconds()
            
            final_result = {
                **completion_data,
                "flow_duration": flow_duration,
                "parallel_storage_errors": [str(e) for e in storage_errors] if storage_errors else None,
                "flow_completed": True,
                "status": create_status_info(
                    ChatStatus.COMPLETED,
                    message=f"客户 {uid} 的并行处理完成",
                    progress=1.0
                )
            }
            
            logger.info(f"⚡ 并行核心流程完成: {uid}, 耗时: {flow_duration:.2f}s")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ 并行核心流程失败 {uid}: {str(e)}")
            
            flow_duration = (datetime.now() - flow_context["flow_start_time"]).total_seconds()
            
            return {
                **flow_context,
                "flow_duration": flow_duration,
                "flow_error": str(e),
                "flow_completed": False,
                "status": create_status_info(
                    ChatStatus.ERROR,
                    message=f"客户 {uid} 的并行处理失败: {str(e)}",
                    error_details=str(e)
                )
            }
    
    async def _store_conversation_history(self, completion_data: Dict[str, Any]):
        """并行任务：存储对话历史"""
        try:
            # 这里可以复用StoreProfile中的方法或者独立实现
            store_profile = StoreProfile()
            await store_profile._store_conversation_history(
                await store_profile._get_redis_client(), 
                completion_data
            )
            
        except Exception as e:
            logger.error(f"对话历史存储失败: {str(e)}")
            raise
    
    async def _update_profile_data(self, completion_data: Dict[str, Any]):
        """并行任务：更新Profile数据"""
        try:
            store_profile = StoreProfile()
            redis_client = await store_profile._get_redis_client()
            
            # 并行执行Profile相关更新
            tasks = [
                store_profile._update_customer_profile(redis_client, completion_data),
                store_profile._update_customer_memory(redis_client, completion_data),
                store_profile._update_customer_preferences(redis_client, completion_data)
            ]
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Profile数据更新失败: {str(e)}")
            raise
    
    async def _cleanup_and_analytics(self, completion_data: Dict[str, Any]):
        """并行任务：清理和分析"""
        try:
            store_profile = StoreProfile()
            redis_client = await store_profile._get_redis_client()
            
            # 并行执行清理和统计任务
            tasks = [
                store_profile._record_usage_statistics(redis_client, completion_data),
                store_profile._cleanup_old_data(redis_client, completion_data.get("uid"))
            ]
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"清理和分析任务失败: {str(e)}")
            raise


# 工厂函数
def create_core_flow(parallel: bool = False) -> CoreFlow:
    """
    创建核心流程处理器
    
    Args:
        parallel: 是否使用并行模式
        
    Returns:
        CoreFlow: 核心流程处理器实例
    """
    if parallel:
        return ParallelCoreFlow()
    else:
        return CoreFlow()


# 便捷函数
async def process_chat_request(request_data: Dict[str, Any], parallel: bool = False) -> Dict[str, Any]:
    """
    便捷的对话请求处理函数
    
    Args:
        request_data: 请求数据
        parallel: 是否使用并行模式
        
    Returns:
        Dict[str, Any]: 处理结果
    """
    core_flow = create_core_flow(parallel=parallel)
    return await core_flow.run(request_data) 