import os
import labelbox as lb
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LabelboxPipeline:
    def __init__(self):
        self.api_key = os.getenv("LABELBOX_API_KEY")
        self.project_id = os.getenv("LABELBOX_PROJECT_ID")
        
        if not self.api_key or not self.project_id:
            raise EnvironmentError("[!] CRITICAL ERROR: Live API credentials missing from .env! Mocks disabled.")
            
        self.client = lb.Client(api_key=self.api_key)

    def process_batch_historical(self, model_outputs_array):
        """
        Processes massive historical CSV predictions into Labelbox overnight.
        Targeted for Training and CV refinement.
        """
        logger.info(f"[*] Processing Labelbox MAL BATCH Job. Size: {len(model_outputs_array)}")
        predictions = self._format_schema(model_outputs_array)
        job_name = f"wtt_mal_batch_{os.urandom(4).hex()}"
        
        try:
            upload_job = lb.MALPredictionImport.create_from_objects(self.client, self.project_id, job_name, predictions)
            upload_job.wait_until_done()
            logger.info(f"[*] Batch Pipeline Synced. Errors: {upload_job.errors}")
        except Exception as e:
            logger.error(f"[!] BATCH MAL Upload Failed: {e}")

    def process_live_stream_webhook(self, realtime_anomaly_json):
        """
        Executes on a live ping from the Go ingestion layer.
        Immediately formats the single anomaly bounding box to the live remote labelers.
        """
        logger.info("[*] Processing Labelbox MAL REAL-TIME Stream.")
        predictions = self._format_schema([realtime_anomaly_json])
        job_name = f"wtt_mal_rt_{os.urandom(4).hex()}"
        
        try:
            upload_job = lb.MALPredictionImport.create_from_objects(self.client, self.project_id, job_name, predictions)
            logger.info("[*] Real-Time pipeline hook triggered successfully.")
        except Exception as e:
            logger.error(f"[!] STREAM MAL Upload Failed: {e}")

    def _format_schema(self, data_array):
        predictions = []
        for output in data_array:
            bbox = lb.types.Rectangle(top=output["top"], left=output["left"], height=output["height"], width=output["width"])
            pred = lb.types.ObjectAnnotation(name=output["target"], value=bbox)
            predictions.append(lb.types.Label(data=lb.types.ImageData(global_key=output["row_id"]), annotations=[pred]))
        return predictions

if __name__ == "__main__":
    logger.info("[*] Polyglot Labelbox MAL DAEMON started.")
    # Pipeline awaits calls from C++ or Go layers rather than running Mocks.
