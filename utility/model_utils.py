from pathlib import Path
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME


def load_embedding_model(verify: bool = True) -> SentenceTransformer:
    """Load a SentenceTransformer model from a local directory.

    Parameters
    ----------
    verify: bool, optional
        When True, perform a tiny encode call to ensure the model is usable.
    Returns
    -------
    SentenceTransformer
        Loaded model instance.
    Raises
    ------
    FileNotFoundError
        If the configured path does not exist or is not a directory.
    RuntimeError
        If the model cannot be loaded or fails verification.
    """
    model_path = Path(EMBEDDING_MODEL_NAME)
    if not model_path.exists() or not model_path.is_dir():
        print(
            f"⚠️  Expected embedding model at '{model_path}', but it was not found. "
            "Offline mode does not attempt to download models."
        )
        raise FileNotFoundError(
            f"Embedding model not found at '{model_path}'. "
            "Ensure the model is downloaded to this path or update EMBEDDING_MODEL_NAME."
        )

    try:
        model = SentenceTransformer(str(model_path))
        print(f"✅ Loaded embedding model from {model_path}")
    except Exception as exc:
        raise RuntimeError(f"Failed to load embedding model from {model_path}: {exc}")

    if verify:
        try:
            model.encode(["test"], show_progress_bar=False)
        except Exception as exc:
            raise RuntimeError(
                f"Model at {model_path} failed verification encode: {exc}"
            )

    return model
