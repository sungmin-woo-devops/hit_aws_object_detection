import streamlit as st
import cv2
import numpy as np
import onnxruntime as ort
import json
from pathlib import Path
from PIL import Image
import time
import torch
import tempfile
from ultralytics import YOLO

# Page configuration
st.set_page_config(
    page_title="AWS Diagram Object Detection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

def convert_pt_to_onnx_and_metadata():
    """Convert PyTorch model to ONNX and create metadata"""
    # 현재 스크립트 위치 기준으로 models 디렉토리 찾기
    current_dir = Path(__file__).parent
    models_dir = current_dir / "models"
    
    pt_files = list(models_dir.glob("*.pt"))
    if not pt_files: 
        st.error(f"No PT files found in {models_dir}")
        return None, None
    
    try:
        # Load YOLO model using ultralytics
        model = YOLO(pt_files[0])
        onnx_path = pt_files[0].with_suffix('.onnx')
        
        # Export to ONNX using YOLO's export method
        model.export(format='onnx', imgsz=320, opset=11)
        
        # Get class names from the model
        class_names = list(model.names.values()) if hasattr(model, 'names') else ["aws_service"]
        
        metadata = {
            "model_path": str(onnx_path), 
            "classes": class_names, 
            "imgsz": 320, 
            "conf_threshold": 0.5, 
            "model_name": pt_files[0].stem, 
            "num_classes": len(class_names), 
            "timestamp": time.strftime("%Y%m%d_%H%M%S")
        }
        metadata_path = models_dir / "model_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        st.success(f"✅ Successfully converted {pt_files[0].name} to ONNX")
        return str(onnx_path), metadata
    except Exception as e:
        st.error(f"Failed to convert model: {e}")
        return None, None

@st.cache_resource
def load_model_and_metadata(metadata_path: str):
    """Load ONNX model and metadata from local path"""
    try:
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        model_path = metadata["model_path"]
        if not Path(model_path).exists():
            st.error(f"Model file not found: {model_path}")
            st.stop()

        # Load ONNX model
        session = ort.InferenceSession(model_path)
        return session, metadata
    except Exception as e:
        st.error(f"Failed to load model or metadata: {e}")
        st.stop()

def preprocess_image(image: np.ndarray, imgsz: int):
    """Preprocess image for YOLOv8 ONNX inference"""
    # Handle different image formats
    if len(image.shape) == 2:  # Grayscale
        img = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif len(image.shape) == 3:
        if image.shape[2] == 4:  # RGBA
            img = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        elif image.shape[2] == 3:  # RGB
            img = image.copy()
        else:
            # Handle other channel formats by converting to RGB
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        raise ValueError(f"Unsupported image format with shape: {image.shape}")
    
    img = cv2.resize(img, (imgsz, imgsz))
    img = img.transpose(2, 0, 1).astype(np.float32) / 255.0  # HWC to CHW, normalize
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img

def postprocess_detections(outputs: np.ndarray, conf_threshold: float, nms_threshold: float, img_shape: tuple, imgsz: int):
    """Postprocess YOLOv8 ONNX outputs with NMS"""
    boxes = outputs[0][:, :4]  # x, y, w, h
    scores = outputs[0][:, 4]  # Confidence scores
    class_ids = outputs[0][:, 5].astype(int)  # Class IDs

    # Scale boxes back to original image size
    scale_x, scale_y = img_shape[1] / imgsz, img_shape[0] / imgsz
    boxes[:, [0, 2]] *= scale_x  # x coordinates
    boxes[:, [1, 3]] *= scale_y  # y coordinates

    # Convert center-based (x, y, w, h) to corner-based (x1, y1, x2, y2)
    boxes[:, 0] = boxes[:, 0] - boxes[:, 2] / 2  # x1 = x - w/2
    boxes[:, 1] = boxes[:, 1] - boxes[:, 3] / 2  # y1 = y - h/2
    boxes[:, 2] = boxes[:, 0] + boxes[:, 2]      # x2 = x + w/2
    boxes[:, 3] = boxes[:, 1] + boxes[:, 3]      # y2 = y + h/2

    # Apply NMS (Non-Maximum Suppression)
    indices = cv2.dnn.NMSBoxes(
        boxes.tolist(), scores.tolist(), conf_threshold, nms_threshold
    )
    if isinstance(indices, tuple):
        indices = indices[0]  # Handle tuple output in some OpenCV versions

    return boxes[indices], scores[indices], class_ids[indices]

def draw_detections(image: np.ndarray, boxes: np.ndarray, scores: np.ndarray, class_ids: np.ndarray, class_names: list):
    """Draw bounding boxes and labels on the image"""
    img = image.copy()
    for box, score, class_id in zip(boxes, scores, class_ids):
        x1, y1, x2, y2 = map(int, box)
        label = f"{class_names[class_id]}: {score:.2f}"
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return img

def main():
    st.markdown('<h1 class="main-header">🔍 AWS Diagram Object Detection</h1>', unsafe_allow_html=True)

    # Sidebar configuration
    st.sidebar.header("⚙️ Detection Settings")
    
    # File uploader for metadata.json
    metadata_file = st.sidebar.file_uploader("Upload metadata.json", type="json")
    metadata_path = None
    if metadata_file:
        # Save uploaded metadata.json to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(metadata_file.read())
            metadata_path = tmp.name
    else:
        # Check local models/ directory for metadata.json
        current_dir = Path(__file__).parent
        models_dir = current_dir / "models"
        metadata_path = models_dir / "model_metadata.json"
        
        if not metadata_path.exists() or metadata_path.stat().st_size == 0:
            # Try to convert PT model to ONNX and create metadata
            onnx_path, metadata = convert_pt_to_onnx_and_metadata()
            if onnx_path and metadata:
                metadata_path = models_dir / "model_metadata.json"
                st.sidebar.success("✅ Converted PT model to ONNX and created metadata")
            else:
                st.error("❌ No metadata.json found and no PT model to convert")
                st.stop()
        else:
            st.sidebar.info(f"📁 Using metadata: {metadata_path}")

    # Load model and metadata
    session, metadata = load_model_and_metadata(metadata_path)
    class_names = metadata["classes"]
    imgsz = metadata["imgsz"]
    default_conf = metadata["conf_threshold"]

    # Detection settings
    confidence_threshold = st.sidebar.slider(
        "Confidence Threshold", min_value=0.1, max_value=1.0, value=default_conf, step=0.05
    )
    nms_threshold = st.sidebar.slider(
        "NMS Threshold", min_value=0.1, max_value=1.0, value=0.45, step=0.05
    )

    # Model information
    with st.sidebar.expander("📊 Model Information"):
        st.json({
            "model_name": metadata.get("model_name", "Unknown"),
            "num_classes": metadata.get("num_classes", 0),
            "timestamp": metadata.get("timestamp", "Unknown")
        })

    # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📤 Upload Image")
        uploaded_file = st.file_uploader("Choose an AWS architecture diagram", type=['png', 'jpg', 'jpeg'])

        # Sample images
        st.subheader("Or try a sample:")
        current_dir = Path(__file__).parent
        sample_dir = current_dir / "samples"
        sample_images = []
        if sample_dir.exists():
            # Support multiple image formats
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff"]:
                sample_images.extend(sample_dir.glob(ext))
        
        if sample_images:
            # Create a more user-friendly sample selection
            sample_names = [f"Sample {i+1}: {path.stem}" for i, path in enumerate(sample_images)]
            selected_sample_name = st.selectbox(
                "Choose a sample image:",
                options=[""] + sample_names,
                index=0,
                help="Select a sample AWS architecture diagram to test the detection"
            )
            
            selected_sample = None
            if selected_sample_name:
                sample_index = sample_names.index(selected_sample_name)
                selected_sample = sample_images[sample_index]
                
                # Show preview of selected sample
                if selected_sample:
                    st.image(selected_sample, caption=f"Preview: {selected_sample.name}", width=200)
        else:
            st.info("No sample images found in the samples directory.")

    with col2:
        st.header("🎯 Detection Results")
        if uploaded_file or selected_sample:
            # Load image
            try:
                if uploaded_file:
                    image = Image.open(uploaded_file)
                else:
                    image = Image.open(selected_sample)
                
                # Convert RGBA to RGB if necessary
                if image.mode == 'RGBA':
                    image = image.convert('RGB')
                
                img_array = np.array(image)
                img_shape = img_array.shape[:2]  # Original shape (height, width)
            except Exception as e:
                st.error(f"Failed to load image: {e}")
                return

            # Display original image
            st.subheader("Original Image")
            st.image(image, use_container_width=True)

            # Preprocess and run inference
            with st.spinner("🔍 Detecting AWS services..."):
                start_time = time.time()
                img_input = preprocess_image(img_array, imgsz)
                outputs = session.run(None, {"images": img_input})[0]  # Assuming YOLOv8 ONNX output
                boxes, scores, class_ids = postprocess_detections(
                    outputs, confidence_threshold, nms_threshold, img_shape, imgsz
                )
                inference_time = time.time() - start_time

            # Display results
            if len(boxes) > 0:
                img_with_detections = draw_detections(img_array, boxes, scores, class_ids, class_names)
                st.subheader("🎯 Detected Services")
                st.image(img_with_detections, use_container_width=True)

                # Detection statistics
                num_detections = len(boxes)
                avg_confidence = np.mean(scores) if scores.size > 0 else 0.0
                st.markdown(f"""
                <div class="detection-stats">
                    <h4 style="color: #ffffff; margin-bottom: 1rem;">📈 Detection Statistics</h4>
                    <ul style="color: #e0e0e0; margin: 0; padding-left: 1.5rem;">
                        <li style="margin-bottom: 0.5rem;"><strong style="color: #ffffff;">Services Detected:</strong> <span style="color: #4CAF50;">{num_detections}</span></li>
                        <li style="margin-bottom: 0.5rem;"><strong style="color: #ffffff;">Average Confidence:</strong> <span style="color: #FF9800;">{avg_confidence:.2f}</span></li>
                        <li style="margin-bottom: 0.5rem;"><strong style="color: #ffffff;">Inference Time:</strong> <span style="color: #2196F3;">{inference_time:.3f}s</span></li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                # Detailed results table
                st.subheader("📋 Detailed Results")
                results_data = [
                    {
                        'Service': class_names[int(class_id)] if int(class_id) < len(class_names) else f'Class_{int(class_id)}',
                        'Confidence': f"{score:.3f}",
                        'Location': f"({box[0]:.0f}, {box[1]:.0f}, {box[2]:.0f}, {box[3]:.0f})"
                    }
                    for box, score, class_id in zip(boxes, scores, class_ids)
                ]
                st.dataframe(results_data, use_container_width=True)

                # Download results
                if st.button("💾 Download Results as JSON"):
                    results_json = {
                        'metadata': {
                            'inference_time': inference_time,
                            'model_name': metadata.get('model_name', 'Unknown'),
                            'confidence_threshold': confidence_threshold,
                            'nms_threshold': nms_threshold
                        },
                        'detections': results_data
                    }
                    st.download_button(
                        label="Download JSON",
                        data=json.dumps(results_json, indent=2),
                        file_name=f"aws_detection_results_{int(time.time())}.json",
                        mime="application/json"
                    )
            else:
                st.warning("No AWS services detected. Try adjusting the confidence threshold.")
        else:
            st.info("👆 Please upload an image or select a sample to begin detection.")

if __name__ == "__main__":
    main()