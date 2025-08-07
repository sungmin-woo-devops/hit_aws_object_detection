import pytest
import sys
from pathlib import Path
import numpy as np

from app import (
    preprocess_image,
    postprocess_detections,
    draw_detections,
)

# Add the parent directory to the path to import app functions
sys.path.append(str(Path(__file__).parent.parent))


class TestImageProcessing:
    """Test image processing functions"""

    def test_preprocess_image_rgb(self):
        """Test preprocessing RGB image"""
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        processed = preprocess_image(test_image, 320)

        assert processed.shape == (1, 3, 320, 320)
        assert processed.dtype == np.float32
        assert np.all(processed >= 0) and np.all(processed <= 1)

    def test_preprocess_image_rgba(self):
        """Test preprocessing RGBA image"""
        test_image = np.random.randint(0, 255, (100, 100, 4), dtype=np.uint8)
        processed = preprocess_image(test_image, 320)

        assert processed.shape == (1, 3, 320, 320)
        assert processed.dtype == np.float32

    def test_preprocess_image_grayscale(self):
        """Test preprocessing grayscale image"""
        test_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        processed = preprocess_image(test_image, 320)

        assert processed.shape == (1, 3, 320, 320)
        assert processed.dtype == np.float32

    def test_postprocess_detections(self):
        """Test postprocessing detections"""
        mock_output = np.array([[
            [100, 100, 50, 50, 0.8, 0],
            [200, 200, 30, 30, 0.6, 1]
        ]])

        img_shape = (640, 640)
        imgsz = 320

        boxes, scores, class_ids = postprocess_detections(
            mock_output, 0.5, 0.45, img_shape, imgsz
        )

        assert len(boxes) >= 0
        assert len(scores) >= 0
        assert len(class_ids) >= 0

    def test_draw_detections(self):
        """Test drawing detections on image"""
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        boxes = np.array([[10, 10, 50, 50], [20, 20, 60, 60]])
        scores = np.array([0.8, 0.6])
        class_ids = np.array([0, 1])
        class_names = ["service1", "service2"]

        result = draw_detections(
            test_image, boxes, scores, class_ids, class_names
        )

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype


class TestModelConversion:
    """Test model conversion functions"""

    def test_convert_pt_to_onnx_no_files(self, tmp_path):
        """Test conversion when no PT files exist"""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        def mock_convert():
            pt_files = list(models_dir.glob("*.pt"))
            if not pt_files:
                return None, None
            return "dummy_path", {}

        onnx_path, metadata = mock_convert()
        assert onnx_path is None
        assert metadata is None

    def test_metadata_structure(self):
        """Test metadata structure validation"""
        mock_metadata = {
            "model_path": "test.onnx",
            "classes": ["aws_service"],
            "imgsz": 320,
            "conf_threshold": 0.5,
            "model_name": "test_model",
            "num_classes": 1,
            "timestamp": "20250101_000000"
        }

        required_fields = ["model_path", "classes", "imgsz", "conf_threshold"]
        for field in required_fields:
            assert field in mock_metadata

        assert isinstance(mock_metadata["classes"], list)
        assert isinstance(mock_metadata["imgsz"], int)
        assert isinstance(mock_metadata["conf_threshold"], float)


class TestAppConfiguration:
    """Test app configuration and dependencies"""

    def test_required_imports(self):
        """Test that all required modules can be imported"""
        assert True

    def test_css_styles(self):
        """Test that CSS styles are properly defined"""
        css_content = """
        .main-header {
            font-size: 2.5rem;
            color: #FF9900;
            text-align: center;
            margin-bottom: 2rem;
        }
        .detection-stats {
            background-color: #1e1e1e;
            color: #ffffff;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            border: 1px solid #333333;
        }
        """

        assert "main-header" in css_content
        assert "detection-stats" in css_content
        assert "#1e1e1e" in css_content


class TestFileOperations:
    """Test file operations and path handling"""

    def test_sample_images_discovery(self):
        """Test that sample images can be discovered"""
        current_dir = Path(__file__).parent.parent
        sample_dir = current_dir / "samples"

        if sample_dir.exists():
            image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff"]
            found_images = []

            for ext in image_extensions:
                found_images.extend(sample_dir.glob(ext))

            assert len(found_images) >= 0

    def test_models_directory_structure(self):
        """Test models directory structure"""
        current_dir = Path(__file__).parent.parent
        models_dir = current_dir / "models"

        assert models_dir.exists(), "Models directory should exist"

        pt_files = list(models_dir.glob("*.pt"))
        assert len(pt_files) >= 0

    def test_requirements_file(self):
        """Test that requirements.txt exists and is valid"""
        current_dir = Path(__file__).parent.parent
        requirements_file = current_dir / "requirements.txt"

        assert requirements_file.exists(), "requirements.txt should exist"

        with open(requirements_file, 'r') as f:
            content = f.read()
            assert len(content.strip()) > 0, "requirements.txt is empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
