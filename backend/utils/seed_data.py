from faker import Faker
from uuid import uuid4
from datetime import datetime, timedelta
import random

fake = Faker()

def generate_dummy_users(n=3):
    return [
        {
            "email": fake.email(),
            "api_token": str(uuid4()),
            "role": random.choice(["admin", "user", "guest"]),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        } for _ in range(n)
    ]

def generate_dummy_datasets(n=3):
    return [
        {
            "name": fake.word(),
            "description": fake.sentence(),
            "file_path": f"s3://bucket/datasets/{fake.word()}/data.zip",
            "file_size": random.randint(1000000, 10000000000), # 1MB to 10GB
            "metadata": {
                "num_samples": random.randint(1000, 10000),
                "classes": fake.words(3),
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        } for _ in range(n)
    ]

def generate_dummy_models(n=3, dataset_ids=None, user_ids=None):
    frameworks = ["tensorflow", "pytorch", "ultralytics_yolo", "huggingface"]
    formats = ["onnx", "pt", "h5", "bin"]
    metadata_examples = {
        "tensorflow": {"input_shape": [224, 224, 3], "model_type": "ResNet50"},
        "pytorch": {"input_shape": [3, 224, 224], "model_type": "resnet18"},
        "ultralytics_yolo": {"input_size": [640, 640], "classes": ["person", "car"]},
        "huggingface": {"model_type": "bert-base-uncased", "max_length": 512}
    }
    return [
        {
            "name": fake.word(),
            "version": f"v{random.randint(1, 5)}.0",
            "framework": random.choice(frameworks),
            "file_path": f"s3://bucket/models/{random.choice(frameworks)}/{fake.word()}/v{random.randint(1, 5)}.0/model.{random.choice(formats)}",
            "format": random.choice(formats),
            "file_size": random.randint(1000000, 1000000000),
            "metadata": metadata_examples[random.choice(frameworks)],
            "dataset_id": random.choice(dataset_ids) if dataset_ids else None,
            "created_by": random.choice(user_ids) if user_ids else None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        } for _ in range(n)
    ]

def generate_dummy_experiments(n=3, model_ids=None, user_ids=None):
    frameworks = ["tensorflow", "pytorch", "ultralytics_yolo", "huggingface"]
    return [
        {
            "model_id": random.choice(model_ids) if model_ids else None,
            "name": fake.word(),
            "framework": random.choice(frameworks),
            "hyperparameters": {"learning_rate": random.uniform(0.0001, 0.01), "batch_size": random.choice([16, 32, 64])},
            "metrics": {"accuracy": random.uniform(0.8, 0.99), "loss": random.uniform(0.1, 0.5)},
            "start_time": datetime.now() - timedelta(days=random.randint(1, 10)),
            "end_time": datetime.now() - timedelta(days=random.randint(0, 5)),
            "created_by": random.choice(user_ids) if user_ids else None,
            "created_at": datetime.now()
        } for _ in range(n)
    ]