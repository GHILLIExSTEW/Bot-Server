"""
Icon converter utility for DBSBM Service Manager
Converts favicon.webp to .ico format for Windows compatibility
"""

import os
from pathlib import Path

def convert_favicon():
    """Convert webp favicon to ico format"""
    base_dir = Path(__file__).parent
    webp_path = base_dir / "StaticFiles" / "DBSBMWEB" / "static" / "favicon.webp"
    ico_path = base_dir / "dbsbm_icon.ico"
    
    if not webp_path.exists():
        print(f"Favicon not found at: {webp_path}")
        return False
    
    try:
        from PIL import Image
        
        # Open and convert
        with Image.open(webp_path) as img:
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Resize to standard icon sizes
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
            icons = []
            
            for size in sizes:
                resized = img.resize(size, Image.Resampling.LANCZOS)
                icons.append(resized)
            
            # Save as ICO
            icons[0].save(ico_path, format='ICO', sizes=[img.size for img in icons])
            print(f"Icon converted successfully: {ico_path}")
            return True
            
    except ImportError:
        print("Pillow not installed. Install with: pip install Pillow")
        return False
    except Exception as e:
        print(f"Error converting icon: {e}")
        return False

if __name__ == "__main__":
    convert_favicon()
