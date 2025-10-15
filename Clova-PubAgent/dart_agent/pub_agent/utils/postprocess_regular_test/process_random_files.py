#!/usr/bin/env python3
"""
무작위 20개 파일 후처리 테스트
"""

import json
import glob
import random
import os
from pathlib import Path
from pub_agent.utils.postprocess_regular import DartRegularPostprocessor

def process_random_files():
    """무작위 20개 파일 후처리"""

    # 모든 JSON 파일 찾기
    all_files = glob.glob("/home/sese/Clova-PubAgent/dart_api_data/2025/Q1/companies/*.json")

    # 무작위로 20개 선택
    random.seed(42)  # 재현 가능하도록
    selected_files = random.sample(all_files, min(20, len(all_files)))

    processor = DartRegularPostprocessor()
    output_dir = "/home/sese/Clova-PubAgent/dart_agent/processed_samples"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Processing {len(selected_files)} random files...\n")

    success_count = 0

    for i, file_path in enumerate(selected_files, 1):
        file_name = Path(file_path).stem
        output_path = f"{output_dir}/{file_name}_processed.md"

        try:
            result = processor.process_file(file_path, output_path)
            success_count += 1

            # 처리 결과 요약
            api_count = len([k for k in result.keys() if k.startswith('api_')])
            file_size = os.path.getsize(output_path)

            print(f"{i:2d}. {file_name}")
            print(f"    APIs: {api_count}, Output: {file_size:,} bytes")

        except Exception as e:
            print(f"{i:2d}. {file_name} - ERROR: {e}")

    print(f"\nCompleted: {success_count}/{len(selected_files)} files processed")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    process_random_files()