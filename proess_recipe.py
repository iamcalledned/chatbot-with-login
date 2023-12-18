import re
from name_recipe import name_recipe

async def process_recipe(recipe_text):
    # Function to find and concatenate multiple sections
    def find_and_concat_sections(text, marker):
        pattern = re.compile(rf'\b{marker}\b', re.IGNORECASE)
        sections = pattern.split(text)
        return '\n'.join(section.strip() for section in sections[1:]) if len(sections) > 1 else ""

    # Get the title
    title = name_recipe(recipe_text)
    print("Title:", title)

    # Find and concatenate all Ingredients and Instructions sections
    ingredients_text = find_and_concat_sections(recipe_text, "Ingredients")
    instructions_text = find_and_concat_sections(recipe_text, "Instructions")

    # Normalize line breaks for consistency
    ingredients = ingredients_text.replace('\r', '\n')
    instructions = instructions_text.replace('\r', '\n')

    return {
        'title': title,
        'ingredients': ingredients,
        'instructions': instructions
    }
