"""
日志工具模块
提供结构化日志功能
"""

import logging
import sys
from typing import Optional
from datetime import datetime

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """获取配置好的logger实例"""
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # 避免重复添加handler
        # 设置日志级别
        log_level = getattr(logging, (level or "INFO").upper())
        logger.setLevel(log_level)
        
        # 创建console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # 创建formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # 添加handler
        logger.addHandler(console_handler)
        
        # 防止日志传播到root logger
        logger.propagate = False
    
    return logger 