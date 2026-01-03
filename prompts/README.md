# Prompts Directory

This directory contains all AI prompts used by the Idea2Ad platform. These prompts are stored as markdown files for easy editing and version control.

## Available Prompts

### `analyzer_prompt.md`
**Purpose**: Analyzes landing page content to extract marketing insights and styling guide.

**Variables**:
- `{scraped_text}`: Full text content from the landing page
- `{colors}`: List of colors extracted from the page CSS
- `{fonts}`: List of fonts extracted from the page CSS

**Output**: JSON with marketing analysis and styling guide

**When to Edit**: 
- To improve the quality of marketing insights
- To adjust styling guide extraction logic
- To add new analysis fields

---

### `image_brief_prompt.md`
**Purpose**: Generates 3 distinct image briefs with explicit text overlay specifications following Meta ads best practices.

**Variables**:
- `{summary}`: Product/service summary
- `{unique_selling_proposition}`: Main USP
- `{pain_points}`: List of pain points
- `{call_to_action}`: Primary CTA
- `{keywords}`: Important keywords
- `{buyer_persona}`: Target audience details
- `{primary_colors}`: Brand primary colors
- `{secondary_colors}`: Brand secondary colors
- `{font_families}`: Brand fonts
- `{design_style}`: Overall design aesthetic
- `{mood}`: Emotional tone

**Output**: JSON array with 3 image briefs

**When to Edit**:
- To adjust creative approaches
- To modify Meta ads best practices
- To change text overlay specifications
- To improve image generation quality

---

## How to Edit Prompts

1. **Open the prompt file** in your text editor
2. **Modify the instructions** while keeping the variable placeholders intact (e.g., `{scraped_text}`)
3. **Test your changes** by running the application and checking the output quality
4. **Iterate** based on results

## Best Practices

- **Keep variables intact**: Don't change `{variable_name}` placeholders
- **Be specific**: Clear, detailed instructions produce better results
- **Use examples**: Show the AI what good output looks like
- **Test thoroughly**: Always verify changes with real landing pages
- **Version control**: Commit prompt changes to git with descriptive messages

## Prompt Engineering Tips

1. **Structure matters**: Use clear sections and formatting
2. **Be explicit**: Don't assume the AI knows what you want
3. **Provide context**: Explain why certain outputs are needed
4. **Use constraints**: Specify limits (e.g., "maximum 3 colors")
5. **Request JSON**: Always specify the exact output format
6. **Give examples**: Show what good output looks like
