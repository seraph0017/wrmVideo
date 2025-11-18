#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查脚本 - 检测系统环境和依赖是否满足部署要求

功能：
1. 检查操作系统和 Python 版本
2. 检查必需软件（FFmpeg、MySQL、Redis）
3. 检查 Python 依赖包
4. 检查 GPU 环境（可选）
5. 检查目录权限
6. 生成检查报告
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path
from datetime import datetime


class EnvironmentChecker:
    """环境检查器类"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system': {},
            'python': {},
            'software': {},
            'packages': {},
            'gpu': {},
            'directories': {},
            'warnings': [],
            'errors': [],
            'passed': True
        }
    
    def check_system(self):
        """检查操作系统信息"""
        print("=" * 60)
        print("检查系统环境...")
        print("=" * 60)
        
        try:
            self.results['system'] = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor()
            }
            
            print(f"✓ 操作系统: {self.results['system']['platform']} {self.results['system']['platform_release']}")
            print(f"✓ 架构: {self.results['system']['architecture']}")
            
            # 检查操作系统是否支持
            if self.results['system']['platform'] not in ['Darwin', 'Linux']:
                self.results['warnings'].append(f"不推荐的操作系统: {self.results['system']['platform']}")
                print(f"⚠ 警告: 不推荐的操作系统")
            
        except Exception as e:
            self.results['errors'].append(f"系统检查失败: {str(e)}")
            self.results['passed'] = False
            print(f"✗ 系统检查失败: {e}")
    
    def check_python(self):
        """检查 Python 版本和环境"""
        print("\n" + "=" * 60)
        print("检查 Python 环境...")
        print("=" * 60)
        
        try:
            python_version = sys.version_info
            self.results['python'] = {
                'version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                'executable': sys.executable,
                'prefix': sys.prefix
            }
            
            print(f"✓ Python 版本: {self.results['python']['version']}")
            print(f"✓ Python 路径: {self.results['python']['executable']}")
            
            # 检查版本是否满足要求
            if python_version < (3, 8):
                self.results['errors'].append(f"Python 版本过低: {self.results['python']['version']}，需要 3.8+")
                self.results['passed'] = False
                print(f"✗ Python 版本过低，需要 3.8+")
            
            # 检查是否在虚拟环境中
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            self.results['python']['in_virtualenv'] = in_venv
            
            if in_venv:
                print(f"✓ 运行在虚拟环境中")
            else:
                self.results['warnings'].append("未在虚拟环境中运行")
                print(f"⚠ 警告: 建议在虚拟环境（conda/venv）中运行")
            
        except Exception as e:
            self.results['errors'].append(f"Python 检查失败: {str(e)}")
            self.results['passed'] = False
            print(f"✗ Python 检查失败: {e}")
    
    def check_command(self, command, version_flag='--version'):
        """检查命令是否可用"""
        try:
            result = subprocess.run(
                [command, version_flag],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                return True, version
            else:
                return False, None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, None
    
    def check_software(self):
        """检查必需软件"""
        print("\n" + "=" * 60)
        print("检查必需软件...")
        print("=" * 60)
        
        software_checks = {
            'ffmpeg': {'command': 'ffmpeg', 'required': True},
            'mysql': {'command': 'mysql', 'required': False},
            'redis-server': {'command': 'redis-server', 'required': True},
            'redis-cli': {'command': 'redis-cli', 'required': True},
            'conda': {'command': 'conda', 'required': False},
        }
        
        for name, info in software_checks.items():
            available, version = self.check_command(info['command'])
            self.results['software'][name] = {
                'available': available,
                'version': version,
                'required': info['required']
            }
            
            if available:
                print(f"✓ {name}: {version}")
            else:
                if info['required']:
                    self.results['errors'].append(f"缺少必需软件: {name}")
                    self.results['passed'] = False
                    print(f"✗ {name}: 未安装（必需）")
                else:
                    self.results['warnings'].append(f"缺少可选软件: {name}")
                    print(f"⚠ {name}: 未安装（可选）")
    
    def check_python_packages(self):
        """检查 Python 依赖包"""
        print("\n" + "=" * 60)
        print("检查 Python 依赖包...")
        print("=" * 60)
        
        required_packages = [
            'django',
            'requests',
            'volcengine',
            'jinja2',
            'PIL',  # Pillow
            'celery',
            'redis',
            'jieba'
        ]
        
        for package in required_packages:
            try:
                if package == 'PIL':
                    __import__('PIL')
                    import PIL
                    version = PIL.__version__
                else:
                    module = __import__(package)
                    version = getattr(module, '__version__', 'unknown')
                
                self.results['packages'][package] = {
                    'installed': True,
                    'version': version
                }
                print(f"✓ {package}: {version}")
            except ImportError:
                self.results['packages'][package] = {
                    'installed': False,
                    'version': None
                }
                self.results['errors'].append(f"缺少 Python 包: {package}")
                self.results['passed'] = False
                print(f"✗ {package}: 未安装")
    
    def check_gpu(self):
        """检查 GPU 环境"""
        print("\n" + "=" * 60)
        print("检查 GPU 环境（可选）...")
        print("=" * 60)
        
        # 检查 nvidia-smi
        nvidia_available, nvidia_info = self.check_command('nvidia-smi')
        self.results['gpu']['nvidia_available'] = nvidia_available
        
        if nvidia_available:
            print(f"✓ NVIDIA GPU: 可用")
            self.results['gpu']['nvidia_info'] = nvidia_info
            
            # 检查 FFmpeg NVENC 支持
            try:
                result = subprocess.run(
                    ['ffmpeg', '-encoders'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                nvenc_available = 'h264_nvenc' in result.stdout
                self.results['gpu']['nvenc_available'] = nvenc_available
                
                if nvenc_available:
                    print(f"✓ FFmpeg NVENC: 支持")
                else:
                    self.results['warnings'].append("FFmpeg 不支持 NVENC 编码器")
                    print(f"⚠ FFmpeg NVENC: 不支持")
            except Exception as e:
                self.results['warnings'].append(f"无法检查 NVENC 支持: {str(e)}")
                print(f"⚠ 无法检查 NVENC 支持")
        else:
            print(f"⚠ NVIDIA GPU: 不可用（可选）")
            self.results['gpu']['nvidia_available'] = False
    
    def check_directories(self):
        """检查目录结构和权限"""
        print("\n" + "=" * 60)
        print("检查目录结构...")
        print("=" * 60)
        
        project_root = Path(__file__).parent.parent
        
        required_dirs = [
            'config',
            'data',
            'src',
            'web',
            'logs',
            'Character_Images'
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            exists = dir_path.exists()
            writable = os.access(dir_path, os.W_OK) if exists else False
            
            self.results['directories'][dir_name] = {
                'exists': exists,
                'writable': writable,
                'path': str(dir_path)
            }
            
            if exists and writable:
                print(f"✓ {dir_name}: 存在且可写")
            elif exists and not writable:
                self.results['warnings'].append(f"目录不可写: {dir_name}")
                print(f"⚠ {dir_name}: 存在但不可写")
            else:
                self.results['warnings'].append(f"目录不存在: {dir_name}")
                print(f"⚠ {dir_name}: 不存在")
        
        # 检查配置文件
        config_file = project_root / 'config' / 'config.py'
        config_exists = config_file.exists()
        self.results['directories']['config_file'] = {
            'exists': config_exists,
            'path': str(config_file)
        }
        
        if config_exists:
            print(f"✓ config.py: 存在")
        else:
            self.results['warnings'].append("配置文件不存在: config/config.py")
            print(f"⚠ config.py: 不存在（需要从 config.example.py 复制）")
    
    def check_services(self):
        """检查服务状态"""
        print("\n" + "=" * 60)
        print("检查服务状态...")
        print("=" * 60)
        
        # 检查 Redis
        try:
            result = subprocess.run(
                ['redis-cli', 'ping'],
                capture_output=True,
                text=True,
                timeout=5
            )
            redis_running = result.stdout.strip() == 'PONG'
            self.results['software']['redis_running'] = redis_running
            
            if redis_running:
                print(f"✓ Redis: 运行中")
            else:
                self.results['warnings'].append("Redis 未运行")
                print(f"⚠ Redis: 未运行")
        except Exception:
            self.results['warnings'].append("无法检查 Redis 状态")
            print(f"⚠ Redis: 无法检查状态")
        
        # 检查 MySQL
        if self.results['software'].get('mysql', {}).get('available'):
            try:
                result = subprocess.run(
                    ['mysqladmin', 'ping'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                mysql_running = result.returncode == 0
                self.results['software']['mysql_running'] = mysql_running
                
                if mysql_running:
                    print(f"✓ MySQL: 运行中")
                else:
                    self.results['warnings'].append("MySQL 未运行")
                    print(f"⚠ MySQL: 未运行")
            except Exception:
                self.results['warnings'].append("无法检查 MySQL 状态")
                print(f"⚠ MySQL: 无法检查状态")
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "=" * 60)
        print("生成检查报告...")
        print("=" * 60)
        
        # 保存 JSON 报告
        report_dir = Path(__file__).parent
        json_report = report_dir / 'environment_check_report.json'
        
        with open(json_report, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON 报告已保存: {json_report}")
        
        # 生成文本报告
        txt_report = report_dir / 'environment_check_report.txt'
        
        with open(txt_report, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("wrmVideo 环境检查报告\n")
            f.write("=" * 60 + "\n")
            f.write(f"检查时间: {self.results['timestamp']}\n")
            f.write(f"总体结果: {'通过' if self.results['passed'] else '失败'}\n")
            f.write("\n")
            
            # 系统信息
            f.write("系统信息:\n")
            f.write("-" * 60 + "\n")
            for key, value in self.results['system'].items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
            
            # Python 信息
            f.write("Python 环境:\n")
            f.write("-" * 60 + "\n")
            for key, value in self.results['python'].items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
            
            # 软件检查
            f.write("软件检查:\n")
            f.write("-" * 60 + "\n")
            for name, info in self.results['software'].items():
                if isinstance(info, dict):
                    status = "✓" if info.get('available', False) else "✗"
                    version = info.get('version', 'N/A')
                    f.write(f"  {status} {name}: {version}\n")
            f.write("\n")
            
            # Python 包
            f.write("Python 依赖包:\n")
            f.write("-" * 60 + "\n")
            for name, info in self.results['packages'].items():
                status = "✓" if info['installed'] else "✗"
                version = info.get('version', 'N/A')
                f.write(f"  {status} {name}: {version}\n")
            f.write("\n")
            
            # GPU 信息
            if self.results['gpu']:
                f.write("GPU 环境:\n")
                f.write("-" * 60 + "\n")
                for key, value in self.results['gpu'].items():
                    if key != 'nvidia_info':
                        f.write(f"  {key}: {value}\n")
                f.write("\n")
            
            # 警告
            if self.results['warnings']:
                f.write("警告信息:\n")
                f.write("-" * 60 + "\n")
                for warning in self.results['warnings']:
                    f.write(f"  ⚠ {warning}\n")
                f.write("\n")
            
            # 错误
            if self.results['errors']:
                f.write("错误信息:\n")
                f.write("-" * 60 + "\n")
                for error in self.results['errors']:
                    f.write(f"  ✗ {error}\n")
                f.write("\n")
        
        print(f"✓ 文本报告已保存: {txt_report}")
    
    def print_summary(self):
        """打印检查摘要"""
        print("\n" + "=" * 60)
        print("检查摘要")
        print("=" * 60)
        
        if self.results['passed']:
            print("✓ 环境检查通过！")
        else:
            print("✗ 环境检查失败！")
        
        print(f"\n警告数量: {len(self.results['warnings'])}")
        print(f"错误数量: {len(self.results['errors'])}")
        
        if self.results['errors']:
            print("\n需要解决的错误:")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"  {i}. {error}")
        
        if self.results['warnings']:
            print("\n建议处理的警告:")
            for i, warning in enumerate(self.results['warnings'], 1):
                print(f"  {i}. {warning}")
        
        print("\n详细报告已保存到 deploy/ 目录")
        print("=" * 60)
    
    def run(self):
        """运行所有检查"""
        self.check_system()
        self.check_python()
        self.check_software()
        self.check_python_packages()
        self.check_gpu()
        self.check_directories()
        self.check_services()
        self.generate_report()
        self.print_summary()
        
        return self.results['passed']


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("wrmVideo 环境检查工具")
    print("=" * 60 + "\n")
    
    checker = EnvironmentChecker()
    passed = checker.run()
    
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()

