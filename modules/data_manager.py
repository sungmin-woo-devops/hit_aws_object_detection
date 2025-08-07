#!/usr/bin/env python3
"""
데이터 관리 시스템 - 버킷 prefix 전략 및 로컬 디렉터리 관리

이 모듈은 AI 모델 학습을 위한 데이터의 전체 라이프사이클을 관리합니다:
- 원본 데이터 수집 및 저장
- 전처리 및 라벨링 준비
- 데이터셋 구성 및 버전 관리
- 모델 학습 및 결과 저장
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import yaml
from tqdm import tqdm

import modules.minio as minio


class DataManager:
    """데이터 라이프사이클 관리 클래스"""
    
    def __init__(self, bucket_name: str, local_root: str = "./data"):
        self.bucket_name = bucket_name
        self.local_root = Path(local_root)
        
        # 버킷 prefix 정의
        self.prefixes = {
            'raw': 'raw/',
            'processed': 'processed/',
            'datasets': 'datasets/',
            'models': 'models/',
            'exports': 'exports/'
        }
        
        # 로컬 디렉터리 구조 정의
        self.local_dirs = {
            'raw': self.local_root / 'raw',
            'processed': self.local_root / 'processed',
            'datasets': self.local_root / 'datasets',
            'models': self.local_root / 'models',
            'temp': self.local_root / 'temp'
        }
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """로컬 디렉터리 구조 생성"""
        for dir_path in self.local_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def upload_raw_data(self, local_path: str, data_type: str = 'images') -> bool:
        """원본 데이터 업로드"""
        local_file = Path(local_path)
        if not local_file.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {local_path}")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = f"{self.prefixes['raw']}{data_type}/{timestamp}_{local_file.name}"
        
        return minio.upload_file(self.bucket_name, str(local_file), key, quiet=False)
    
    def upload_processed_data(self, local_path: str, status: str = 'unlabeled') -> bool:
        """전처리된 데이터 업로드"""
        local_file = Path(local_path)
        if not local_file.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {local_path}")
            return False
        
        key = f"{self.prefixes['processed']}{status}/{local_file.name}"
        return minio.upload_file(self.bucket_name, str(local_file), key, quiet=False)
    
    def create_dataset_version(self, dataset_name: str, version: str = None) -> str:
        """새로운 데이터셋 버전 생성"""
        if version is None:
            version = datetime.now().strftime("v%Y%m%d_%H%M%S")
        
        dataset_prefix = f"{self.prefixes['datasets']}{dataset_name}_{version}/"
        
        # 데이터셋 디렉터리 구조 생성 (MinIO에서는 빈 폴더를 만들 수 없으므로 메타데이터 파일 생성)
        metadata = {
            'dataset_name': dataset_name,
            'version': version,
            'created_at': datetime.now().isoformat(),
            'status': 'created'
        }
        
        # 로컬에 임시 메타데이터 파일 생성 후 업로드
        temp_file = self.local_dirs['temp'] / f"{dataset_name}_{version}_metadata.yaml"
        with open(temp_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True)
        
        metadata_key = f"{dataset_prefix}metadata.yaml"
        minio.upload_file(self.bucket_name, str(temp_file), metadata_key, quiet=False)
        
        # 임시 파일 삭제
        temp_file.unlink()
        
        print(f"✅ 데이터셋 '{dataset_name}_{version}' 생성 완료")
        return dataset_prefix
    
    def upload_dataset(self, 
                      local_dataset_path: str, 
                      dataset_name: str, 
                      version: str = None,
                      include_labels: bool = True) -> str:
        """완성된 데이터셋 업로드"""
        dataset_path = Path(local_dataset_path)
        if not dataset_path.exists():
            print(f"❌ 데이터셋 경로를 찾을 수 없습니다: {local_dataset_path}")
            return ""
        
        dataset_prefix = self.create_dataset_version(dataset_name, version)
        
        # 이미지 및 라벨 파일 업로드
        uploaded_count = 0
        failed_count = 0
        
        for split in ['train', 'test', 'val']:
            split_path = dataset_path / split
            if not split_path.exists():
                continue
            
            # 이미지 업로드
            images_dir = split_path / 'images'
            if images_dir.exists():
                for img_file in images_dir.glob('*'):
                    if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        key = f"{dataset_prefix}{split}/images/{img_file.name}"
                        if minio.upload_file(self.bucket_name, str(img_file), key, quiet=True):
                            uploaded_count += 1
                        else:
                            failed_count += 1
            
            # 라벨 업로드 (선택적)
            if include_labels:
                labels_dir = split_path / 'labels'
                if labels_dir.exists():
                    for label_file in labels_dir.glob('*'):
                        if label_file.suffix.lower() in ['.txt', '.xml', '.json', '.npy']:
                            key = f"{dataset_prefix}{split}/labels/{label_file.name}"
                            if minio.upload_file(self.bucket_name, str(label_file), key, quiet=True):
                                uploaded_count += 1
                            else:
                                failed_count += 1
        
        # data.yaml 파일 업로드
        data_yaml = dataset_path / 'data.yaml'
        if data_yaml.exists():
            key = f"{dataset_prefix}data.yaml"
            if minio.upload_file(self.bucket_name, str(data_yaml), key, quiet=False):
                uploaded_count += 1
            else:
                failed_count += 1
        
        print(f"📦 데이터셋 업로드 완료: {uploaded_count}개 성공, {failed_count}개 실패")
        return dataset_prefix
    
    def download_dataset(self, 
                        dataset_prefix: str, 
                        local_path: str = None) -> str:
        """데이터셋 다운로드"""
        if local_path is None:
            local_path = self.local_dirs['datasets'] / dataset_prefix.replace('/', '_').rstrip('_')
        
        local_path = Path(local_path)
        local_path.mkdir(parents=True, exist_ok=True)
        
        # 데이터셋 파일들 목록 조회
        dataset_files = minio.list_files_by_prefix(self.bucket_name, dataset_prefix)
        
        downloaded_count = 0
        for file_info in tqdm(dataset_files, desc="데이터셋 다운로드 중"):
            key = file_info['Key']
            relative_path = key[len(dataset_prefix):]
            local_file_path = local_path / relative_path
            
            # 디렉터리 생성
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if minio.download_file(self.bucket_name, key, str(local_file_path), quiet=True):
                downloaded_count += 1
            else:
                print(f"다운로드 실패: {key}")
        
        print(f"✅ 데이터셋 다운로드 완료: {downloaded_count}개 파일")
        return str(local_path)
    
    def list_datasets(self) -> List[Dict]:
        """사용 가능한 데이터셋 목록 조회"""
        datasets = []
        dataset_files = minio.list_files_by_prefix(self.bucket_name, self.prefixes['datasets'])
        
        # 데이터셋별로 그룹화
        dataset_groups = {}
        for file_info in dataset_files:
            key = file_info['Key']
            parts = key.replace(self.prefixes['datasets'], '').split('/')
            if len(parts) >= 1:
                dataset_id = parts[0]
                if dataset_id not in dataset_groups:
                    dataset_groups[dataset_id] = []
                dataset_groups[dataset_id].append(file_info)
        
        for dataset_id, files in dataset_groups.items():
            dataset_info = {
                'id': dataset_id,
                'file_count': len(files),
                'last_modified': max(f['LastModified'] for f in files),
                'prefix': f"{self.prefixes['datasets']}{dataset_id}/"
            }
            datasets.append(dataset_info)
        
        return sorted(datasets, key=lambda x: x['last_modified'], reverse=True)
    
    def migrate_existing_data(self):
        """기존 데이터를 새로운 구조로 마이그레이션"""
        print("🔄 기존 데이터 마이그레이션 시작...")
        
        # 1. AWS-Icon-Detector--4 데이터셋 마이그레이션
        aws_dataset_path = "./AWS-Icon-Detector--4"
        if Path(aws_dataset_path).exists():
            print("📦 AWS Icon Detector v4 데이터셋 마이그레이션 중...")
            self.upload_dataset(aws_dataset_path, "aws_icon_detector", "v4")
        
        # 2. processed 폴더 데이터 마이그레이션
        processed_path = self.local_dirs['processed']
        if processed_path.exists():
            print("🔧 전처리된 데이터 마이그레이션 중...")
            for img_file in processed_path.glob('*.png'):
                self.upload_processed_data(str(img_file), 'unlabeled')
        
        print("✅ 데이터 마이그레이션 완료")
    
    def generate_local_config(self, dataset_prefix: str) -> str:
        """로컬 학습용 data.yaml 설정 파일 생성"""
        # 데이터셋을 로컬에 다운로드
        local_dataset_path = self.download_dataset(dataset_prefix)
        
        # data.yaml 파일 경로 수정
        data_yaml_path = Path(local_dataset_path) / 'data.yaml'
        if data_yaml_path.exists():
            with open(data_yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 경로를 로컬 경로로 수정
            base_path = Path(local_dataset_path)
            config['train'] = str(base_path / 'train' / 'images')
            config['val'] = str(base_path / 'test' / 'images')  # validation으로 test 사용
            config['test'] = str(base_path / 'test' / 'images')
            
            # 수정된 설정 저장
            with open(data_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            
            print(f"✅ 로컬 설정 파일 생성: {data_yaml_path}")
            return str(data_yaml_path)
        
        return ""


def show_data_structure_guide():
    """데이터 구조 가이드 출력"""
    print("""
🗂️  데이터 관리 구조 가이드

📁 로컬 디렉터리:
├── data/
│   ├── raw/                    # 원본 데이터 (SVG, 이미지)
│   ├── processed/              # 전처리된 데이터 (라벨링 대기)
│   ├── datasets/               # 완성된 데이터셋들
│   ├── models/                 # 학습된 모델 저장
│   └── temp/                   # 임시 작업 파일

☁️  MinIO 버킷 구조:
├── raw/                        # 원본 데이터
│   ├── svg_files/              # SVG 원본들
│   └── images/                 # 기타 이미지 원본들
├── processed/                  # 전처리된 데이터
│   ├── unlabeled/              # 라벨링 대기 중
│   └── temp/                   # 임시 처리 파일들
├── datasets/                   # 완성된 데이터셋들
│   ├── aws_icon_detector_v4/   # AWS Icon Detector v4
│   └── custom_dataset_v1/      # 커스텀 데이터셋
├── models/                     # 학습된 모델들
│   ├── weights/                # 모델 가중치
│   └── experiments/            # 실험 결과
└── exports/                    # 배포용 모델

🔄 데이터 흐름:
raw → processed → datasets → models → exports

📝 사용 예시:
```python
# 데이터 매니저 초기화
dm = DataManager('aws-diagram-object-detection')

# 기존 데이터 마이그레이션
dm.migrate_existing_data()

# 새 데이터셋 업로드
dm.upload_dataset('./my-dataset', 'custom_icons', 'v1')

# 데이터셋 목록 조회
datasets = dm.list_datasets()

# 학습용 로컬 설정 생성
config_path = dm.generate_local_config('datasets/aws_icon_detector_v4/')
```
""")


if __name__ == "__main__":
    show_data_structure_guide()