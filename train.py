from dotenv import load_dotenv
load_dotenv()
ROBOFLOW_API_KEY = os.getenv('ROBOFLOW_API_KEY', "GmmcPzjqUM0s4fqtIu1V")

import json
import os
import shutil
import yaml
import cv2
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st  # Streamlit 추가
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple
import albumentations as A
import tensorflow as tf
from roboflow import Roboflow
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from ultralytics import YOLO
import gc

# GPU 설정
physical_devices = tf.config.experimental.list_physical_devices('GPU')
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
else:
    tf.config.set_visible_devices(tf.config.list_physical_devices('CPU')[0], 'CPU')


# Roboflow 데이터 다운로드
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace("aws-icons").project("aws-icon-detector")
version = project.version(4)
dataset = version.download("yolov8")


# 모델 다운로드
model = YOLO('yolov8n.pt')  # yolov8s.pt로 변경 가능


# 하이퍼파라미터 튜닝 포함한 모델 훈련
model.train(
    # 데이터 설정
    project='/home/smallpod/workspace/hit_aws_object_detection/runs',
    data='/home/smallpod/workspace/hit_aws_object_detection/AWS-Icon-Detector--4/data.yaml', 
    
    # 리소스 설정
    workers=4,  # 8코어 중 4개 사용
    cache='disk',

    # 모델 훈련 설정
    epochs=100, 
    imgsz=320,  # 416 대신 320 사용
    batch=8,
    patience=10,
    cos_lr=True, # 코사인 학습률 스케줄링

    # 하이퍼파라미터 튜닝
    lr0=0.01, # 초기 학습률
    lrf=0.1,
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3.0,
    warmup_momentum=0.8,
    warmup_bias_lr=0.1,
    box=7.5,  # 박스 손실 가중치
    cls=0.5,  # 클래스 손실 가중치
    dfl=1.5,  # 분포 초점 손실 가중치
)


# 모델 저장
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = f'/home/smallpod/workspace/hit_aws_object_detection/runs/aws_icon_detector_best_{current_time}.pt'
model.save(model_path)


# ONNX로 모델 내보내기
onnx_path = f'/home/smallpod/workspace/hit_aws_object_detection/runs/aws_icon_detector_best_{current_time}.onnx'
model.export(format='onnx', imgsz=320, onnx_path=onnx_path)
exported_onnx = Path(model_path).parent / 'aws_icon_detector_best.onnx'
if exported_onnx.exists():
    shutil.move(str(exported_onnx), onnx_path)

# metadata.json 생성
metadata = {
    "model_name": f"aws_icon_detector_best_{current_time}",
    "classes": model.names,  # 클래스 이름
    "imgsz": 320,  # 입력 이미지 크기
    "conf_threshold": 0.5,  # 신뢰도 임계값
    "model_path": onnx_path,  # ONNX 모델 경로
    "timestamp": current_time,
    "num_classes": len(model.names),
}
metadata_path = f'/home/smallpod/workspace/hit_aws_object_detection/runs/metadata_{current_time}.json'
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=4)


# 모델 평가
# 학습이 100 에포크를 완료한 후, 테스트 데이터로 모델 성능을 평가
# 클래스별 성능 분석: mAP@50, mAP@50:95, Precision, Recall, F1-score, AP@50, AP@50:95
model = YOLO(model_path)  # 저장된 모델 경로 사용
results = model.val(
    data='/home/smallpod/workspace/hit_aws_object_detection/AWS-Icon-Detector--4/data.yaml',
    imgsz=320,
    batch=8,
    project='/home/smallpod/workspace/hit_aws_object_detection/runs'
)


# Confusion Matrix 시각화
cm = results.confusion_matrix.matrix
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='.0f', cmap='Blues', xticklabels=results.names.values(), yticklabels=results.names.values())
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('True')
plt.savefig('/home/smallpod/workspace/hit_aws_object_detection/runs/confusion_matrix.png')
plt.close()


# 예측 수행
results = model.predict(
    source='/home/smallpod/workspace/hit_aws_object_detection/AWS-Icon-Detector--4/test/images', 
    imgsz=320, 
    conf=0.5,    # 신뢰도 임계값 설정
    save=True,   # 예측 결과를 파일로 저장 
    project='/home/smallpod/workspace/hit_aws_object_detection/runs'
)


# 클래스별 탐지 수 집계
all_classes = []
for result in results:
    classes = result.boxes.cls.cpu().numpy()
    all_classes.extend(classes.astype(int))
class_counts = np.bincount(all_classes, minlength=len(results.names))


# 클래스별 탐지 수 시각화
fig = px.bar(x=list(results.names.values()), y=class_counts, labels={'x': 'Class', 'y': 'Count'})
fig.update_layout(title='Class Detection Counts')
st.plotly_chart(fig)  # Streamlit에서 표시
fig.write(f'/home/smallpod/workspace/hit_aws_object_detection/runs/class_counts.html')


# 클래스별 탐지 수 집계
all_classes = []
for result in results:
    classes = result.boxes.cls.cpu().numpy()
    all_classes.extend(classes.astype(int))
class_counts = np.bincount(all_classes, minlength=len(results.names))


# 클래스별 탐지 수 시각화 (Streamlit 없이 로컬 저장)
fig = px.bar(x=list(results.names.values()), y=class_counts, labels={'x': 'Class', 'y': 'Count'})
fig.update_layout(title='Class Detection Counts')
fig.write(f'/home/smallpod/workspace/hit_aws_object_detection/runs/class_counts.html')


# 예측 결과 시각화 (Streamlit 없이 로컬 저장)
for idx, result in enumerate(results):
    img = result.orig_img
    boxes = result.boxes.xyxy.cpu().numpy()
    scores = result.boxes.conf.cpu().numpy()
    classes = result.boxes.cls.cpu().numpy()
    class_names = result.names

    for box, score, cls in zip(boxes, scores, classes):
        x1, y1, x2, y2 = map(int, box)
        label = f"{class_names[int(cls)]}: {score:.2f}"
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 로컬 저장
    cv2.imwrite(f'/home/smallpod/workspace/hit_aws_object_detection/runs/prediction_{idx + 1}.png', img[..., ::-1])


# 메모리 정리
gc.collect()