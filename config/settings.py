"""
配置加载器模块
统一管理系统配置的加载和访问
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.project_root = self.config_dir.parent
        self._configs = {}
        
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        加载YAML配置文件
        
        Args:
            filename: 配置文件名（不含路径）
            
        Returns:
            配置字典
        """
        if filename in self._configs:
            return self._configs[filename]
            
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        self._configs[filename] = config
        return config
    
    def get_main_config(self) -> Dict[str, Any]:
        """获取主配置"""
        return self.load_yaml('config.yaml')
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """获取策略配置"""
        return self.load_yaml('strategy_params.yaml')
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        return self.load_yaml('ai_settings.yaml')
    
    def get_env(self, key: str, default: Any = None) -> str:
        """
        获取环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            环境变量值
        """
        return os.getenv(key, default)
    
    def get_database_path(self) -> Path:
        """获取数据库路径"""
        db_path = self.get_env('DATABASE_PATH')
        if db_path:
            return Path(db_path)
        
        # 使用配置文件中的路径
        main_config = self.get_main_config()
        db_path = main_config.get('database', {}).get('path', 'data/kline.db')
        return self.project_root / db_path
    
    def get_log_directory(self) -> Path:
        """获取日志目录"""
        log_dir = self.get_env('LOG_DIRECTORY')
        if log_dir:
            return Path(log_dir)
        return self.project_root / 'logs'
    
    def reload(self):
        """重新加载所有配置"""
        self._configs.clear()
        load_dotenv(override=True)


# 全局配置加载器实例
config_loader = ConfigLoader()


# 便捷访问函数
def get_config() -> Dict[str, Any]:
    """获取主配置"""
    return config_loader.get_main_config()


def get_strategy_config() -> Dict[str, Any]:
    """获取策略配置"""
    return config_loader.get_strategy_config()


def get_ai_config() -> Dict[str, Any]:
    """获取AI配置"""
    return config_loader.get_ai_config()


def get_env(key: str, default: Any = None) -> str:
    """获取环境变量"""
    return config_loader.get_env(key, default)


# 常用配置常量
BINANCE_API_KEY = get_env('BINANCE_API_KEY', '')
BINANCE_API_SECRET = get_env('BINANCE_API_SECRET', '')
BINANCE_TESTNET = get_env('BINANCE_TESTNET', 'true').lower() == 'true'
OPENAI_API_KEY = get_env('OPENAI_API_KEY', '')
DATABASE_PATH = str(config_loader.get_database_path())
LOG_DIRECTORY = str(config_loader.get_log_directory())
