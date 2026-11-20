# SCALER Project Website

Static academic project page for **SCALER: Breaking the Latent Scaling Bottleneck via Single-Pass Context-Anchored Latent Visual Reasoning** at **https://bonjour-codedev.github.io/SCALER/**.

The site lives in `SCALER/`. No build step, external fonts, or package installation is required.

```bash
python3 -m http.server 8080
# Visit http://localhost:8080/SCALER/
```

- `SCALER/index.html`: project overview, method, benchmark results, and interactive figures.
- `SCALER/style.css`: responsive desktop and mobile layouts.
- `SCALER/app.js`: accessible figure viewer, zoom controls, navigation, and copy buttons.
- `SCALER/assets/`: nine rendered figures, high-resolution versions, and site artwork.

The page presents the motivation, single-pass inference pipeline, three-stage SFT + ALPO training framework, task-complexity heatmaps, latent-length scaling curves, qualitative case studies, attention visualizations, and supplementary analyses. Official code and runnable examples are available in [SCALER-Code](https://github.com/Bonjour-CodeDev/SCALER-Code). **Training code & Model Checkpoints will be released soon.**

```bash
python3 tools/check_site.py
node --check SCALER/app.js
```
