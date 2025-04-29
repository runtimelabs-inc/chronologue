import markdown
import json
from typing import List, Dict

def markdown_table_to_json(md_text: str) -> List[Dict]:
    """
    Parse a markdown grocery table into JSON format.
    Assumes format:
    | Quantity | Item | Link |
    |:---|:---|:---|
    | 2 | Organic Blueberries | https://example.com/blueberries |
    """
    lines = md_text.strip().split('\n')
    headers = [h.strip() for h in lines[1].strip('|').split('|')]
    rows = []
    for line in lines[3:]:
        if line.strip():
            fields = [field.strip() for field in line.strip('|').split('|')]
            row = dict(zip(headers, fields))
            rows.append(row)
    return rows

def json_to_markdown_table(items: List[Dict]) -> str:
    """
    Convert JSON grocery items to markdown table.
    """
    headers = "| Quantity | Item | Link |\n|:---|:---|:---|"
    rows = [f"| {item['quantity']} | {item['item']} | {item.get('link', '')} |" for item in items]
    return "\n".join([headers] + rows)
