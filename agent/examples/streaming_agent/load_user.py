#!/usr/bin/env python3
"""
用户管理模块 - 负责用户并发控制和状态管理
"""

import asyncio
from typing import Set
from datetime import datetime

class UserManager:
    """用户状态管理器"""
    
    def __init__(self):
        # 正在处理的用户ID集合
        self._processing_users: Set[str] = set()
        # 异步锁
        self._lock = asyncio.Lock()
    
    async def check_and_mark_user_processing(self, uid: str) -> bool:
        """
        检查并标记用户处理状态
        
        Args:
            uid: 用户ID
            
        Returns:
            bool: 是否可以开始处理（True=可以处理，False=已在处理中）
        """
        async with self._lock:
            if uid in self._processing_users:
                return False  # 用户已在处理中
            
            # 标记用户为正在处理
            self._processing_users.add(uid)
            print(f"🔒 用户 {uid} 开始处理")
            return True  # 可以开始处理
    
    async def unmark_user_processing(self, uid: str):
        """
        取消用户处理标记
        
        Args:
            uid: 用户ID
        """
        try:
            async with self._lock:
                self._processing_users.discard(uid)
                print(f"🔓 用户 {uid} 处理完成")
        except Exception as e:
            # 如果锁获取失败，直接操作（这是最后的保障）
            print(f"⚠️ 锁获取失败，直接移除用户 {uid}: {str(e)}")
            self._processing_users.discard(uid)
    
    async def get_processing_users(self) -> dict:
        """
        获取当前处理状态
        
        Returns:
            dict: 包含活跃用户数和用户列表的字典
        """
        async with self._lock:
            active_users = len(self._processing_users)
            users_list = list(self._processing_users)
        
        return {
            "active_users": active_users,
            "processing_users": users_list
        }
    
    def is_user_processing(self, uid: str) -> bool:
        """
        同步方法检查用户是否正在处理中
        
        Args:
            uid: 用户ID
            
        Returns:
            bool: 用户是否正在处理中
        """
        return uid in self._processing_users

# 全局用户管理器实例
user_manager = UserManager() 