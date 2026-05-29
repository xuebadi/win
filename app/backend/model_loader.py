"""
Model Manager - Lazy imports for memory efficiency
Supports safetensors format via transformers + torch (CPU)
"""
import os
from pathlib import Path


class ModelManager:
    """Unified model loader with lazy heavy imports"""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        # Look for safetensors model directory
        self._model_dir = None
        self._llm = None
        self._tokenizer = None

    def _find_model_dir(self) -> Path | None:
        """Find downloaded model directory (safetensors format)"""
        # Check common patterns from modelscope cache
        cache_dir = self.models_dir
        if not cache_dir.exists():
            return None

        # Direct subdirectory with config.json
        for d in cache_dir.iterdir():
            if d.is_dir() and (d / "config.json").exists():
                return d

        # modelscope cache: models/Qwen/Qwen3-1.7B/
        for namespace in cache_dir.iterdir():
            if namespace.is_dir():
                for model_dir in namespace.iterdir():
                    if model_dir.is_dir() and (model_dir / "config.json").exists():
                        return model_dir

        return None

    @property
    def model_dir(self) -> Path | None:
        if self._model_dir is None:
            self._model_dir = self._find_model_dir()
        return self._model_dir

    def get_status(self) -> dict:
        """Check model file status without loading anything heavy"""
        model_dir = self.model_dir
        return {
            "model_exists": model_dir is not None,
            "model_loaded": self._llm is not None,
            "backend": "transformers" if self._llm is not None else None,
            "model_path": str(model_dir) if model_dir else None,
        }

    def load(self):
        """Load model and tokenizer (lazy heavy imports)"""
        if self._llm is not None:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        model_path = self.model_dir
        if model_path is None:
            raise FileNotFoundError(
                "Model not found. Download with: "
                "python -c \"from modelscope import snapshot_download; "
                "snapshot_download('Qwen/Qwen3-1.7B', cache_dir='models')\""
            )

        self._tokenizer = AutoTokenizer.from_pretrained(
            str(model_path), trust_remote_code=True
        )
        self._llm = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            dtype=torch.bfloat16,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        self._llm.eval()

    def generate(self, prompt: str, max_new_tokens: int = 512) -> str:
        """Generate text from prompt"""
        self.load()

        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = self._llm.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        result = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt part
        if result.startswith(prompt):
            result = result[len(prompt):].strip()
        # Truncate if model generates multiple turns
        for stop_token in ["\n用户:", "\n导师:", "\nUser:", "\nAssistant:"]:
            idx = result.find(stop_token)
            if idx > 0:
                result = result[:idx].strip()
        return result

    def unload(self):
        """Release model memory"""
        if self._llm is not None:
            del self._llm
            self._llm = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        import gc
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass
