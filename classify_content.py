import re

async def classify_content(message_content):

 # Check for recipe-like headers and list formats
    ingredients_header = re.search(r'\*\*Ingredients:\*\*', message_content)
    instructions_header = re.search(r'\*\*Instructions:\*\*', message_content)
    ingredients_list = re.findall(r'-\s+\d+\s+\w+', message_content)
    instructions_list = re.findall(r'\d+\.\s+[A-Z]', message_content)

    # Determine if it is a recipe by the presence of headers and lists
    if ingredients_header and instructions_header and ingredients_list and instructions_list:
        return "recipe"
    else:
        return "other"