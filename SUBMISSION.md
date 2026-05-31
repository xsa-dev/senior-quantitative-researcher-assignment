# Submission

## Links

- GitHub repository: https://github.com/xsa-dev/senior-quantitative-researcher-assignment
- Russian documentation Google Doc: https://docs.google.com/document/d/17FHnEeDEcN-3uFHe-J6tAI_y6y9su1lNTST3BWxSLX8/edit?usp=drivesdk
- Google Drive result artifacts: https://drive.google.com/drive/folders/1bFTa7zj9hZeBhmgAN0aeZqjb3QWKYxHA

## What is in GitHub

The repository contains only code, tests, reproducibility scripts, and documentation. Large raw and generated files are intentionally excluded from GitHub:

- raw assignment data: `documents/`;
- generated CSV/plot/report artifacts: `outputs/**`, except `.gitkeep` skeleton files.

Full generated results are delivered through the Google Drive folder above.

## Quick verification

```bash
git clone https://github.com/xsa-dev/senior-quantitative-researcher-assignment.git
cd senior-quantitative-researcher-assignment
make install
make test
```

`make all` requires the original raw input files under local `documents/`, which are not committed to GitHub.
