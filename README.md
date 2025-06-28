# Optical Flow Comparison: HCVFlow vs Lucas-Kanade

This repository contains the project developed for the **EE584 – Machine Vision** course at METU. The project compares the performance of two optical flow estimation methods: the classical **Lucas-Kanade** algorithm and the modern deep learning-based **HCVFlow**.

[🎥 Watch Explanation on YouTube](https://youtu.be/LhAHxa8gRbo)

---

## 🔍 Abstract

This project compares HCVFlow and Lucas-Kanade optical flow methods for EE584. HCVFlow, a learning-based model, handles blur and complex motion better, while Lucas-Kanade is faster but less robust. Results show the trade-off between accuracy and efficiency in optical flow estimation.

---

## 📂 Project Structure

HCVFlow.pdf is original paper.
HCVFlow contains project files.
Run.txt shows how to run project.
SlideShow.pptx is explanation with slides whereas Term Project.docx is comprehensive explanation paper of project. 
Lucas_Kanade_Optical_Flow.ipynb contains traditional optical flow method.


---

## ⚙️ Methods

### Lucas-Kanade
- Traditional optical flow algorithm based on image gradients
- Implemented using OpenCV’s `cv2.calcOpticalFlowPyrLK`
- Fast and lightweight, but sensitive to blur and large motion

### HCVFlow
- Deep learning-based model designed for blurry and degraded videos
- Uses hierarchical cost volumes for flow estimation
- Adapted from the official repo: [HCVFlow GitHub](https://github.com/gangweix/HCVFlow/tree/main)
- I added **video inference support** to run it on full video files

---

## 🧪 Experiments

- Input: Videos with motion blur and complex movement
- Compared flow field quality visually and functionally
- Focused on robustness to blur and motion consistency

---

## 📊 Results

- **Lucas-Kanade**: Fast, interpretable, but struggles with blur
- **HCVFlow**: Accurate and robust, especially under challenging visual conditions
