import os
from pathlib import Path
from PIL import Image

def get_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)

def optimize_image(img_path):
    path = Path(img_path)
    size_kb = os.path.getsize(path) / 1024
    
    # Ignore icons < 50 KB (just copy them to webp? or just skip?)
    # Wait, the HTML will be updated to point to .webp, so we should convert them all to WebP, 
    # but not resize if small.
    
    with Image.open(path) as img:
        width, height = img.size
        new_width, new_height = width, height
        
        # Resizing rules
        if "team_" in path.name.lower():
            # Fotos de equipe: 208x300
            new_width, new_height = 208, 300
        elif width > 1600:
            # Hero images: max 1600px width
            ratio = 1600 / width
            new_width = 1600
            new_height = int(height * ratio)
            
        if (new_width, new_height) != (width, height):
            # Use Resampling.LANCZOS for high quality downsampling
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        # Convert to RGB if necessary (e.g. RGBA) before saving as WebP
        # But WebP supports RGBA! So we can just save it.
        
        out_path = path.with_suffix('.webp')
        img.save(out_path, format='webp', quality=82)
        
        return path, out_path, size_kb, os.path.getsize(out_path) / 1024

def main():
    static_dir = Path("static")
    if not static_dir.exists():
        print("Diretório static/ não encontrado!")
        return

    print("Iniciando otimização de imagens...")
    print("-" * 50)
    
    total_original = 0
    total_optimized = 0
    
    for path in static_dir.rglob("*.png"):
        try:
            original, optimized, orig_kb, opt_kb = optimize_image(path)
            total_original += orig_kb
            total_optimized += opt_kb
            reduction = (1 - (opt_kb / orig_kb)) * 100
            print(f"[OK] {original.name}: {orig_kb:.1f} KB -> {opt_kb:.1f} KB (-{reduction:.1f}%)")
        except Exception as e:
            print(f"[ERRO] Erro ao otimizar {path.name}: {e}")
            
    print("-" * 50)
    print(f"Total original: {total_original / 1024:.2f} MB")
    print(f"Total otimizado: {total_optimized / 1024:.2f} MB")
    
if __name__ == "__main__":
    main()
