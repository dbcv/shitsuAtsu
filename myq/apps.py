import os

from django.apps import AppConfig

SAM3_PROCESSOR = None
SAM2_PREDICTOR = None


class MyqConfig(AppConfig):
    name = "myq"

    def ready(self):

        if os.environ.get("RUN_MAIN") != "true":
            return
