import re
from html import unescape

# Test the extraction patterns with the real cleaned text
sample_text = """Top job picks for you Roblox/LUA - Senior Game Programmer MildMania · Ankara, Turkey Actively recruiting Easy Apply Gerçek Zamanlı Yazılım Mühendisi Aselsan · Ankara, Türkiye Actively recruiting Easy Apply Back End Developer Rootie Micro-Learning and... · Ankara, Turkey Actively recruiting Easy Apply PHP Developer JotForm · Ankara, Turkey Actively recruiting Easy Apply Software Architect, DevFactory (Remote) - $200,000/year USD Crossover"""

job_id = "2318780725"

print("Testing extraction patterns...")
print(f"Sample text: {sample_text[:200]}...")
print(f"Looking for job ID: {job_id}")
print()

# Test company · location pattern
company_patterns = [
    r'([A-Z][a-zA-Z\s&,.-]{2,40})\s*·\s*[A-Za-z\s,]+',
    r'([A-Z][a-zA-Z\s&,.-]+?)\s*·\s*[A-Za-z\s,]+',
    r'(\w+)\s*·\s*[A-Za-z\s,]+',
]

print("=== TESTING COMPANY PATTERNS ===")
for i, pattern in enumerate(company_patterns):
    matches = re.findall(pattern, sample_text)
    print(f"Pattern {i+1}: {pattern}")
    print(f"Matches: {matches}")
    print()

# Test position patterns
print("=== TESTING POSITION PATTERNS ===")
position_patterns = [
    r'([\w\s/\-]+?)\s+([A-Z][a-zA-Z\s&,.-]+?)\s*·',
    r'(\w+[\w\s/\-]*?)\s+\w+\s*·',
    r'([\w\s/\-]+?(?:Developer|Engineer|Manager|Analyst|Director|Specialist|Consultant|Designer|Programmer))',
]

for i, pattern in enumerate(position_patterns):
    matches = re.findall(pattern, sample_text)
    print(f"Pattern {i+1}: {pattern}")
    print(f"Matches: {matches}")
    print()

# Manual extraction test
print("=== MANUAL EXTRACTION TEST ===")
# Split by common delimiters and look for the pattern
parts = re.split(r'(Easy Apply|Actively recruiting)', sample_text)
print(f"Split parts: {len(parts)}")

for i, part in enumerate(parts[:5]):
    print(f"Part {i}: {part.strip()}")
    
    # Look for company · location
    company_match = re.search(r'([A-Z]\w+(?:\s+\w+)*)\s*·\s*[A-Za-z\s,]+', part)
    if company_match:
        print(f"  Found company: {company_match.group(1)}")
    
    # Look for job title (everything before company)
    title_match = re.search(r'([\w\s/\-]+?)\s+([A-Z]\w+(?:\s+\w+)*)\s*·', part)
    if title_match:
        print(f"  Found title: {title_match.group(1)}")
        print(f"  Found company: {title_match.group(2)}")
    
    print()