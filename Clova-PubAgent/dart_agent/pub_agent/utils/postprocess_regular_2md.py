#!/usr/bin/env python3
"""
DART regular disclosure data postprocessor
Convert 28 API sections to markdown table format
"""

import json
from typing import Dict, Any, List


class DartRegularPostprocessor:
    """DART regular disclosure data postprocessor"""

    def __init__(self):
        # Common fields to exclude
        self.exclude_fields = {'rcept_no', 'corp_cls', 'corp_code', 'corp_name', 'stlm_dt'}

    def process_regular_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Process regular data by API sections"""
        if 'api_data' not in data:
            return {"error": "api_data not found"}

        api_data = data['api_data']
        processed = {}

        # Process metadata
        if 'metadata' in data:
            processed['metadata'] = self._format_metadata(data['metadata'])

        # Process each API
        for api_key in sorted(api_data.keys()):
            api_items = api_data[api_key]
            processed[api_key] = self._process_api(api_items, api_key)

        return processed

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata to markdown"""
        lines = [f"# {metadata.get('corp_name', 'Unknown')} - {metadata.get('year_quarter', 'Unknown')}"]
        lines.append(f"- **stock_code**: {metadata.get('stock_code', '-')}")
        lines.append(f"- **corp_code**: {metadata.get('corp_code', '-')}")
        lines.append(f"- **collection_date**: {metadata.get('collection_date', '-')}")
        lines.append(f"- **successful_apis**: {metadata.get('successful_apis', 0)}")
        return "\n".join(lines)

    def _process_api(self, items: List[Dict], api_key: str) -> str:
        """Convert API data to markdown table"""
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
            # Extract headers
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

    def save_processed_data(self, processed_data: Dict[str, str], output_path: str):
        """Save processed data to markdown file"""
        lines = []

        # Metadata first
        if 'metadata' in processed_data:
            lines.append(processed_data['metadata'])
            lines.append("")

        # API data sections
        for key in sorted(processed_data.keys()):
            if key != 'metadata':
                lines.append(processed_data[key])
                lines.append("")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def process_file(self, input_path: str, output_path: str) -> Dict[str, str]:
        """Read file, process and save"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        processed = self.process_regular_data(data)
        self.save_processed_data(processed, output_path)
        return processed


# Test
if __name__ == "__main__":
    processor = DartRegularPostprocessor()

    input_file = "/home/sese/Clova-PubAgent/dart_api_data/2025/Q1/companies/000010_신한은행.json"
    output_file = "/home/sese/Clova-PubAgent/dart_agent/pub_agent/utils/postprocess_regular_test/test_processed.md"

    result = processor.process_file(input_file, output_file)
    print(f"Processed {len(result)} sections")
    print(f"Output saved to: {output_file}")