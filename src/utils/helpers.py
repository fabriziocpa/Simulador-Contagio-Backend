"""Utility functions and helpers."""
import os
import shutil
from pathlib import Path


class DirectoryManager:

    @staticmethod
    def clean_and_create(base_dir: Path):
        """Clean and recreate output directory structure."""
        if base_dir.exists():
            shutil.rmtree(base_dir)
        
        base_dir.mkdir(parents=True, exist_ok=True)
        (base_dir / 'grafos_diarios').mkdir(exist_ok=True)
        (base_dir / 'epidemia').mkdir(exist_ok=True)
    
    @staticmethod
    def ensure_exists(directory: Path):
        """Ensure directory exists."""
        directory.mkdir(parents=True, exist_ok=True)
