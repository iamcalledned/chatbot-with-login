import re

def classify_content(message_content):
    # Check for Ingredients and Instructions headers
    has_headers = "**Ingredients:**" in message_content and "**Instructions:**" in message_content
    
    # Regular expression for ingredient list items
    ingredient_pattern = re.compile(r'-\s+\d+\/?\d*\s+\w+')
    has_ingredient_list = bool(ingredient_pattern.search(message_content))
    
    # Regular expression for step-by-step instructions
    instruction_pattern = re.compile(r'\b\d+\.\s+(Combine|Stir|Mix|Add|Pour|Simmer|Chop|Bake)')
    has_instructions = bool(instruction_pattern.search(message_content))
    
    if has_headers and has_ingredient_list and has_instructions
        return "recipe"
