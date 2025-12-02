# Synthetic Thai License Plate Generator

This script generates synthetic images of Thai license plates for use in OCR model training (e.g., TrOCR). It supports both standard and special/vanity plate formats, applies various augmentations, and outputs a CSV file compatible with TrOCR training scripts.

## Features

- Generates realistic Thai license plate images with random text and province names
- Supports both standard plates (e.g., กข 1234) and special/vanity plates (e.g., หล่อ 999)
- Applies data augmentation: perspective distortion, rotation, scaling, translation, noise, blur, and brightness adjustment
- Uses a Thai font for accurate rendering (customizable via `--font-path`)
- Outputs a CSV file with fields required for TrOCR: `plate`, `province_code`, `province_description`, `image_name_gray`
- Images and CSV are saved in a specified output directory

## Requirements

- Python 3.x
- [Pillow](https://python-pillow.org/)
- [OpenCV](https://opencv.org/)
- [numpy](https://numpy.org/)
- Thai font file (e.g., Sarun's ThangLuang.ttf, THSarabunNew.ttf)

Install dependencies:

```bash
pip install pillow opencv-python numpy
```

## Usage

Run the script from the project root or the `train` directory:

```bash
python train/synthetic_data.py [OPTIONS]
```

### Options

- `--output-dir` Output directory for generated data (default: `synthetic_plates`)
- `--num-samples` Number of samples to generate (default: 100)
- `--width` Image width in pixels (default: 340)
- `--height` Image height in pixels (default: 150)
- `--font-path` Path to a Thai font file (.ttf) (optional)
- `--no-transforms` Disable all image augmentations (for debugging)
- `--special-ratio` Ratio of special/vanity plates (0.0-1.0, default: 0.0)

### Example

Generate 1000 images with 20% special plates and a custom font:

```bash
python train/synthetic_data.py --num-samples 1000 --output-dir synthetic_plates_trocr --special-ratio 0.2 --font-path "C:/Users/PC/AppData/Local/Microsoft/Windows/Fonts/Sarun's ThangLuang.ttf"
```

## Output

- Images are saved in `[output-dir]/images/`
- CSV file is saved as `[output-dir]/synthetic_plates.csv`
- Each CSV row contains:
  - `plate`: License plate text (e.g., กข 1234 or หล่อ 999)
  - `province_code`: Province code (e.g., TH-01)
  - `province_description`: Province name in Thai
  - `image_name_gray`: Relative path to the image file

## Notes

- Bounding box information is not included, as TrOCR requires only the full image and label.
- The script will attempt to auto-detect a Thai font if `--font-path` is not provided, but specifying a font is recommended for best results.
- You can use the generated CSV directly with your TrOCR training script.

## Example TrOCR Training Command

```bash
python train/train_trocr.py --csv synthetic_plates.csv --data-root synthetic_plates
```

---

**Author:** Tanaphat-Ken

For questions or improvements, please open an issue or contact the repository maintainer.
