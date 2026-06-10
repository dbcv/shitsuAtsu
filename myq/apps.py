import os
from pathlib import Path

from django.apps import AppConfig
from config import settings
import torch

SAM3_PROCESSOR = None
SAM2_PREDICTOR = None
class MyqConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myq'

    def ready(self):
        
        if os.environ.get("RUN_MAIN") != "true":return

        import myq.signals

        # print("--- Loading SAM3 Model ---")
        # global SAM3_PROCESSOR
        # if SAM3_PROCESSOR is None:
        #     try:
        #         from sam3.model_builder import build_sam3_image_model
        #         from sam3.model.sam3_image_processor import Sam3Processor

        #         if torch.cuda.is_available():
        #             device = "cuda"
        #         elif torch.backends.mps.is_available():
        #             device = "mps"
        #         else:
        #             device = "cpu"

        #         print(f"Using device: {device}")

                
        #         bpe_path = Path(settings.BASE_DIR) / "sam3" / "sam3" / "assets" / "bpe_simple_vocab_16e6.txt.gz"

        #         if not bpe_path.exists():
        #             raise FileNotFoundError(f"BPE vocab not found: {bpe_path}")

        #         sam3_model = build_sam3_image_model(bpe_path=str(bpe_path))

        #         SAM3_PROCESSOR = Sam3Processor(sam3_model)

        #         print("--- SAM3 Model Loaded Successfully ---")
        #     except Exception as e:
        #         print(f"!!! FAILED to load SAM3 Model: {e}")

