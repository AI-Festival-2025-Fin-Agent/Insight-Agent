#!/usr/bin/env python3
"""
DART regular disclosure data postprocessor - JSON format
Convert API data to markdown text within JSON structure
"""

import json
from typing import Dict, Any, List


class DartRegularPostprocessor:
    """DART regular disclosure data postprocessor - JSON output"""

    def __init__(self):
        # Common fields to exclude
        self.exclude_fields = {'rcept_no', 'corp_cls', 'corp_code', 'corp_name', 'stlm_dt'}

    def process_regular_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process regular data and return JSON with markdown content"""
        if 'api_data' not in data:
            return {"error": "api_data not found"}

        # Keep original structure but replace content with markdown
        result = {
            "metadata": data.get('metadata', {}),
            "api_data": {}
        }

        api_data = data['api_data']

        # Process each API
        for api_key in sorted(api_data.keys()):
            api_items = api_data[api_key]
            result["api_data"][api_key] = self._process_api_to_markdown(api_items, api_key)

        return result

    def _process_api_to_markdown(self, items: List[Dict], api_key: str) -> str:
        """Convert API data to markdown text"""
        if not items:
            return f"## {api_key}\nNo data available"

        lines = [f"## {api_key}"]

        if len(items) == 1:
            # Single item - key-value table
            item = items[0]
            filtered_data = {k: v for k, v in item.items() if k not in self.exclude_fields}

            if filtered_data:
                lines.append("| Field | Value |")
                lines.append("| --- | --- |")
                for key, value in filtered_data.items():
                    lines.append(f"| {key} | {value} |")
            else:
                lines.append("No relevant data")

        else:
            # Multiple items - regular table
            if items:
                headers = [k for k in items[0].keys() if k not in self.exclude_fields]

                if headers:
                    lines.append("| " + " | ".join(headers) + " |")
                    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

                    for item in items:
                        values = [str(item.get(h, '-')) for h in headers]
                        lines.append("| " + " | ".join(values) + " |")
                else:
                    lines.append("No relevant data")

        return "\n".join(lines)

    def process_file(self, input_path: str) -> Dict[str, Any]:
        """Read file and process - returns JSON structure"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self.process_regular_data(data)

    def save_processed_data(self, processed_data: Dict[str, Any], output_path: str):
        """Save processed data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)


# Test
if __name__ == "__main__":
    processor = DartRegularPostprocessor()

    input_file = "/home/sese/Clova-PubAgent/dart_api_data/2025/Q1/companies/000010_신한은행.json"

    result = processor.process_file(input_file)

    print("Processed structure:")
    print(f"- metadata keys: {list(result['metadata'].keys())}")
    print(f"- api_data keys: {list(result['api_data'].keys())}")
    print(f"- api_01 content preview: {result['api_data']['api_01'][:100]}...")

    # Save example
    output_file = "/tmp/test_processed.json"
    processor.save_processed_data(result, output_file)
    print(f"Saved to: {output_file}")