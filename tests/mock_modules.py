"""
模拟模块
为测试提供模拟的数据处理和数据源组件
确保测试能够独立运行，不依赖于实际的外部API
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import json

class MockSessionNormalizer:
    """模拟会话数据标准化器"""
    
    def normalize(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化会话数据"""
        if data is None or data.empty:
            return pd.DataFrame()
        
        result = data.copy()
        
        # 移除异常数据
        result = result[result['open'] > 0]
        result = result[result['high'] > 0]
        result = result[result['low'] > 0]
        result = result[result['close'] > 0]
        result = result[result['volume'] >= 0]
        
        # 修复价格关系
        result['high'] = np.maximum.reduce([result['open'], result['close'], result['high']])
        result['low'] = np.minimum.reduce([result['open'], result['close'], result['low']])
        
        # 移除重复数据
        if 'datetime' in result.columns:
            result = result.drop_duplicates(subset=['symbol', 'datetime'])
        
        return result

class MockPriceAdjuster:
    """模拟价格调整器"""
    
    def adjust_pre_close(self, data: pd.DataFrame) -> pd.DataFrame:
        """调整前收盘价"""
        if data is None or data.empty:
            return pd.DataFrame()
        
        result = data.copy()
        
        # 如果没有前收盘价，用上一日收盘价填充
        if 'pre_close' not in result.columns:
            result['pre_close'] = result['close'].shift(1)
        
        # 处理复权因子
        if 'adj_factor' in result.columns:
            result['pre_close'] = result['pre_close'] * result['adj_factor']
        
        # 填充首日前收盘价
        if not result.empty and pd.isna(result.iloc[0]['pre_close']):
            result.iloc[0, result.columns.get_loc('pre_close')] = result.iloc[0]['open']
        
        return result

class MockSymbolMapper:
    """模拟股票代码映射器"""
    
    def __init__(self):
        self.mapping_rules = {
            # 深交所股票
            r'^000\d{3}$': '.SZ',
            r'^300\d{3}$': '.SZ',
            r'^002\d{3}$': '.SZ',
            
            # 上交所股票
            r'^60\d{4}$': '.SH',
            r'^688\d{3}$': '.SH',
            
            # 港股
            r'^\d{4}\.HK$': '.HK',
            
            # 美股（不需要后缀）
            r'^[A-Z]{1,5}$': ''
        }
    
    def map_symbol(self, symbol: str) -> str:
        """映射股票代码"""
        if not symbol:
            return symbol
        
        symbol = symbol.upper().strip()
        
        # 如果已经有后缀，直接返回
        if '.' in symbol:
            return symbol
        
        # 应用映射规则
        import re
        for pattern, suffix in self.mapping_rules.items():
            if re.match(pattern, symbol):
                return symbol + suffix
        
        # 默认返回原始代码
        return symbol

class MockDataCache:
    """模拟数据缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self.default_ttl = 3600  # 1小时
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._timestamps:
            age = (datetime.now() - self._timestamps[key]).total_seconds()
            if age > self.default_ttl:
                del self._cache[key]
                del self._timestamps[key]
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存数据"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        
        if ttl is not None:
            # 可以实现自定义TTL，这里简化处理
            pass
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)

class MockAkshareSource:
    """模拟Akshare数据源"""
    
    def __init__(self):
        self.rate_limit_delay = 1.0  # 模拟限流
        self.last_request_time = 0
    
    def _generate_mock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟数据"""
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        # 只保留交易日（简化处理，排除周末）
        dates = [d for d in dates if d.weekday() < 5]
        
        if len(dates) == 0:
            return pd.DataFrame()
        
        # 生成价格走势（随机游走）
        np.random.seed(hash(symbol) % 2**32)  # 确保同一股票数据一致
        base_price = np.random.uniform(10, 50)
        price_changes = np.random.normal(0, 0.02, len(dates))  # 2%波动率
        prices = base_price * np.exp(np.cumsum(price_changes))
        
        data = []
        for i, date in enumerate(dates):
            close_price = prices[i]
            open_price = close_price * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            volume = np.random.randint(1000000, 50000000)
            amount = volume * close_price * np.random.uniform(0.8, 1.2)
            
            data.append({
                'symbol': symbol,
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume,
                'amount': round(amount, 2)
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def fetch_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票数据"""
        # 模拟限流
        current_time = time.time()
        if current_time - self.last_request_time < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - (current_time - self.last_request_time))
        self.last_request_time = time.time()
        
        # 模拟网络延迟
        time.sleep(np.random.uniform(0.1, 0.5))
        
        # 模拟偶发错误（5%概率）
        if np.random.random() < 0.05:
            raise ConnectionError("模拟网络连接错误")
        
        return self._generate_mock_data(symbol, start_date, end_date)

class MockTushareSource:
    """模拟Tushare数据源"""
    
    def __init__(self, token: str = "mock_token"):
        self.token = token
        self.daily_limit = 5000  # 模拟每日调用限制
        self.used_calls = 0
        self.reset_date = datetime.now().date()
    
    def _check_quota(self):
        """检查调用配额"""
        current_date = datetime.now().date()
        if current_date != self.reset_date:
            self.used_calls = 0
            self.reset_date = current_date
        
        if self.used_calls >= self.daily_limit:
            raise Exception("Tushare API调用次数已达每日限制")
        
        self.used_calls += 1
    
    def _tushare_to_standard_format(self, data: pd.DataFrame) -> pd.DataFrame:
        """转换Tushare格式到标准格式"""
        if data.empty:
            return data
        
        # Tushare使用不同的列名
        column_mapping = {
            'ts_code': 'symbol',
            'trade_date': 'date',
            'vol': 'volume'
        }
        
        result = data.rename(columns=column_mapping)
        
        # 转换日期格式
        if 'date' in result.columns:
            result['date'] = pd.to_datetime(result['date'], format='%Y%m%d')
        
        # 转换股票代码格式
        if 'symbol' in result.columns:
            result['symbol'] = result['symbol'].apply(lambda x: x.replace('.SH', '.SH').replace('.SZ', '.SZ'))
        
        return result
    
    def fetch_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票数据"""
        self._check_quota()
        
        # 模拟网络延迟
        time.sleep(np.random.uniform(0.2, 0.8))
        
        # 生成模拟数据（格式稍有不同）
        mock_source = MockAkshareSource()
        data = mock_source._generate_mock_data(symbol, start_date, end_date)
        
        if not data.empty:
            # 转换为Tushare格式
            data['ts_code'] = symbol
            data['trade_date'] = data['date'].dt.strftime('%Y%m%d')
            data['vol'] = data['volume']
            data = data.drop(['symbol', 'date', 'volume'], axis=1)
            
            # 再转换回标准格式
            data = self._tushare_to_standard_format(data)
        
        return data

class MockDataMerger:
    """模拟数据合并器"""
    
    def merge_with_fallback(self, sources: List[Dict]) -> pd.DataFrame:
        """合并多个数据源，支持回退机制"""
        if not sources:
            return pd.DataFrame()
        
        # 按优先级排序
        sources = sorted(sources, key=lambda x: x.get('priority', 999))
        
        merged_data = pd.DataFrame()
        coverage_dates = set()
        
        for source in sources:
            source_data = source.get('data', pd.DataFrame())
            if source_data.empty:
                continue
            
            if merged_data.empty:
                merged_data = source_data.copy()
                if 'date' in merged_data.columns:
                    coverage_dates = set(merged_data['date'].dt.date)
            else:
                # 找出缺失的日期
                if 'date' in source_data.columns:
                    source_dates = set(source_data['date'].dt.date)
                    missing_dates = source_dates - coverage_dates
                    
                    if missing_dates:
                        # 添加缺失日期的数据
                        missing_data = source_data[source_data['date'].dt.date.isin(missing_dates)]
                        merged_data = pd.concat([merged_data, missing_data], ignore_index=True)
                        coverage_dates.update(missing_dates)
        
        # 排序并去重
        if not merged_data.empty and 'date' in merged_data.columns:
            merged_data = merged_data.sort_values('date').reset_index(drop=True)
            merged_data = merged_data.drop_duplicates(subset=['symbol', 'date'], keep='first')
        
        return merged_data

class MockZiplineIngester:
    """模拟Zipline数据摄入器"""
    
    def __init__(self):
        self.ingested_data = {}
        self.bundle_name = "mock_bundle"
    
    def ingest_data(self, data: pd.DataFrame) -> bool:
        """摄入数据到Zipline"""
        try:
            if data is None or data.empty:
                return False
            
            # 验证数据格式
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in data.columns]
                raise ValueError(f"数据缺少必要列: {missing_cols}")
            
            # 模拟数据转换过程
            zipline_data = data.copy()
            
            # 设置索引
            if 'date' in zipline_data.columns:
                zipline_data = zipline_data.set_index('date')
            
            # 验证价格数据
            if (zipline_data['high'] < zipline_data['low']).any():
                raise ValueError("数据质量检查失败: high < low")
            
            # 模拟摄入过程
            time.sleep(0.1)  # 模拟处理时间
            
            # 存储到模拟的bundle中
            symbol = zipline_data['symbol'].iloc[0] if 'symbol' in zipline_data.columns else 'UNKNOWN'
            self.ingested_data[symbol] = zipline_data
            
            return True
            
        except Exception as e:
            print(f"Zipline摄入失败: {e}")
            return False
    
    def get_ingested_symbols(self) -> List[str]:
        """获取已摄入的股票代码"""
        return list(self.ingested_data.keys())
    
    def get_ingested_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取已摄入的数据"""
        return self.ingested_data.get(symbol)

class MockAlgoRunner:
    """模拟算法运行器"""
    
    def __init__(self):
        self.available_algorithms = {
            'buy_and_hold': self._buy_and_hold_strategy,
            'moving_average': self._moving_average_strategy,
            'mean_reversion': self._mean_reversion_strategy,
            'test_strategy': self._test_strategy
        }
    
    def _buy_and_hold_strategy(self, config: Dict) -> Dict:
        """买入持有策略"""
        # 模拟简单的买入持有回测
        np.random.seed(42)
        total_return = np.random.normal(0.08, 0.15)  # 平均8%收益，15%波动
        sharpe_ratio = np.random.normal(0.6, 0.3)
        max_drawdown = -abs(np.random.normal(0.15, 0.1))
        volatility = abs(np.random.normal(0.18, 0.05))
        
        return {
            'total_returns': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'trades': 2,  # 买入和卖出
            'win_rate': 1.0 if total_return > 0 else 0.0
        }
    
    def _moving_average_strategy(self, config: Dict) -> Dict:
        """移动平均策略"""
        np.random.seed(123)
        total_return = np.random.normal(0.12, 0.20)
        sharpe_ratio = np.random.normal(0.8, 0.4)
        max_drawdown = -abs(np.random.normal(0.12, 0.08))
        volatility = abs(np.random.normal(0.16, 0.04))
        
        return {
            'total_returns': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'trades': np.random.randint(10, 50),
            'win_rate': np.random.uniform(0.4, 0.7)
        }
    
    def _mean_reversion_strategy(self, config: Dict) -> Dict:
        """均值回归策略"""
        np.random.seed(456)
        total_return = np.random.normal(0.06, 0.18)
        sharpe_ratio = np.random.normal(0.4, 0.5)
        max_drawdown = -abs(np.random.normal(0.20, 0.12))
        volatility = abs(np.random.normal(0.22, 0.06))
        
        return {
            'total_returns': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'trades': np.random.randint(20, 100),
            'win_rate': np.random.uniform(0.3, 0.6)
        }
    
    def _test_strategy(self, config: Dict) -> Dict:
        """测试策略"""
        return {
            'total_returns': 0.10,
            'sharpe_ratio': 1.5,
            'max_drawdown': -0.08,
            'volatility': 0.15,
            'trades': 5,
            'win_rate': 0.6
        }
    
    def run_backtest(self, config: Dict) -> Dict:
        """运行回测"""
        algo_name = config.get('name', 'test_strategy')
        
        if algo_name not in self.available_algorithms:
            algo_name = 'test_strategy'
        
        try:
            # 模拟回测运行时间
            time.sleep(np.random.uniform(0.1, 0.3))
            
            # 运行策略
            result = self.available_algorithms[algo_name](config)
            
            # 添加通用字段
            result.update({
                'algorithm': algo_name,
                'start_date': config.get('start_date', '2024-01-01'),
                'end_date': config.get('end_date', '2024-01-31'),
                'initial_capital': config.get('initial_capital', 100000),
                'symbols': config.get('symbols', ['000001.SZ'])
            })
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'total_returns': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'volatility': 0.0
            }
    
    def get_available_algorithms(self) -> List[str]:
        """获取可用算法列表"""
        return list(self.available_algorithms.keys())

# 模拟模块工厂
class MockModuleFactory:
    """模拟模块工厂，用于创建所需的模拟对象"""
    
    @staticmethod
    def create_session_normalizer():
        return MockSessionNormalizer()
    
    @staticmethod
    def create_price_adjuster():
        return MockPriceAdjuster()
    
    @staticmethod
    def create_symbol_mapper():
        return MockSymbolMapper()
    
    @staticmethod
    def create_data_cache():
        return MockDataCache()
    
    @staticmethod
    def create_akshare_source():
        return MockAkshareSource()
    
    @staticmethod
    def create_tushare_source(token: str = "mock_token"):
        return MockTushareSource(token)
    
    @staticmethod
    def create_data_merger():
        return MockDataMerger()
    
    @staticmethod
    def create_zipline_ingester():
        return MockZiplineIngester()
    
    @staticmethod
    def create_algo_runner():
        return MockAlgoRunner()

# 模拟数据生成器
class MockDataGenerator:
    """模拟数据生成器，用于生成各种测试数据"""
    
    @staticmethod
    def generate_stock_data(symbol: str, start_date: str, end_date: str, 
                          price_range: tuple = (10, 50), volatility: float = 0.02) -> pd.DataFrame:
        """生成股票数据"""
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = [d for d in dates if d.weekday() < 5]  # 只保留工作日
        
        if len(dates) == 0:
            return pd.DataFrame()
        
        np.random.seed(hash(symbol) % 2**32)
        base_price = np.random.uniform(*price_range)
        price_changes = np.random.normal(0, volatility, len(dates))
        prices = base_price * np.exp(np.cumsum(price_changes))
        
        data = []
        for i, date in enumerate(dates):
            close_price = prices[i]
            open_price = close_price * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            volume = np.random.randint(1000000, 50000000)
            
            data.append({
                'symbol': symbol,
                'datetime': date,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume,
                'amount': round(volume * close_price * np.random.uniform(0.8, 1.2), 2)
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_corrupted_data(normal_data: pd.DataFrame, corruption_rate: float = 0.1) -> pd.DataFrame:
        """生成包含错误的数据"""
        if normal_data.empty:
            return normal_data
        
        corrupted = normal_data.copy()
        n_corruptions = int(len(corrupted) * corruption_rate)
        
        for _ in range(n_corruptions):
            idx = np.random.randint(0, len(corrupted))
            corruption_type = np.random.choice(['negative_price', 'high_low_invert', 'missing_volume', 'extreme_price'])
            
            if corruption_type == 'negative_price':
                corrupted.iloc[idx, corrupted.columns.get_loc('open')] = -abs(corrupted.iloc[idx]['open'])
            elif corruption_type == 'high_low_invert':
                high_val = corrupted.iloc[idx]['high']
                low_val = corrupted.iloc[idx]['low']
                corrupted.iloc[idx, corrupted.columns.get_loc('high')] = low_val
                corrupted.iloc[idx, corrupted.columns.get_loc('low')] = high_val
            elif corruption_type == 'missing_volume':
                corrupted.iloc[idx, corrupted.columns.get_loc('volume')] = np.nan
            elif corruption_type == 'extreme_price':
                corrupted.iloc[idx, corrupted.columns.get_loc('close')] *= np.random.choice([100, 0.01])
        
        return corrupted

if __name__ == "__main__":
    # 测试模拟模块
    print("测试模拟模块...")
    
    # 测试数据生成
    generator = MockDataGenerator()
    test_data = generator.generate_stock_data("000001.SZ", "2024-01-01", "2024-01-10")
    print(f"✅ 生成测试数据: {len(test_data)}行")
    
    # 测试各个模拟组件
    factory = MockModuleFactory()
    
    # 测试数据源
    akshare = factory.create_akshare_source()
    data = akshare.fetch_stock_data("000001.SZ", "2024-01-01", "2024-01-05")
    print(f"✅ Akshare模拟数据: {len(data)}行")
    
    # 测试数据处理
    normalizer = factory.create_session_normalizer()
    normalized = normalizer.normalize(test_data)
    print(f"✅ 数据标准化: {len(normalized)}行")
    
    # 测试算法运行
    algo_runner = factory.create_algo_runner()
    result = algo_runner.run_backtest({'name': 'test_strategy'})
    print(f"✅ 算法测试: 收益率 {result['total_returns']:.2%}")
    
    print("模拟模块测试完成!")