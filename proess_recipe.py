import re

async def process_recipe(recipe_content):
    title = re.search(r'A recipe for:(.*)', recipe_content)
    title = title.group(1).strip() if title else None

    ingredients_sections = re.findall(r'Ingredients:\n(.*?)(?:\n\n|\Z)', recipe_content, re.DOTALL)
    ingredients = {}
    for section in ingredients_sections:
        section_title = re.search(r'For the (.*?):', section)
        section_title = section_title.group(1).strip() if section_title else 'Main'
        section_ingredients = [line.strip() for line in section.split('\n') if line.strip() and 'For the' not in line]
        ingredients[section_title] = section_ingredients

    instructions = re.findall(r'(?:Directions:|Instructions:)([\s\S]*)', recipe_content)
    instructions = [line.strip() for line in instructions[0].split('\n') if line.strip()] if instructions else []

    return {
        'title': title,
        'ingredients': ingredients,
        'instructions': instructions
    }