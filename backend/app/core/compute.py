from app.core.settings import settings


def torch_device() -> str:
    configured = settings.torch_device.strip().lower()
    if configured != "auto":
        return configured

    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def cuda_status() -> dict[str, str | bool | int | None]:
    try:
        import torch

        available = torch.cuda.is_available()
        return {
            "available": available,
            "device_count": torch.cuda.device_count() if available else 0,
            "device_name": torch.cuda.get_device_name(0) if available else None,
            "torch_version": torch.__version__,
        }
    except Exception as exc:
        return {
            "available": False,
            "device_count": 0,
            "device_name": None,
            "torch_version": None,
            "error": str(exc),
        }
