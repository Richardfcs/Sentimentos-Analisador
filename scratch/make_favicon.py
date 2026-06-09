from PIL import Image
import os

def crop_favicon():
    logo_path = 'static/logo.png'
    favicon_path = 'static/favicon.ico'
    
    if not os.path.exists(logo_path):
        print(f"Error: {logo_path} not found.")
        return
        
    img = Image.open(logo_path)
    width, height = img.size
    print(f"Loaded logo: {width}x{height}, mode={img.mode}")
    
    # If the image has an alpha channel, use it. Otherwise, use luminance.
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        alpha = img.convert('RGBA').split()[-1]
    else:
        alpha = img.convert('L')
        
    # Analyze columns to find the boundaries of the brain icon
    # The brain icon is on the left. Let's scan columns from x=0 to x=width//2.
    left_limit = width // 2
    
    # Find columns that contain non-transparent pixels
    col_has_content = []
    for x in range(left_limit):
        has_content = False
        for y in range(height):
            if alpha.getpixel((x, y)) > 10:  # threshold of transparency
                has_content = True
                break
        col_has_content.append(has_content)
        
    # Find the left edge of the brain icon
    brain_start_x = 0
    for x in range(left_limit):
        if col_has_content[x]:
            brain_start_x = x
            break
            
    # Find the right edge of the brain icon
    # We look for a gap of consecutive empty columns or the end of the left half.
    brain_end_x = left_limit
    empty_streak = 0
    for x in range(brain_start_x, left_limit):
        if not col_has_content[x]:
            empty_streak += 1
            if empty_streak >= 15:  # 15 consecutive empty columns indicate a gap
                brain_end_x = x - empty_streak
                break
        else:
            empty_streak = 0
            
    print(f"Detected brain icon horizontal boundaries: x = {brain_start_x} to {brain_end_x}")
    
    # Find vertical boundaries of the brain icon within the horizontal boundaries
    brain_start_y = 0
    brain_end_y = height
    
    row_has_content = []
    for y in range(height):
        has_content = False
        for x in range(brain_start_x, brain_end_x):
            if alpha.getpixel((x, y)) > 10:
                has_content = True
                break
        row_has_content.append(has_content)
        
    for y in range(height):
        if row_has_content[y]:
            brain_start_y = y
            break
            
    for y in range(height - 1, -1, -1):
        if row_has_content[y]:
            brain_end_y = y + 1
            break
            
    print(f"Detected brain icon vertical boundaries: y = {brain_start_y} to {brain_end_y}")
    
    # Crop the brain icon
    brain_w = brain_end_x - brain_start_x
    brain_h = brain_end_y - brain_start_y
    print(f"Brain icon bounding box: {brain_w}x{brain_h}")
    
    # We want a square crop. Let's make it square by adding padding or expanding the crop.
    size = max(brain_w, brain_h)
    center_x = brain_start_x + brain_w // 2
    center_y = brain_start_y + brain_h // 2
    
    # Determine crop coordinates
    crop_left = max(0, center_x - size // 2)
    crop_top = max(0, center_y - size // 2)
    crop_right = min(width, crop_left + size)
    crop_bottom = min(height, crop_top + size)
    
    # If it hits the boundaries and isn't square, adjust
    crop_w = crop_right - crop_left
    crop_h = crop_bottom - crop_top
    crop_size = min(crop_w, crop_h)
    
    crop_left = center_x - crop_size // 2
    crop_top = center_y - crop_size // 2
    crop_right = crop_left + crop_size
    crop_bottom = crop_top + crop_size
    
    print(f"Cropping square area: ({crop_left}, {crop_top}, {crop_right}, {crop_bottom}) of size {crop_size}x{crop_size}")
    
    cropped_brain = img.crop((crop_left, crop_top, crop_right, crop_bottom))
    
    # Create sizes for the favicon.ico
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    
    # Save as ICO with multiple sizes
    cropped_brain.save(favicon_path, format='ICO', sizes=sizes)
    print(f"Saved multi-size favicon to {favicon_path}")

if __name__ == '__main__':
    crop_favicon()
