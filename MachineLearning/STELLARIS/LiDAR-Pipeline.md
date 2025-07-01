# 🎮 Dynamic Classifier Network in UPBGE

> _“A dynamic set of heads or channels of information emerging from encoded embeddings.”_

---

## ✨ Overview
**Dynamic Classifier Network**  
- Spawns and prunes lightweight binary **heads** on the fly  
- All heads share a **single encoder** (Sobel → Conv pipeline)  
- Ideal for discovering new shape concepts in 3D scans and collapsing redundancies

---

## 🚀 Prerequisites
- **UPBGE** (Blender Game Engine) with its embedded Python  
- Your existing **point-cloud→depth-map** pipeline (`PointCloudRead` + `sample_six_side_depths`)

---

## 🗺️ Locating UPBGE’s `site-packages`
1. **Launch** UPBGE and open the **Python Console**.  
2. Run:
   ```python
   import site
   print(site.getsitepackages())
