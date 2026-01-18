# Ad Template Specifications

## Product Image Generation

### Imagen Prompt (image_gen.py)
```
Professional product photography, isolated product shot.

SUBJECT: {product_prompt}

REQUIREMENTS:
- Single product centered, solid white background (#ffffff)
- Professional studio lighting, sharp focus
- No text, no watermarks, no other objects
- Product fills 70-80% of frame
- High contrast edges for easy background removal

STYLE: Commercial product photography, 4K quality
```

### Background Removal
- Service: rembg with u2net model
- Alpha matting enabled for clean edges
- Foreground threshold: 240
- Background threshold: 10

---

## Product Image Display (CSS)

### Key Approach: CSS Transform Scale
Product images are scaled 3x using CSS transform to maintain layout while enlarging the visual:

```css
.product-image {
    max-width: 85%;
    max-height: 262px;
    object-fit: contain;
    filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.18));
    transform: scale(3);  /* 3x visual enlargement */
    transform-origin: center center;
}
```

### Why This Approach
- `transform: scale(3)` enlarges the image visually without affecting flex layout
- Text, CTA, and background remain in original positions
- Product image overlays naturally in center of ad
- Drop shadow adds depth and separation

---

## Template Variants

### 1. product_focused.html
- Layout: Vertical stack (content → product → CTA)
- Product max-height: 262px (scaled 3x = ~786px visual)
- Best for: Direct product showcase

### 2. lifestyle.html
- Layout: Top section → product → bottom CTA
- Product max-height: 262px (scaled 3x)
- Best for: Emotional/aspirational messaging

### 3. problem_solution.html
- Layout: Split (problem top → solution bottom with product)
- Product max-height: 220px (scaled 3x = ~660px visual)
- Best for: Before/after, pain point messaging

---

## Text Overlay Extraction

### Subheadline Filtering
CTA-like text is excluded from subheadlines to avoid duplication:
```python
cta_keywords = ["learn", "get", "try", "start", "buy", "shop", "sign", "join", "discover"]
```

---

## Canvas Dimensions

| Aspect Ratio | Dimensions |
|--------------|------------|
| 1:1          | 1080x1080  |
| 4:5          | 1080x1350  |
| 9:16         | 1080x1920  |

Device scale factor: 2x (retina quality)
