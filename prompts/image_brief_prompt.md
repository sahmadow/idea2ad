# Image Brief Generation Prompt

You are an expert Meta Ads creative strategist specializing in high-performing visual content. Generate 3 distinct image briefs for Meta Ads based on the provided marketing analysis and styling guide.

## INPUT DATA

**Marketing Analysis:**
- Summary: {summary}
- USP: {unique_selling_proposition}
- Pain Points: {pain_points}
- Call to Action: {call_to_action}
- Keywords: {keywords}
- Buyer Persona: {buyer_persona}

**Styling Guide:**
- Primary Colors: {primary_colors}
- Secondary Colors: {secondary_colors}
- Font Families: {font_families}
- Design Style: {design_style}
- Mood: {mood}

---

## YOUR TASK

Create 3 distinct image briefs using different creative approaches. Each brief must follow Meta Ads best practices and include explicit text overlay specifications.

### Creative Approaches

1. **Product-Focused**: Hero product shot with clear CTA
   - Showcase the product/service prominently
   - Clean, professional composition
   - Strong visual hierarchy with CTA

2. **Lifestyle**: Product in use, showing transformation/benefit
   - Show the product being used in real-life context
   - Emphasize the emotional benefit or transformation
   - Relatable, aspirational scenario

3. **Problem-Solution**: Before/after or pain point visualization
   - Visually represent the problem being solved
   - Show the contrast or transformation
   - Create urgency or desire for the solution

---

## META ADS BEST PRACTICES TO APPLY

1. **Mobile-First Design**: Ensure text is readable on small screens
2. **20% Text Rule**: Keep text overlay minimal (though not strictly enforced anymore, less is more)
3. **Clear CTA**: Make the call-to-action prominent and actionable
4. **Eye-Catching**: Use contrasting colors and bold visuals to stop the scroll
5. **Brand Consistency**: Match the landing page styling (colors, fonts, mood)
6. **Emotional Appeal**: Connect with the target audience's desires or pain points
7. **High Quality**: Professional, high-resolution imagery
8. **Focal Point**: Clear subject/focus that draws the eye immediately

---

## OUTPUT FORMAT

Return ONLY valid JSON with this exact structure:

```json
[
  {
    "approach": "product-focused",
    "visual_description": "Detailed description of the scene, composition, lighting, and visual elements. Be specific about what should be shown, camera angle, background, etc.",
    "styling_notes": "How to apply the landing page colors, fonts, and design style to this image. Be specific about which colors to use where.",
    "text_overlays": [
      {
        "content": "Exact text to display",
        "font_size": "large/medium/small or specific like 48px",
        "position": "top-left/top-center/top-right/center/bottom-left/bottom-center/bottom-right",
        "color": "#HEXCODE",
        "background": "Optional: semi-transparent overlay, gradient, or solid color"
      }
    ],
    "meta_best_practices": [
      "Mobile-first design with large, readable text",
      "Clear focal point on product",
      "Brand colors used for consistency"
    ],
    "rationale": "Why this approach works for this audience and product",
    "product_image_prompt": "A sleek wireless headphone in matte black finish"
  },
  {
    "approach": "lifestyle",
    "visual_description": "...",
    "styling_notes": "...",
    "text_overlays": [...],
    "meta_best_practices": [...],
    "rationale": "...",
    "product_image_prompt": "A modern laptop displaying analytics dashboard"
  },
  {
    "approach": "problem-solution",
    "visual_description": "...",
    "styling_notes": "...",
    "text_overlays": [...],
    "meta_best_practices": [...],
    "rationale": "...",
    "product_image_prompt": null
  }
]
```

---

## CRITICAL INSTRUCTIONS

1. **Use the styling guide**: All colors and fonts MUST come from the provided styling guide
2. **Be explicit about text overlays**: Specify exact content, size, position, and color for each text element
3. **Include clear CTAs**: Each image should have a prominent call-to-action
4. **Use keywords**: Incorporate the provided keywords naturally in text overlays
5. **Mobile-first**: All text must be readable on mobile devices (minimum 24px for body, 36px+ for headlines)
6. **Limit text**: Maximum 2-3 text overlays per image to avoid clutter
7. **Brand consistency**: The images should feel like they belong to the same brand as the landing page
8. **Different approaches**: Each brief must use a distinctly different creative strategy
9. **ALWAYS include product_image_prompt**: For each brief, you MUST provide a `product_image_prompt` field describing a single isolated product. Set to null only for abstract services with no tangible product.

---

## COLOR-PRECISE VISUAL DESCRIPTIONS

**CRITICAL: Be explicit about colors in the visual_description field.**

When specifying colors, ALWAYS include:
- The exact hex code from the styling guide
- A natural language color description

**BAD Examples:**
- "Use brand colors"
- "Professional background"
- "Matching the website style"

**GOOD Examples:**
- "The background is bright chartreuse yellow (#f0fb29)"
- "Accent elements use vibrant turquoise cyan (#5cf0e4)"
- "Clean white (#ffffff) background with dark navy (#1a1a2e) text"

**Visual Description Format:**
Include color specifications naturally in the scene description:

"[Scene description]. The dominant background color is {primary_color} ({hex}). Key visual elements use {accent_color} ({hex}). The overall aesthetic is {design_style} with a {mood} feel."

**Example:**
"A modern workspace with a laptop displaying analytics charts. The scene has a dominant bright yellow (#f0fb29) background with cyan (#5cf0e4) accent highlights on key data points. Clean, minimal composition with the laptop as the hero element in the upper two-thirds, leaving the bottom clear for text overlay."

---

## TEXT OVERLAY GUIDELINES

- **Headlines**: 36-60px, bold, primary brand color, top-third or center
- **Subheadlines**: 24-36px, medium weight, secondary color, below headline
- **CTAs**: 28-48px, bold, high-contrast color, bottom-third or prominent position
- **Position options**: top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, bottom-right
- **Background options**: "semi-transparent black", "gradient from {color1} to {color2}", "solid {color}", or null for no background

---

## PRODUCT IMAGE PROMPT

Include a `product_image_prompt` field describing a SINGLE isolated product/item to display in the ad:

**Guidelines:**
- Describe a SPECIFIC, concrete product (not abstract concepts)
- Include material, color, and style details
- Focus on a SINGLE object (no scenes, no people)
- Match the brand aesthetic
- Keep description concise (1-2 sentences)

**Good Examples:**
- SaaS: "A modern laptop displaying colorful analytics dashboard"
- E-commerce: "A premium leather crossbody handbag in burgundy with gold hardware"
- Food: "A glass bottle of cold-pressed green juice with condensation"
- Fitness: "A pair of sleek running shoes in neon green and black"

**When to set `product_image_prompt` to null:**
- Abstract services (consulting, coaching, coaching)
- Problem-solution layouts where the focus is on text/contrast
- When no tangible product representation makes sense
