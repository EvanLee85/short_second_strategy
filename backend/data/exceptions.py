# -*- coding: utf-8 -*-
"""
数据源异常和错误处理
---------------------------------
目标：
  - 定位问题快且不静默失败
  - 自定义 DataSourceError（含 provider、symbol、区间、root_cause）
  - 统一异常类型，便于上层统一处理和日志记录

异常层次：
  - DataSourceError: 数据源相关的基础异常
  - ProviderError: 特定提供商的错误
  - DataValidationError: 数据验证失败
  - CacheError: 缓存操作异常
  - MergeError: 多源合并异常
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 可忽略，如缓存未命中
    MEDIUM = "medium"     # 需要关注，如数据源切换
    HIGH = "high"         # 需要处理，如数据验证失败
    CRITICAL = "critical" # 需要立即处理，如所有数据源失败


@dataclass
class ErrorContext:
    """错误上下文信息"""
    provider: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    freq: Optional[str] = None
    adjust: Optional[str] = None
    operation: Optional[str] = None  # 操作类型：fetch/merge/cache/validate
    
    # 数据源统计信息
    requested_sessions: int = 0
    returned_sessions: int = 0
    missing_sessions: int = 0
    conflict_sessions: int = 0
    backfilled_sessions: int = 0
    
    # 源占比信息
    source_coverage: Dict[str, float] = field(default_factory=dict)
    primary_source: Optional[str] = None
    fallback_sources: List[str] = field(default_factory=list)
    
    # 时间信息
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于日志记录"""
        return {
            "provider": self.provider,
            "symbol": self.symbol,
            "date_range": f"{self.start_date}~{self.end_date}" if self.start_date and self.end_date else None,
            "freq": self.freq,
            "adjust": self.adjust,
            "operation": self.operation,
            "data_quality": {
                "requested_sessions": self.requested_sessions,
                "returned_sessions": self.returned_sessions,
                "missing_sessions": self.missing_sessions,
                "conflict_sessions": self.conflict_sessions,
                "backfilled_sessions": self.backfilled_sessions,
                "completeness_ratio": self.returned_sessions / max(1, self.requested_sessions),
            },
            "source_info": {
                "primary_source": self.primary_source,
                "source_coverage": self.source_coverage,
                "fallback_sources": self.fallback_sources,
            },
            "performance": {
                "timestamp": self.timestamp.isoformat(),
                "duration_ms": self.duration_ms,
            }
        }


class DataSourceError(Exception):
    """
    数据源基础异常类
    
    包含丰富的上下文信息，便于问题定位和日志分析
    """
    
    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        root_cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        **kwargs
    ):
        """
        初始化数据源异常
        
        参数:
            message: 错误描述
            provider: 数据提供商名称
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期
            root_cause: 根本原因异常
            severity: 错误严重程度
            context: 错误上下文
            **kwargs: 其他上下文信息
        """
        super().__init__(message)
        
        self.message = message
        self.provider = provider
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.root_cause = root_cause
        self.severity = severity
        
        # 构建或使用提供的上下文
        if context:
            self.context = context
        else:
            self.context = ErrorContext(
                provider=provider,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                **kwargs
            )
        
        # 如果有根本原因，记录其堆栈信息
        self.root_cause_traceback = None
        if root_cause:
            self.root_cause_traceback = traceback.format_exception(
                type(root_cause), root_cause, root_cause.__traceback__
            )
    
    def get_error_code(self) -> str:
        """生成错误代码，便于快速识别"""
        code_parts = []
        
        if self.provider:
            code_parts.append(self.provider.upper()[:3])
        
        if self.context.operation:
            code_parts.append(self.context.operation.upper()[:4])
        
        code_parts.append(self.severity.value.upper()[:3])
        
        return "_".join(code_parts) if code_parts else "UNKNOWN"
    
    def get_summary(self) -> str:
        """获取错误摘要"""
        parts = [self.message]
        
        if self.symbol:
            parts.append(f"Symbol: {self.symbol}")
        
        if self.start_date and self.end_date:
            parts.append(f"Period: {self.start_date}~{self.end_date}")
        
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        
        return " | ".join(parts)
    
    def get_detailed_info(self) -> Dict[str, Any]:
        """获取详细错误信息"""
        info = {
            "error_code": self.get_error_code(),
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context.to_dict(),
        }
        
        if self.root_cause:
            info["root_cause"] = {
                "type": type(self.root_cause).__name__,
                "message": str(self.root_cause),
                "traceback": self.root_cause_traceback,
            }
        
        return info
    
    def __str__(self) -> str:
        return f"[{self.get_error_code()}] {self.get_summary()}"


class ProviderError(DataSourceError):
    """特定数据提供商错误"""
    
    def __init__(self, message: str, provider: str, **kwargs):
        super().__init__(
            message, 
            provider=provider,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            **kwargs
        )


class DataValidationError(DataSourceError):
    """数据验证失败异常"""
    
    def __init__(
        self, 
        message: str, 
        validation_type: str,
        failed_checks: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(
            message,
            operation="validate",
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.validation_type = validation_type
        self.failed_checks = failed_checks or []
    
    def get_error_code(self) -> str:
        return f"VALIDATION_{self.validation_type.upper()}"


class CacheError(DataSourceError):
    """缓存操作异常"""
    
    def __init__(self, message: str, cache_operation: str, **kwargs):
        super().__init__(
            message,
            operation=f"cache_{cache_operation}",
            severity=ErrorSeverity.LOW,  # 缓存问题通常不是致命的
            **kwargs
        )
        self.cache_operation = cache_operation


class MergeError(DataSourceError):
    """多源合并异常"""
    
    def __init__(
        self, 
        message: str, 
        sources: List[str],
        conflicts: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message,
            operation="merge",
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.sources = sources
        self.conflicts = conflicts or 0
    
    def get_error_code(self) -> str:
        return f"MERGE_{len(self.sources)}SRC_{self.conflicts}CONF"


class NetworkError(ProviderError):
    """网络相关错误"""
    
    def __init__(self, message: str, provider: str, **kwargs):
        super().__init__(
            message,
            provider=provider,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class AuthenticationError(ProviderError):
    """认证相关错误"""
    
    def __init__(self, message: str, provider: str, **kwargs):
        super().__init__(
            message,
            provider=provider,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class RateLimitError(ProviderError):
    """限流错误"""
    
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            message,
            provider=provider,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.retry_after = retry_after


# 便捷的异常构造函数
def create_provider_error(
    provider: str,
    symbol: str,
    operation: str,
    error: Exception,
    **context_kwargs
) -> ProviderError:
    """便捷的提供商错误构造函数"""
    return ProviderError(
        f"{operation} failed for {symbol}",
        provider=provider,
        symbol=symbol,
        root_cause=error,
        operation=operation,
        **context_kwargs
    )


def create_validation_error(
    symbol: str,
    validation_type: str,
    failed_checks: List[str],
    **context_kwargs
) -> DataValidationError:
    """便捷的验证错误构造函数"""
    return DataValidationError(
        f"Data validation failed for {symbol}: {', '.join(failed_checks)}",
        symbol=symbol,
        validation_type=validation_type,
        failed_checks=failed_checks,
        **context_kwargs
    )


def create_merge_error(
    symbol: str,
    sources: List[str],
    conflicts: int,
    **context_kwargs
) -> MergeError:
    """便捷的合并错误构造函数"""
    return MergeError(
        f"Data merge failed for {symbol} across {len(sources)} sources with {conflicts} conflicts",
        symbol=symbol,
        sources=sources,
        conflicts=conflicts,
        **context_kwargs
    )


# 错误统计和分析
class ErrorCollector:
    """错误收集器，用于统计和分析错误模式"""
    
    def __init__(self):
        self.errors: List[DataSourceError] = []
    
    def add_error(self, error: DataSourceError) -> None:
        """添加错误记录"""
        self.errors.append(error)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要统计"""
        if not self.errors:
            return {"total": 0}
        
        summary = {
            "total": len(self.errors),
            "by_severity": {},
            "by_provider": {},
            "by_operation": {},
            "recent_errors": []
        }
        
        for error in self.errors:
            # 按严重程度统计
            severity = error.severity.value
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # 按提供商统计
            if error.provider:
                summary["by_provider"][error.provider] = summary["by_provider"].get(error.provider, 0) + 1
            
            # 按操作类型统计
            if error.context.operation:
                op = error.context.operation
                summary["by_operation"][op] = summary["by_operation"].get(op, 0) + 1
        
        # 最近的错误（最多5个）
        recent_errors = sorted(self.errors, key=lambda e: e.context.timestamp, reverse=True)[:5]
        summary["recent_errors"] = [
            {
                "code": error.get_error_code(),
                "message": error.message,
                "timestamp": error.context.timestamp.isoformat(),
            }
            for error in recent_errors
        ]
        
        return summary
    
    def clear(self) -> None:
        """清空错误记录"""
        self.errors.clear()


# 全局错误收集器实例
global_error_collector = ErrorCollector()


def report_error(error: DataSourceError) -> None:
    """报告错误到全局收集器"""
    global_error_collector.add_error(error)


def get_global_error_summary() -> Dict[str, Any]:
    """获取全局错误摘要"""
    return global_error_collector.get_error_summary()


# 异常装饰器
def handle_data_source_errors(
    operation: str,
    provider: Optional[str] = None,
    default_return=None
):
    """
    数据源异常处理装饰器
    
    自动捕获异常并转换为DataSourceError
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except DataSourceError:
                # 已经是数据源异常，直接重新抛出
                raise
            except Exception as e:
                # 转换为数据源异常
                error = DataSourceError(
                    f"{operation} operation failed",
                    provider=provider,
                    root_cause=e,
                    operation=operation,
                    severity=ErrorSeverity.HIGH
                )
                report_error(error)
                
                if default_return is not None:
                    return default_return
                else:
                    raise error
        
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    # 示例1：提供商错误
    try:
        raise NetworkError("连接超时", provider="akshare")
    except DataSourceError as e:
        print("错误代码:", e.get_error_code())
        print("错误摘要:", e.get_summary())
        print("详细信息:", e.get_detailed_info())
    
    # 示例2：使用便捷构造函数
    validation_error = create_validation_error(
        symbol="000001",
        validation_type="ohlc",
        failed_checks=["high < low", "negative volume"],
        provider="test"
    )
    print("\n验证错误:", validation_error)
    
    # 示例3：错误统计
    report_error(validation_error)
    print("\n全局错误摘要:", get_global_error_summary())