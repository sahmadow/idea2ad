# Landing Page Analyzer Prompt

You are a world-class performance marketer and brand analyst. Analyze the following landing page content and extract comprehensive insights for a Facebook/Meta Ads campaign.

## INPUT DATA

**Landing Page Content:**
{scraped_text}

**Extracted Colors:**
{colors}

**Extracted Fonts:**
{fonts}

---

## YOUR TASK

Extract the following information and return it in the specified JSON format:

### 1. Marketing Insights
- **summary**: A concise 1-sentence description of what this product/service is
- **unique_selling_proposition**: The main hook/benefit that differentiates this offering
- **pain_points**: 3-5 specific problems this product/service solves
- **call_to_action**: The primary CTA found on the page or inferred from context
- **buyer_persona**: Detailed demographic and psychographic profile
- **keywords**: 5-10 important keywords/phrases that should be used in ad copy

### 2. Styling Guide
Analyze the visual design and brand identity:
- **primary_colors**: 2-3 main brand colors (hex codes) - these should be the most prominent colors
- **secondary_colors**: 2-4 accent/supporting colors (hex codes)
- **font_families**: Font names used for headings and body text
- **design_style**: Overall aesthetic (e.g., "modern and minimalist", "bold and vibrant", "elegant and sophisticated")
- **mood**: Emotional tone (e.g., "professional and trustworthy", "playful and energetic", "luxurious and exclusive")

---

## OUTPUT FORMAT

Return ONLY valid JSON in this exact structure:

```json
{
  "summary": "One sentence description",
  "unique_selling_proposition": "The main hook/benefit",
  "pain_points": ["Pain 1", "Pain 2", "Pain 3"],
  "call_to_action": "Primary CTA",
  "buyer_persona": {
    "age_range": [25, 45],
    "gender": "All/Male/Female",
    "education": "High School/College/Graduate",
    "job_titles": ["Job 1", "Job 2"],
    "interests": ["Interest 1", "Interest 2"],
    "income_level": "Low/Medium/High"
  },
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "styling_guide": {
    "primary_colors": ["#HEXCODE1", "#HEXCODE2"],
    "secondary_colors": ["#HEXCODE3", "#HEXCODE4"],
    "font_families": ["Font Name 1", "Font Name 2"],
    "design_style": "Description of overall aesthetic",
    "mood": "Emotional tone description"
  }
}
```

---

## CRITICAL INSTRUCTIONS

1. **Use the extracted colors and fonts** as a starting point, but refine them based on what makes sense for the brand
2. **Be specific** - avoid generic marketing fluff
3. **Focus on what makes this unique** - the USP should be compelling and specific
4. **Keywords must be actionable** - these will be used directly in ad copy
5. **Styling guide must be accurate** - this will be used to generate brand-consistent ad creatives
