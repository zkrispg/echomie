import os
import shutil
from uuid import uuid4
from pathlib import Path


# 默认把存储目录放到用户目录，避免 D:\projects\backend 没写权限导致 WinError 5
DEFAULT_BASE = Path(os.getenv("USERPROFILE", ".")) / "backend-storage"

# 允许用环境变量覆盖：STORAGE_BASE_PATH
BASE_DIR = Path(os.getenv("STORAGE_BASE_PATH", str(DEFAULT_BASE))).expanduser().resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)


class StorageService:
    def __init__(self, base_dir: Path = BASE_DIR):
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_upload_file(self, file, subdir: str) -> str:
        """
        保存上传文件到本地存储，返回相对路径
        subdir: 例如 "videos/raw/{user_id}"
        """
        dir_path = (self.base_dir / subdir).resolve()
        dir_path.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename or "").suffix or ".bin"
        filename = f"{uuid4().hex}{ext}"
        full_path = dir_path / filename

        # 流式拷贝，避免大文件一次性读入内存
        file.file.seek(0)
        with full_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        # 返回相对路径（统一用 /）
        rel_path = full_path.relative_to(self.base_dir).as_posix()
        return rel_path

    def abs_path(self, rel_path: str) -> Path:
        # rel_path 统一按 posix 存储，这里做兼容
        rel = Path(rel_path.replace("/", os.sep))
        return (self.base_dir / rel).resolve()

    def copy_rel_to(self, src_rel_path: str, dst_subdir: str, dst_ext: str = "") -> str:
        """
        把 src_rel_path 复制到 dst_subdir 下，生成新文件名，返回新的相对路径
        """
        src = self.abs_path(src_rel_path)
        if not src.exists():
            raise FileNotFoundError(f"input file not found: {src}")

        dst_dir = (self.base_dir / dst_subdir).resolve()
        dst_dir.mkdir(parents=True, exist_ok=True)

        # 默认保留原扩展名
        ext = dst_ext or src.suffix or ".bin"
        dst_name = f"{uuid4().hex}{ext}"
        dst = dst_dir / dst_name

        shutil.copyfile(src, dst)

        return dst.relative_to(self.base_dir).as_posix()

    def get_public_url(self, rel_path: str) -> str:
        """
        生产环境：改成 OSS/S3 预签名 URL
        现在：返回本地 static 地址
        """
        return f"/static/{rel_path}"
