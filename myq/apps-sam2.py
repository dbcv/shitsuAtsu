from django.apps import AppConfig
import torch

SAM2_PREDICTOR = None

class MyqConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myq'

    def ready(self):
        import myq.signals

        print("--- Loading SAM2 Model ---")
        global SAM2_PREDICTOR
        if SAM2_PREDICTOR is None:
            try:
                from sam2.build_sam import build_sam2
                from sam2.sam2_image_predictor import SAM2ImagePredictor

                if torch.cuda.is_available():
                    device = "cuda"
                elif torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"

                print(f"Using device: {device}")

                sam2_checkpoint = "../checkpoints/sam2.1_hiera_large.pt"
                model_cfg = "../sam2/configs/sam2.1/sam2.1_hiera_l.yaml"

                sam2_model = build_sam2(model_cfg, sam2_checkpoint, device=device)
                SAM2_PREDICTOR = SAM2ImagePredictor(sam2_model)
                print("--- SAM2 Model Loaded Successfully ---")
            except Exception as e:
                print(f"!!! FAILED to load SAM2 Model: {e}")

