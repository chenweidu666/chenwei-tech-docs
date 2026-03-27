"""
CustomOp 基类定义

这个模块定义了CustomOp的基类，模拟vLLM的CustomOp接口。
在实际vLLM中，这个基类来自 vllm.model_executor.layers.ops
"""

import torch
from typing import Optional, Any, Callable
from abc import ABC, abstractmethod
import functools


class CustomOp(ABC):
    """
    自定义算子基类
    
    这是vLLM CustomOp机制的核心。每个自定义算子都需要继承这个类，
    并实现forward_native和forward_oot两个方法。
    
    调用流程：
    1. __call__ 被调用
    2. 检查 is_oot_supported() 
    3. 如果支持OOT：调用 forward_oot()
    4. 否则：调用 forward_native()
    
    这种设计允许：
    - 在不同硬件上使用不同实现
    - 在没有硬件支持时优雅降级
    - 方便调试（可以对比native和oot的结果）
    """
    
    # 类级别的OOT支持标志
    # 子类可以覆盖这个属性
    _oot_supported: bool = True
    
    def __init__(self):
        """初始化"""
        # 检查模拟算子库是否可用
        self._check_mygpu_available()
    
    def _check_mygpu_available(self) -> bool:
        """检查MyGPU算子库是否可用"""
        try:
            import mygpu_ops
            return mygpu_ops.is_available()
        except ImportError:
            return False
    
    @classmethod
    def is_oot_supported(cls) -> bool:
        """
        检查是否支持Out-of-Tree实现
        
        这个方法用于运行时判断是否应该使用OOT实现。
        子类可以覆盖这个方法来添加更复杂的检查逻辑。
        
        Returns:
            True 如果支持OOT实现，否则False
        """
        return cls._oot_supported
    
    @abstractmethod
    def forward_native(self, *args, **kwargs) -> Any:
        """
        PyTorch原生实现
        
        这是fallback实现，使用纯PyTorch操作。
        当OOT实现不可用时会调用这个方法。
        
        优点：
        - 跨平台兼容
        - 方便调试
        - 可以作为正确性验证的基准
        
        缺点：
        - 性能不如优化的kernel
        - 内存效率可能较低
        """
        raise NotImplementedError("forward_native must be implemented")
    
    @abstractmethod
    def forward_oot(self, *args, **kwargs) -> Any:
        """
        Out-of-Tree实现
        
        调用自研算子库的实现。
        这是性能关键路径，应该使用高度优化的kernel。
        
        OOT = Out-of-Tree，表示这个实现不在PyTorch主代码树中，
        而是由第三方（如国产GPU厂商）提供。
        
        实现要求：
        - 调用mygpu_ops中的对应函数
        - 处理好内存布局和数据类型转换
        - 保证与forward_native的数值一致性
        """
        raise NotImplementedError("forward_oot must be implemented")
    
    def forward(self, *args, **kwargs) -> Any:
        """
        前向传播入口
        
        根据OOT支持情况选择实现。
        """
        if self.is_oot_supported():
            return self.forward_oot(*args, **kwargs)
        else:
            return self.forward_native(*args, **kwargs)
    
    def __call__(self, *args, **kwargs) -> Any:
        """使算子可调用"""
        return self.forward(*args, **kwargs)
    
    def debug_compare(self, *args, **kwargs) -> dict:
        """
        调试辅助：比较native和oot实现的结果
        
        用于验证OOT实现的正确性。
        
        Returns:
            包含比较结果的字典
        """
        # 运行native实现
        native_result = self.forward_native(*args, **kwargs)
        
        # 运行oot实现
        oot_result = self.forward_oot(*args, **kwargs)
        
        # 比较结果
        if isinstance(native_result, torch.Tensor):
            native_tensors = [native_result]
            oot_tensors = [oot_result]
        elif isinstance(native_result, tuple):
            native_tensors = [t for t in native_result if isinstance(t, torch.Tensor)]
            oot_tensors = [t for t in oot_result if isinstance(t, torch.Tensor)]
        else:
            return {"error": "Unsupported return type"}
        
        comparisons = []
        for i, (nat, oot) in enumerate(zip(native_tensors, oot_tensors)):
            diff = torch.abs(nat - oot)
            comparisons.append({
                "tensor_index": i,
                "shape": list(nat.shape),
                "dtype": str(nat.dtype),
                "max_diff": diff.max().item(),
                "mean_diff": diff.mean().item(),
                "allclose_1e-5": torch.allclose(nat, oot, rtol=1e-5, atol=1e-5),
                "allclose_1e-3": torch.allclose(nat, oot, rtol=1e-3, atol=1e-3),
            })
        
        return {
            "num_tensors": len(comparisons),
            "comparisons": comparisons,
            "all_match_1e-5": all(c["allclose_1e-5"] for c in comparisons),
            "all_match_1e-3": all(c["allclose_1e-3"] for c in comparisons),
        }


class CustomOpWithWeights(CustomOp):
    """
    带权重的CustomOp
    
    继承自CustomOp，增加了权重管理功能。
    用于需要持久化权重的算子（如LayerNorm）。
    """
    
    def __init__(self):
        super().__init__()
        self._weights_initialized = False
    
    def initialize_weights(self, **kwargs) -> None:
        """
        初始化权重
        
        子类应该覆盖这个方法来设置权重。
        """
        self._weights_initialized = True
    
    def get_weights(self) -> dict:
        """
        获取权重字典
        
        Returns:
            权重名称到张量的映射
        """
        return {}


def use_native_if_debug(func: Callable) -> Callable:
    """
    装饰器：在调试模式下使用native实现
    
    用法：
        @use_native_if_debug
        def forward_oot(self, ...):
            ...
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        import os
        if os.environ.get("MYGPU_DEBUG", "0") == "1":
            return self.forward_native(*args, **kwargs)
        return func(self, *args, **kwargs)
    return wrapper
