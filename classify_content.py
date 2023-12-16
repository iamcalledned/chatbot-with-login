import re

ingredient_pattern = re.compile(r'- \d+/\d*\s+\w+')
instruction_pattern = re.compile(r'\b\d+\.\s+(Combine|Stir|Mix|Add|Pour|Simmer|Chop|Bake)')

async def classify_content(message_content):

  if "**Ingredients:**" not in message_content or "**Instructions:**" not in message_content:
    return

  if not ingredient_pattern.search(message_content):
    return  

  if not instruction_pattern.search(message_content):
    return

  return "recipe"