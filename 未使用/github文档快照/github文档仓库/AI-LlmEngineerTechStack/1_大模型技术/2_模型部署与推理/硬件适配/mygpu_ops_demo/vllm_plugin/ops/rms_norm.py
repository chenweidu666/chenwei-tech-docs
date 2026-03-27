"""
RMSNorm CustomOp Implementation

这个模块展示如何将RMSNorm算子包装成vLLM CustomOp。
包括标准RMSNorm和融合版本。
"""

import torch
from typing import Tuple, Optional

from .base import CustomOp, use_native_if_debug

# 导入路径处理（支持从项目目录导入mygpu_ops）
import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))


class MyGPURMSNorm(CustomOp):
    """
    MyGPU RMSNorm CustomOp
    
    这是vLLM CustomOp的标准实现模式：
    1. __init__: 存储配置参数
    2. forward_native: PyTorch原生实现
    3. forward_oot: 调用mygpu_ops实现
    
    使用示例：
        # 创建算子
        rms_norm = MyGPURMSNorm(hidden_size=4096, eps=1e-6)
        
        # 准备输入
        x = torch.randn(2, 128, 4096, dtype=torch.float16, device='cuda')
        weight = torch.ones(4096, dtype=torch.float16, device='cuda')
        
        # 调用（自动选择实现）
        output = rms_norm(x, weight)
    """
    
    def __init__(
        self,
        hidden_size: int,
        eps: float = 1e-6,
    ):
        """
        初始化RMSNorm
        
        Args:
            hidden_size: 隐藏层大小
            eps: 防止除零的小常数
        """
        super().__init__()
        self.hidden_size = hidden_size
        self.eps = eps
    
    def forward_native(
        self,
        x: torch.Tensor,
        weight: torch.Tensor,
    ) -> torch.Tensor:
        """
        PyTorch原生实现
        
        这是fallback实现，当mygpu_ops不可用时使用。
        
        数学公式：
            output = x / sqrt(mean(x^2) + eps) * weight
        
        Args:
            x: 输入张量, shape [..., hidden_size]
            weight: 归一化权重, shape [hidden_size]
        
        Returns:
            归一化后的张量
        """
        # 计算方差
        variance = x.pow(2).mean(dim=-1, keepdim=True)
        
        # 归一化
        x_normed = x * torch.rsqrt(variance + self.eps)
        
        # 乘以权重
        output = x_normed * weight
        
        return output
    
    @use_native_if_debug
    def forward_oot(
        self,
        x: torch.Tensor,
        weight: torch.Tensor,
    ) -> torch.Tensor:
        """
        Out-of-Tree实现 - 调用mygpu_ops
        
        这是性能关键路径！
        在实际场景中，这里调用的是高度优化的GPU kernel。
        
        Args:
            x: 输入张量
            weight: 权重张量
        
        Returns:
            归一化后的张量
        """
        # ========== 这是关键！调用自研算子库 ==========
        import mygpu_ops
        
        return mygpu_ops.rms_norm(x, weight, self.eps)
    
    def __repr__(self) -> str:
        return f"MyGPURMSNorm(hidden_size={self.hidden_size}, eps={self.eps})"


class MyGPUFusedAddRMSNorm(CustomOp):
    """
    MyGPU Fused Add + RMSNorm CustomOp
    
    融合残差加法和RMSNorm，减少显存访问次数。
    
    公式：
        hidden = x + residual
        output = RMSNorm(hidden) * weight
    
    使用示例：
        fused_norm = MyGPUFusedAddRMSNorm(hidden_size=4096, eps=1e-6)
        output, new_residual = fused_norm(x, residual, weight)
    """
    
    def __init__(
        self,
        hidden_size: int,
        eps: float = 1e-6,
    ):
        """初始化"""
        super().__init__()
        self.hidden_size = hidden_size
        self.eps = eps
    
    def forward_native(
        self,
        x: torch.Tensor,
        residual: torch.Tensor,
        weight: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        PyTorch原生实现
        
        Args:
            x: 输入张量
            residual: 残差张量
            weight: 权重张量
        
        Returns:
            (output, new_residual)
        """
        # 残差加法
        hidden = x + residual
        new_residual = hidden
        
        # RMSNorm
        variance = hidden.pow(2).mean(dim=-1, keepdim=True)
        hidden_normed = hidden * torch.rsqrt(variance + self.eps)
        output = hidden_normed * weight
        
        return output, new_residual
    
    @use_native_if_debug
    def forward_oot(
        self,
        x: torch.Tensor,
        residual: torch.Tensor,
        weight: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Out-of-Tree实现 - 调用mygpu_ops融合kernel
        
        融合kernel的优势：
        - 减少显存带宽压力
        - 减少kernel launch开销
        - 性能提升20-30%
        """
        import mygpu_ops
        
        return mygpu_ops.fused_add_rms_norm(x, residual, weight, self.eps)
    
    def __repr__(self) -> str:
        return f"MyGPUFusedAddRMSNorm(hidden_size={self.hidden_size}, eps={self.eps})"


# ============================================================================
# 工厂函数
# ============================================================================

def create_rms_norm(
    hidden_size: int,
    eps: float = 1e-6,
    use_fused: bool = False,
) -> CustomOp:
    """
    创建RMSNorm算子的工厂函数
    
    Args:
        hidden_size: 隐藏层大小
        eps: 防止除零
        use_fused: 是否使用融合版本（需要配合残差使用）
    
    Returns:
        RMSNorm CustomOp实例
    """
    if use_fused:
        return MyGPUFusedAddRMSNorm(hidden_size=hidden_size, eps=eps)
    else:
        return MyGPURMSNorm(hidden_size=hidden_size, eps=eps)
