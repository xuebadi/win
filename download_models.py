"""
学霸帝AI - 模型下载脚本
自动下载 Qwen3.5-2B GGUF 模型和视觉投影器

使用方法:
  python download_models.py           # 下载全部
  python download_models.py --llm    # 只下载LLM
  python download_models.py --mmproj # 只下载视觉投影器
"""
import os
import sys
import argparse
import urllib.request
from pathlib import Path

# ModelScope 直链
MODEL_URLS = {
    "llm": "https://modelscope.cn/models/unsloth/Qwen3.5-2B-GGUF/resolve/master/Qwen3.5-2B-Q4_K_M.gguf",
    "mmproj": "https://modelscope.cn/models/unsloth/Qwen3.5-2B-GGUF/resolve/master/mmproj-BF16.gguf",
}

FILE_NAMES = {
    "llm": "models/Qwen3.5-2B-Q4_K_M.gguf",
    "mmproj": "models/mmproj-BF16.gguf",
}

MODEL_REPORTED_SIZES = {
    "llm": "~1.5GB",
    "mmproj": "~300MB",
}


def download_with_progress(url: str, dest: str, description: str):
    """带进度条的下载"""
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        size_mb = dest_path.stat().st_size / 1024 / 1024
        print(f"  ✅ {dest_path.name} 已存在 ({size_mb:.1f}MB)，跳过")
        return True

    print(f"  📥 正在下载 {description}...")
    print(f"     来源: {url}")

    try:
        def report_progress(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, downloaded * 100 / total_size)
                mb_downloaded = downloaded / 1024 / 1024
                mb_total = total_size / 1024 / 1024
                bar_len = 30
                filled = int(bar_len * percent / 100)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"\r  [{bar}] {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f}MB)", end="", flush=True)

        urllib.request.urlretrieve(url, dest, reporthook=report_progress)
        print()  # 换行
        size_mb = dest_path.stat().st_size / 1024 / 1024
        print(f"  ✅ {dest_path.name} 下载完成 ({size_mb:.1f}MB)")
        return True

    except Exception as e:
        print(f"\n  ❌ 下载失败: {e}")
        if dest_path.exists():
            os.remove(dest_path)
        return False


def main():
    parser = argparse.ArgumentParser(description="下载学霸帝AI所需模型")
    parser.add_argument("--llm", action="store_true", help="只下载LLM模型")
    parser.add_argument("--mmproj", action="store_true", help="只下载视觉投影器")
    parser.add_argument("--retry", action="store_true", help="重新下载（覆盖已有文件）")
    args = parser.parse_args()

    # 删除已有文件（--retry）
    if args.retry:
        for name in FILE_NAMES.values():
            p = Path(name)
            if p.exists():
                p.unlink()
                print(f"  🗑️  已删除旧文件: {name}")

    # 确定下载哪些
    targets = []
    if args.llm:
        targets.append("llm")
    elif args.mmproj:
        targets.append("mmproj")
    else:
        targets = list(FILE_NAMES.keys())

    if not targets:
        print("⚠️  没有指定要下载的内容")
        return

    print("=" * 60)
    print("🎓 学霸帝AI - 模型下载")
    print(f"📁 模型保存目录: {Path('models').resolve()}")
    print("=" * 60)

    success_count = 0
    for target in targets:
        desc = "LLM模型 (Qwen3.5-2B Q4量化)" if target == "llm" else "视觉投影器 (mmproj)"
        print(f"\n▶ [{target.upper()}] {desc}")
        print(f"   预计大小: {MODEL_REPORTED_SIZES[target]}")
        if download_with_progress(MODEL_URLS[target], FILE_NAMES[target], desc):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"📊 完成: {success_count}/{len(targets)} 个文件下载成功")
    if success_count == len(targets):
        print("🚀 可以运行: python run.py 启动学霸帝AI")
    else:
        print("⚠️  部分文件未下载，请检查网络后重试")
        print("   重试命令: python download_models.py --retry")
    print("=" * 60)


if __name__ == "__main__":
    main()