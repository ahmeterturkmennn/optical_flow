import torch
from models.hcvflow import HCVFlow
import cv2
import numpy as np

# Modeli yükle
model = HCVFlow()
model.load_state_dict(torch.load('checkpoints/hcvflow.pth'))
model.eval()

# Giriş görüntüsünü yükle
img = cv2.imread('path_to_your_image.jpg')
img = cv2.resize(img, (512, 512))
img_tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).float()

# Tahmin yap
with torch.no_grad():
    output = model(img_tensor)

# Sonucu kaydet
output_image = output.squeeze().permute(1, 2, 0).numpy()
cv2.imwrite('output.jpg', output_image)
