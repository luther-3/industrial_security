from ultralytics import YOLO

# Load pretrained model
model = YOLO("yolo26n.pt")

# Train the model on Construction-PPE dataset
model.train(data="construction-ppe.yaml", epochs=100, imgsz=640)