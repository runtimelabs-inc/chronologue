import re
from typing import List, Dict
from pathlib import Path

def parse_markdown_grocery_list(md_text: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Parses a markdown grocery scheduling file into structured dictionary.
    
    Expected markdown format:
    - Section headers: "# Weekly Order", "# Monthly Order"
    - Item lines: "- Quantity Item Name [Link]"
    """
    orders = {
        "weekly": [],
        "monthly": []
    }

    current_section = None

    for line in md_text.splitlines():
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Detect Section Headers
        if line.lower().startswith("# weekly order"):
            current_section = "weekly"
            continue
        elif line.lower().startswith("# monthly order"):
            current_section = "monthly"
            continue
        
        # Parse Item Lines
        if line.startswith("- ") and current_section:
            # Match "- quantity item_name [link]"
            match = re.match(r"-\s+(.*)\s+\[(http.*?)\]", line)
            if match:
                item_text = match.group(1)
                link = match.group(2)

                # Optionally split quantity and item
                quantity, item = parse_quantity_and_item(item_text)

                orders[current_section].append({
                    "item": item,
                    "quantity": quantity,
                    "link": link
                })
            else:
                print(f"Warning: Line could not be parsed: {line}")

    return orders

def parse_quantity_and_item(text: str) -> (str, str):
    """
    Heuristic to split quantity and item.
    Example:
        "12 Eggs" -> ("12", "Eggs")
        "2 lbs Chicken Breast" -> ("2 lbs", "Chicken Breast")
    """
    tokens = text.split()
    if len(tokens) >= 2:
        quantity = tokens[0]
        item = " ".join(tokens[1:])
        return quantity, item
    else:
        return "", text  # Fallback: no quantity detected

def load_markdown_file(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {filepath}")
    return path.read_text(encoding="utf-8")

def save_orders_to_json(orders: Dict[str, List[Dict[str, str]]], output_path: str):
    import json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2)

if __name__ == "__main__":
    # Example usage
    input_md = "grocery_schedule.md"
    output_json = "grocery_orders.json"

    md_text = load_markdown_file(input_md)
    orders = parse_markdown_grocery_list(md_text)
    save_orders_to_json(orders, output_json)

    print(f"Parsed and saved orders to {output_json}")
