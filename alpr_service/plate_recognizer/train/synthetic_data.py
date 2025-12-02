"""
Synthetic Thai License Plate Generator with Bounding Box Labels
Generates synthetic Thai license plates with:
- Thai characters and numbers in license plate format
- Province names (77 provinces)
- Homography transformation for distortion
- Data augmentation (translation, rotation, scaling)
- Bicubic interpolation for sharpness
- Bounding box annotations for license number (top) and province (bottom)
"""

import os
import random
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import argparse
from typing import Tuple, List, Dict, Optional


# Thai provinces (77 provinces)
THAI_PROVINCES = [
    "กระบี่", "กรุงเทพมหานคร", "กาญจนบุรี", "กาฬสินธุ์", "กำแพงเพชร",
    "ขอนแก่น", "จันทบุรี", "จำปาศักดิ์", "ฉะเชิงเทรา", "ชลบุรี",
    "ชัยนาท", "ชัยภูมิ", "ชุมพร", "เชียงราย", "เชียงใหม่",
    "ตรัง", "ตราด", "ตาก", "นครนายก", "นครปฐม",
    "นครพนม", "นครราชสีมา", "นครศรีธรรมราช", "นครสวรรค์", "นนทบุรี",
    "นราธิวาส", "น่าน", "บึงกาฬ", "บุรีรัมย์", "ปทุมธานี",
    "ประจวบคีรีขันธ์", "ปราจีนบุรี", "ปัตตานี", "พระนครศรีอยุธยา", "พังงา",
    "พัทลุง", "พิจิตร", "พิษณุโลก", "เพชรบุรี", "เพชรบูรณ์",
    "แพร่", "พะเยา", "ภูเก็ต", "มหาสารคาม", "มุกดาหาร",
    "แม่ฮ่องสอน", "ยโสธร", "ยะลา", "ร้อยเอ็ด", "ระนอง",
    "ระยอง", "ราชบุรี", "ลพบุรี", "ลำปาง", "ลำพูน",
    "เลย", "ศรีสะเกษ", "สกลนคร", "สงขลา", "สตูล",
    "สมุทรปราการ", "สมุทรสงคราม", "สมุทรสาคร", "สระแก้ว", "สระบุรี",
    "สิงห์บุรี", "สุโขทัย", "สุพรรณบุรี", "สุราษฎร์ธานี", "สุรินทร์",
    "หนองคาย", "หนองบัวลำภู", "อ่างทอง", "อุดรธานี", "อุทัยธานี",
    "อุตรดิตถ์", "อุบลราชธานี", "อำนาจเจริญ"
]

# Thai consonants commonly used in license plates
THAI_CONSONANTS = [
    "ก", "ข", "ค", "ง", "จ", "ฉ", "ช", "ซ", "ฌ", "ญ",
    "ฎ", "ฏ", "ฐ", "ฑ", "ฒ", "ณ", "ด", "ต", "ถ", "ท",
    "ธ", "น", "บ", "ป", "ผ", "ฝ", "พ", "ฟ", "ภ", "ม",
    "ย", "ร", "ล", "ว", "ศ", "ษ", "ส", "ห", "ฬ", "อ", "ฮ"
]

# Common Thai words for synthetic data (sample dictionary)
THAI_WORDS = [
    "กรุงเทพ", "ไทย", "รถ", "บ้าน", "เมือง", "คน", "น้ำ", "ฟ้า",
    "ดิน", "ไฟ", "ลม", "ป่า", "ภูเขา", "ทะเล", "แม่น้ำ", "ดอกไม้",
    "ต้นไม้", "สวน", "ถนน", "สะพาน", "วัด", "โรงเรียน", "โรงพยาบาล",
    "ตลาด", "ร้านค้า", "อาหาร", "ข้าว", "น้ำตาล", "เกลือ", "พริก",
    "หมู", "ไก่", "เป็ด", "ปลา", "กุ้ง", "ปู", "ผัก", "ผลไม้"
]

# Thai words for special/vanity license plates (ป้ายทะเบียนพิเศษ)
# These words have meaning and often include vowels above/below characters
THAI_SPECIAL_WORDS = [
    # คำมงคล (Auspicious words)
    "รวย", "โชค", "ดี", "เฮง", "เจริญ", "สุข", "ศรี", "มั่ง", "มี", "โภค",
    "ทรัพย์", "สมบูรณ์", "เจริญ", "รุ่ง", "เรือง", "วัฒนา", "พัฒนา",
    # คำที่น่าสนใจ (Interesting words)
    "หล่อ", "สวย", "เท่", "เจ๋ง", "เฟี้ยว", "ว้าว", "โอ้โห",
    # คำทั่วไป (Common words)
    "รัก", "หวัง", "ฝัน", "ใจ", "คิด", "เชื่อ", "ไว้", "ได้", "เอา",
    "ไป", "มา", "อยู่", "เป็น", "ทำ", "ให้", "กับ", "แล้ว", "เพื่อ",
    # คำสั้น (Short words)
    "ฟ้า", "ดิน", "น้ำ", "ไฟ", "ลม", "ดอก", "ใบ", "เมฆ", "ฝน", "แดด"
]


class ThaiLicensePlateGenerator:
    """Generate synthetic Thai license plates with bounding box labels"""
    
    def __init__(
        self,
        output_dir: str = "synthetic_plates",
        image_width: int = 340,
        image_height: int = 150,
        font_path: Optional[str] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        
        self.image_width = image_width
        self.image_height = image_height
        
        # Try to load Thai font
        self.font_path = font_path or self._find_thai_font()
        self.load_fonts()
        
    def _find_thai_font(self) -> str:
        """Find available Thai font on the system"""
        possible_fonts = [
            "C:/Users/PC/AppData/Local/Microsoft/Windows/Fonts/Sarun's ThangLuang.ttf",  # Default Windows Thai font
            "C:/Windows/Fonts/THSarabunNew.ttf",
            "C:/Windows/Fonts/THSarabun Bold.ttf",
            "/usr/share/fonts/truetype/tlwg/Sarabun-Bold.ttf",
            "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
            "/System/Library/Fonts/Thonburi.ttc",  # macOS
        ]
        
        for font in possible_fonts:
            if os.path.exists(font):
                print(f"Using font: {font}")
                return font
        
        print("Warning: No Thai font found, using default")
        return None
    
    def load_fonts(self):
        """Load fonts for license plate text"""
        try:
            if self.font_path:
                # License number (top) - same size for chars and digits for better alignment
                self.font_large = ImageFont.truetype(self.font_path, 50)
                # Province name (bottom) - larger for better visibility
                self.font_small = ImageFont.truetype(self.font_path, 30)
            else:
                self.font_large = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
        except Exception as e:
            print(f"Error loading font: {e}")
            self.font_large = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
    
    def generate_plate_text(self, special_plate_ratio: float = 0.0) -> Tuple[str, str]:
        """
        Generate Thai license plate text
        Returns: (license_number, province)
        
        Format: 
        - Standard: 2-3 Thai consonants + 4 digits (e.g., "กข 1234" or "กขค 5678")
        - Special: Thai word + 3-4 digits (e.g., "หล่อ 999" or "รวย 1234")
        
        Args:
            special_plate_ratio: Probability of generating special/vanity plates (0.0 to 1.0)
        """
        # Decide whether to generate special plate
        use_special = random.random() < special_plate_ratio
        
        if use_special:
            # Generate special/vanity license plate
            word = random.choice(THAI_SPECIAL_WORDS)
            # Special plates often have 3 digits, but can have 4
            num_digits = random.choice([3, 3, 3, 4])  # 75% chance for 3 digits
            digits = ''.join([str(random.randint(0, 9)) for _ in range(num_digits)])
            license_number = f"{word} {digits}"
        else:
            # Generate standard license number: 2-3 Thai consonants + space + 4 digits
            num_consonants = random.choice([2, 3])
            consonants = ''.join(random.choices(THAI_CONSONANTS, k=num_consonants))
            digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            license_number = f"{consonants} {digits}"
        
        # Select random province
        province = random.choice(THAI_PROVINCES)
        
        return license_number, province
    
    def generate_background_color(self) -> Tuple[int, int, int]:
        """Generate random background color for license plate"""
        # Common Thai license plate colors (more realistic)
        colors = [
            (255, 255, 255),  # White (most common - personal vehicles)
            (255, 235, 100),  # Yellow (taxi)
            (255, 180, 90),   # Orange (motorcycle taxi)
            (120, 255, 120),  # Light green (government)
        ]
        
        # 80% chance for white (most common), 20% for others
        if random.random() < 0.8:
            return colors[0]
        else:
            return random.choice(colors[1:])
    
    def create_plate_image(
        self,
        license_number: str,
        province: str
    ) -> Tuple[Image.Image, Dict]:
        """
        Create license plate image with text
        Returns: (image, bounding_boxes)
        """
        # Create blank image with background color
        bg_color = self.generate_background_color()
        img = Image.new('RGB', (self.image_width, self.image_height), bg_color)
        draw = ImageDraw.Draw(img)

        # Add border
        border_color = (0, 0, 0)
        border_width = 3
        draw.rectangle(
            [0, 0, self.image_width-1, self.image_height-1],
            outline=border_color,
            width=border_width
        )

        # Text color (black on light background)
        text_color = (0, 0, 0)

        # Draw license number (top, centered) - Use same font size for all characters
        # This ensures perfect alignment between Thai chars and digits
        try:
            bbox_license = draw.textbbox((0, 0), license_number, font=self.font_large, anchor='lt')
            license_width = bbox_license[2] - bbox_license[0]
            license_height = bbox_license[3] - bbox_license[1]
            license_offset_y = -bbox_license[1]  # offset to start from actual top
        except:
            license_width = len(license_number) * 35
            license_height = 50
            license_offset_y = 0

        license_x = (self.image_width - license_width) // 2
        license_y = 30  # Top position like real Thai plates
        
        # Draw license number with top-left anchor for precise positioning
        draw.text(
            (license_x, license_y + license_offset_y),
            license_number,
            font=self.font_large,
            fill=text_color,
            anchor='lt'
        )

        # Calculate actual bounding box for license
        license_bbox_x_min = license_x
        license_bbox_y_min = license_y
        license_bbox_x_max = license_x + license_width
        license_bbox_y_max = license_y + license_height

        # Draw province name (bottom, centered) - More space from bottom
        try:
            bbox_province = draw.textbbox((0, 0), province, font=self.font_small, anchor='lt')
            province_width = bbox_province[2] - bbox_province[0]
            province_height = bbox_province[3] - bbox_province[1]
            province_offset_y = -bbox_province[1]  # offset to align top
        except:
            province_width = len(province) * 15
            province_height = 25
            province_offset_y = 0

        province_x = (self.image_width - province_width) // 2
        # Position province name near bottom with safe margin
        province_y = self.image_height - province_height - 20

        draw.text(
            (province_x, province_y + province_offset_y),
            province,
            font=self.font_small,
            fill=text_color,
            anchor='lt'
        )

        # Create bounding boxes (normalized coordinates [0, 1])
        bounding_boxes = {
            "license": {
                "x_min": license_bbox_x_min / self.image_width,
                "y_min": license_bbox_y_min / self.image_height,
                "x_max": license_bbox_x_max / self.image_width,
                "y_max": license_bbox_y_max / self.image_height,
                "text": license_number
            },
            "province": {
                "x_min": province_x / self.image_width,
                "y_min": province_y / self.image_height,
                "x_max": (province_x + province_width) / self.image_width,
                "y_max": (province_y + province_height) / self.image_height,
                "text": province
            }
        }

        return img, bounding_boxes
    
    def apply_homography(self, img: np.ndarray) -> np.ndarray:
        """
        Apply homography transformation to simulate perspective distortion
        """
        height, width = img.shape[:2]
        
        # Define random perspective transformation
        # Source points (corners of the image)
        src_points = np.float32([
            [0, 0],
            [width, 0],
            [width, height],
            [0, height]
        ])
        
        # Destination points (with random distortion)
        distortion = random.uniform(0.05, 0.15)
        dst_points = np.float32([
            [random.uniform(0, width*distortion), random.uniform(0, height*distortion)],
            [width - random.uniform(0, width*distortion), random.uniform(0, height*distortion)],
            [width - random.uniform(0, width*distortion), height - random.uniform(0, height*distortion)],
            [random.uniform(0, width*distortion), height - random.uniform(0, height*distortion)]
        ])
        
        # Calculate homography matrix
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        # Apply transformation
        transformed = cv2.warpPerspective(img, matrix, (width, height), 
                                         flags=cv2.INTER_CUBIC,
                                         borderMode=cv2.BORDER_REPLICATE)
        
        return transformed
    
    def apply_augmentation(self, img: np.ndarray) -> np.ndarray:
        """
        Apply data augmentation: translation, rotation, scaling
        """
        height, width = img.shape[:2]
        
        # Random rotation (-15 to 15 degrees)
        angle = random.uniform(-15, 15)
        rotation_matrix = cv2.getRotationMatrix2D((width/2, height/2), angle, 1.0)
        img = cv2.warpAffine(img, rotation_matrix, (width, height),
                            flags=cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REPLICATE)
        
        # Random scaling (0.8 to 1.2)
        scale = random.uniform(0.85, 1.15)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Crop or pad to original size
        if scale > 1.0:
            # Crop center
            start_x = (new_width - width) // 2
            start_y = (new_height - height) // 2
            img = img[start_y:start_y+height, start_x:start_x+width]
        else:
            # Pad with border color
            pad_x = (width - new_width) // 2
            pad_y = (height - new_height) // 2
            img = cv2.copyMakeBorder(img, pad_y, height-new_height-pad_y,
                                    pad_x, width-new_width-pad_x,
                                    cv2.BORDER_REPLICATE)
        
        # Random translation (-20 to 20 pixels)
        tx = random.randint(-20, 20)
        ty = random.randint(-10, 10)
        translation_matrix = np.float32([[1, 0, tx], [0, 1, ty]])
        img = cv2.warpAffine(img, translation_matrix, (width, height),
                            borderMode=cv2.BORDER_REPLICATE)
        
        return img
    
    def add_noise_and_blur(self, img: np.ndarray) -> np.ndarray:
        """Add random noise and blur to make image more realistic"""
        # Add Gaussian noise
        if random.random() < 0.3:
            noise = np.random.normal(0, random.uniform(5, 15), img.shape)
            img = np.clip(img + noise, 0, 255).astype(np.uint8)
        
        # Add blur
        if random.random() < 0.3:
            kernel_size = random.choice([3, 5])
            img = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)
        
        # Adjust brightness
        if random.random() < 0.3:
            factor = random.uniform(0.7, 1.3)
            img = np.clip(img * factor, 0, 255).astype(np.uint8)
        
        return img
    
    def apply_bicubic_interpolation(self, img: np.ndarray, scale: float = 0.5) -> np.ndarray:
        """
        Apply bicubic interpolation to adjust image sharpness
        Downscale then upscale to simulate different quality levels
        """
        height, width = img.shape[:2]
        
        # Downscale
        small = cv2.resize(img, (int(width*scale), int(height*scale)),
                          interpolation=cv2.INTER_CUBIC)
        
        # Upscale back to original size
        img = cv2.resize(small, (width, height), interpolation=cv2.INTER_CUBIC)
        
        return img
    
    def generate_sample(
        self,
        index: int,
        apply_transforms: bool = True,
        special_plate_ratio: float = 0.0
    ) -> Dict:
        """
        Generate a single synthetic license plate sample for TrOCR training
        Returns: metadata dictionary matching train_trocr.py CSV format
        
        Note: Bounding boxes are NOT needed for TrOCR training as it reads the entire image.
        """
        # Generate text
        license_number, province = self.generate_plate_text(special_plate_ratio)
        
        # Create base image (we don't need bboxes for TrOCR)
        img_pil, _ = self.create_plate_image(license_number, province)
        
        # Convert to numpy array
        img_np = np.array(img_pil)
        
        if apply_transforms:
            # Apply homography transformation
            if random.random() < 0.7:
                img_np = self.apply_homography(img_np)
            
            # Apply augmentation
            if random.random() < 0.8:
                img_np = self.apply_augmentation(img_np)
            
            # Apply bicubic interpolation (simulate different quality)
            if random.random() < 0.5:
                scale = random.uniform(0.4, 0.8)
                img_np = self.apply_bicubic_interpolation(img_np, scale)
            
            # Add noise and blur
            img_np = self.add_noise_and_blur(img_np)
        
        # Save image with relative path format matching training data
        image_filename = f"synthetic_{index:06d}.jpg"
        image_path = self.images_dir / image_filename
        cv2.imwrite(str(image_path), cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR))
        
        # Map province name to province code (use TH-XX format)
        province_code = f"TH-{THAI_PROVINCES.index(province) + 1:02d}"
        
        # Create CSV row data matching train_trocr.py format
        # Only includes fields actually used by TrOCR training
        label_data = {
            "plate": license_number,
            "province_code": province_code,
            "province_description": province,
            "image_name_gray": f"images/{image_filename}",
        }
        
        return label_data
    
    def generate_dataset(
        self,
        num_samples: int = 1000,
        apply_transforms: bool = True,
        special_plate_ratio: float = 0.0
    ):
        """Generate a complete dataset of synthetic license plates"""
        print(f"Generating {num_samples} synthetic license plates...")
        print(f"Output directory: {self.output_dir}")
        if special_plate_ratio > 0:
            print(f"Special/vanity plate ratio: {special_plate_ratio*100:.0f}%")
        
        metadata = []
        
        for i in range(num_samples):
            try:
                label_data = self.generate_sample(i, apply_transforms, special_plate_ratio)
                metadata.append(label_data)
                
                if (i + 1) % 100 == 0:
                    print(f"Generated {i + 1}/{num_samples} samples")
            
            except Exception as e:
                print(f"Error generating sample {i}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Save as CSV file matching training data format
        csv_path = self.output_dir / "synthetic_plates.csv"
        
        # Write CSV header and data
        import csv
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            # Define CSV columns matching train_trocr.py requirements
            # Note: Bounding boxes removed as TrOCR doesn't need them
            fieldnames = [
                'plate',
                'province_code',
                'province_description',
                'image_name_gray'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in metadata:
                writer.writerow(row)
        
        print(f"\nDataset generation complete!")
        print(f"- Images: {self.images_dir}")
        print(f"- CSV file: {csv_path}")
        print(f"- Total samples: {len(metadata)}")
        print(f"- Image size: {self.image_width}x{self.image_height}")
        print(f"\nYou can now use this CSV file for training with train_trocr.py")
        print(f"Example command:")
        print(f"  python train/train_trocr.py --csv {csv_path} --data-root {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic Thai license plates with bounding box labels"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="synthetic_plates",
        help="Output directory for generated data"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=100,
        help="Number of samples to generate"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=340,
        help="Image width (default: 340, matching real Thai license plates)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=150,
        help="Image height (default: 150, matching real Thai license plates)"
    )
    parser.add_argument(
        "--font-path",
        type=str,
        default=None,
        help="Path to Thai font file (.ttf)"
    )
    parser.add_argument(
        "--no-transforms",
        action="store_true",
        help="Disable transformations (for debugging)"
    )
    parser.add_argument(
        "--special-ratio",
        type=float,
        default=0.0,
        help="Ratio of special/vanity plates (0.0-1.0, default: 0.0)"
    )
    
    args = parser.parse_args()
    
    # Create generator
    generator = ThaiLicensePlateGenerator(
        output_dir=args.output_dir,
        image_width=args.width,
        image_height=args.height,
        font_path=args.font_path
    )
    
    # Generate dataset
    generator.generate_dataset(
        num_samples=args.num_samples,
        apply_transforms=not args.no_transforms,
        special_plate_ratio=args.special_ratio
    )


if __name__ == "__main__":
    main()
