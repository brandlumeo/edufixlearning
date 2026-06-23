import re

with open("c:/Users/M S I/Desktop/edufixlearn/templates/courses/lesson_view.html", "r", encoding="utf-8") as f:
    content = f.read()

# Remove Django template tags that might confuse simple parsing
# (though they don't contain raw HTML divs usually, let's keep it simple)
clean_content = re.sub(r'{%.*?%}', '', content)
clean_content = re.sub(r'{{.*?}}', '', clean_content)

# Find all div tags
divs = re.findall(r'<div\b|</div>', clean_content)

opened = 0
for idx, div in enumerate(divs):
    if div == '<div':
        opened += 1
    else:
        opened -= 1
    print(f"{idx}: {div} -> opened: {opened}")

print(f"Final opened count: {opened}")
