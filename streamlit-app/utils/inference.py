import cv2
import numpy as np
import torch
from ultralytics import YOLO
import onnxruntime as ort
from pathlib import Path
from tensorflow.keras.models import load_model


class ObjectDetector:
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model_type = self._detect_model_type()
        self.model = self._load_model()
    

    def _detect_model_type(self):
        """Detect model type based on file extension"""
        if self.model_path.suffix == '.pt':
            return 'pytorch'
        elif self.model_path.suffix == '.onnx':
            return 'onnx'
        elif self.model_path.suffix == '.h5':
            return 'keras'
        else:
            raise ValueError(f"Unsupported model type: {self.model_path.suffix}")
    

    def _load_model(self):
        """load model based on model type"""
        if self.model_type == 'pytorch':
            return YOLO(str(self.model_path))
        elif self.model_type == 'onnx':
            return ort.InferenceSession(str(self.model_path))
        elif self.model_type == 'keras':
            return load_model(str(self.model_path))
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
    
    def detect(self, image: np.ndarray, conf_threshold: float = 0.5,
               nms_threshold: float = 0.45) -> dict:
        """Run object detection on image"""
        if self.model_type == 'pytorch':
            return self._detect_pytorch(image, conf_threshold, nms_threshold)
        elif self.model_type == 'onnx':
            return self._detect_onnx(image, conf_threshold, nms_threshold)
        elif self.model_type == 'keras':
            return self._detect_keras(image, conf_threshold, nms_threshold)

    
    def _detect_pytorch(self, image: np.ndarray, conf_threshold: float,
                        nms_threshold: float) -> dict:
        """PyTorch YOLO detection"""
        results = self.model(image, conf=conf_threshold, iou=nms_threshold)

        detections = {
            'boxes': [],
            'scores': [],
            'class_ids': [],
        }

        for result in results:
            if results.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                scores = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy()

                detections['boxes'] = boxes.tolist()
                detections['scores'] = scores.tolist()
                detections['class_ids'] = class_ids.tolist()

        return detections

    
    def _detect_onnx(self, image: np.ndarray, conf_threshold: float,
                     nms_threshold: float) -> dict:
        """ONNX model detection"""
        input_tensor = self._preprocess_onnx(image)
        outputs = self.model.run(None, {self.model.get_inputs()[0].name: input_tensor})
        return self._postprocess_onnx(outputs[0], conf_threshold, nms_threshold)

    def _detect_keras(self, image: np.ndarray, conf_threshold: float,
                      nms_threshold: float) -> dict:
        """Keras (HDF5) model detection"""
        img = cv2.resize(image, (640, 640))
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)  # [B, H, W, C]

        preds = self.model.predict(img)[0]  # 모델에 따라 수정 필요

        # 예시용: 단일 바운딩 박스 출력
        detections = {
            'boxes': [[100, 100, 300, 300]],  # dummy box
            'scores': [0.9],
            'class_ids': [0]
        }

        # → 실제 postprocess 로직 필요 (예: YOLO 계열이면 decode 작업 등)

        return detections

    def _preprocess_onnx(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for ONNX model"""
        img = cv2.resize(image, (640, 640))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))  # HWC → CHW
        img = np.expand_dims(img, axis=0)  # Add batch dim
        return img

    def _postprocess_onnx(self, outputs: np.ndarray, conf_threshold: float,
                          nms_threshold: float) -> dict:
        """Post-process ONNX outputs"""
        detections = {
            'boxes': [],
            'scores': [],
            'class_ids': []
        }

        # → 여기도 모델별로 커스터마이징 필요
        return detections