"""
任务调度器
基于 APScheduler 实现定时任务调度
"""

from typing import Callable, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from config import get_config


class Scheduler:
    """任务调度器类"""
    
    def __init__(self):
        """初始化调度器"""
        self.config = get_config()
        scheduler_config = self.config.get('scheduler', {})
        
        self.scheduler = BackgroundScheduler(
            timezone=scheduler_config.get('timezone', 'Asia/Shanghai'),
            job_defaults={
                'coalesce': scheduler_config.get('coalesce', True),
                'max_instances': scheduler_config.get('max_instances', 3),
                'misfire_grace_time': scheduler_config.get('misfire_grace_time', 60)
            }
        )
        
        self.running = False
        logger.info("任务调度器初始化完成")
    
    def add_job(
        self,
        func: Callable,
        trigger_type: str,
        trigger_args: Dict[str, Any],
        job_id: str,
        name: Optional[str] = None
    ) -> bool:
        """
        添加任务
        
        Args:
            func: 任务函数
            trigger_type: 触发器类型 ('cron' / 'interval')
            trigger_args: 触发器参数
            job_id: 任务ID
            name: 任务名称
        
        Returns:
            bool: 是否成功
        """
        try:
            if trigger_type == 'cron':
                trigger = CronTrigger(**trigger_args)
            elif trigger_type == 'interval':
                trigger = IntervalTrigger(**trigger_args)
            else:
                logger.error(f"不支持的触发器类型: {trigger_type}")
                return False
            
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name or job_id,
                replace_existing=True
            )
            
            logger.info(f"任务已添加: {name or job_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加任务失败: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"任务已移除: {job_id}")
            return True
        except Exception as e:
            logger.error(f"移除任务失败: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"任务已暂停: {job_id}")
            return True
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"任务已恢复: {job_id}")
            return True
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return False
    
    def start(self):
        """启动调度器"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.success("任务调度器已启动")
    
    def shutdown(self, wait: bool = True):
        """关闭调度器"""
        if self.running:
            self.scheduler.shutdown(wait=wait)
            self.running = False
            logger.info("任务调度器已关闭")


# 全局实例
scheduler = Scheduler()
