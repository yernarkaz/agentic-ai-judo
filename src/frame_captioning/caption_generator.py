from transformers import AutoProcessor, AutoModelForVision2Seq
import torch
from PIL import Image
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameCaptioner:
    def __init__(self, model_name="Salesforce/blip-image-captioning-large"):
        """
        Initialize the frame captioner with a pre-trained model.

        Args:
            model_name: Name of the pre-trained model to use
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = AutoModelForVision2Seq.from_pretrained(model_name).to(self.device)

    def generate_caption(self, image_path: str) -> dict:
        """
        Generate a caption for a single image.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing the caption and timestamp
        """
        try:
            # Load and preprocess the image
            image = Image.open(image_path)
            inputs = self.processor(image, return_tensors="pt").to(self.device)

            # Generate caption
            output = self.model.generate(**inputs, max_new_tokens=50)
            caption = self.processor.decode(output[0], skip_special_tokens=True)

            # Extract timestamp from filename (assuming format frame_XXXX.jpg)
            frame_num = Path(image_path).stem.split("_")[1]
            timestamp = int(frame_num)  # Convert to actual timestamp if needed

            return {
                "timestamp": timestamp,
                "caption": caption,
                "image_path": image_path,
            }

        except Exception as e:
            logger.error(f"Error generating caption for {image_path}: {str(e)}")
            raise

    def process_frames(self, frame_paths: list) -> list:
        """
        Generate captions for multiple frames.

        Args:
            frame_paths: List of paths to frame images

        Returns:
            List of dictionaries containing captions and timestamps
        """
        captions = []
        for frame_path in frame_paths:
            try:
                caption_data = self.generate_caption(frame_path)
                captions.append(caption_data)
                logger.info(f"Generated caption for {frame_path}")
            except Exception as e:
                logger.error(f"Skipping frame {frame_path} due to error: {str(e)}")
                continue

        return sorted(captions, key=lambda x: x["timestamp"])
