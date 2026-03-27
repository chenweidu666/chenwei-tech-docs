#!/usr/bin/env python3
"""
MyGPU Ops Demo 安装脚本

这个脚本展示如何打包一个包含 C++ 扩展的 Python 包。

安装方式:
    pip install -e .                    # 开发模式安装
    pip install -e . --verbose          # 查看编译详情
    MYGPU_NO_CPP=1 pip install -e .     # 跳过 C++ 编译 (纯 Python 模式)

编译依赖:
    - PyTorch >= 2.0.0
    - C++17 兼容编译器 (g++ >= 7, clang++ >= 5)
"""

import os
import sys
from pathlib import Path

from setuptools import setup, find_packages

# =============================================================================
# C++ 扩展配置
# =============================================================================

# 检查是否跳过 C++ 编译
SKIP_CPP_EXTENSION = os.environ.get("MYGPU_NO_CPP", "0") == "1"

ext_modules = []
cmdclass = {}

if not SKIP_CPP_EXTENSION:
    try:
        from torch.utils.cpp_extension import CppExtension, BuildExtension
        
        # C++ 源文件列表
        cpp_sources = [
            "csrc/mygpu_ops.cpp",           # pybind11 入口
            "csrc/ops/rms_norm.cpp",        # RMSNorm 实现
            "csrc/ops/rotary_embedding.cpp", # RoPE 实现
            "csrc/ops/attention.cpp",        # Attention 实现
        ]
        
        # 头文件目录
        include_dirs = [
            "csrc/include",
        ]
        
        # 编译选项
        extra_compile_args = {
            "cxx": [
                "-std=c++17",       # C++17 标准
                "-O3",              # 最高优化级别
                "-ffast-math",      # 快速数学运算
                "-fPIC",            # 位置无关代码
                "-Wall",            # 所有警告
            ],
        }
        
        # 定义 C++ 扩展模块
        # 编译后生成 mygpu_ops/_C.so (Linux) 或 _C.pyd (Windows)
        cpp_extension = CppExtension(
            name="mygpu_ops._C",              # Python 导入路径
            sources=cpp_sources,
            include_dirs=include_dirs,
            extra_compile_args=extra_compile_args,
            language="c++",
        )
        
        ext_modules = [cpp_extension]
        cmdclass = {"build_ext": BuildExtension}
        
        print("=" * 60)
        print("MyGPU Ops: 将编译 C++ 扩展")
        print(f"  源文件: {cpp_sources}")
        print("=" * 60)
        
    except ImportError:
        print("=" * 60)
        print("警告: PyTorch 未安装或版本过低")
        print("       将安装纯 Python 版本 (无 C++ 加速)")
        print("=" * 60)
        SKIP_CPP_EXTENSION = True
else:
    print("=" * 60)
    print("MyGPU Ops: 跳过 C++ 扩展编译 (MYGPU_NO_CPP=1)")
    print("           将使用纯 Python 实现")
    print("=" * 60)


# =============================================================================
# 读取 README
# =============================================================================

readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""


# =============================================================================
# Setup 配置
# =============================================================================

setup(
    name="mygpu-ops-demo",
    version="0.1.0",
    author="MyGPU Team",
    author_email="demo@mygpu.ai",
    description="模拟国产GPU算子库与vLLM CustomOp集成演示 (含C++实现)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/mygpu-ops-demo",
    
    packages=find_packages(),
    
    # C++ 扩展
    ext_modules=ext_modules,
    cmdclass=cmdclass,
    
    python_requires=">=3.8",
    
    install_requires=[
        "torch>=2.0.0",
    ],
    
    extras_require={
        "dev": [
            "pytest",
            "black",
            "mypy",
        ],
    },
    
    # vLLM Platform Plugin 入口点
    entry_points={
        "vllm.platform": [
            "mygpu = vllm_plugin:MyGPUPlatform",
        ],
    },
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
