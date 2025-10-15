#!/usr/bin/env python3
"""
DART 공시 문서 검색기 - 순수 파일 시스템 검색 로직
LLM 호출 없이 파일 검색 및 로드만 담당
"""

import os
import json
from typing import Dict, Optional, List
from difflib import SequenceMatcher
from pub_agent.utils import DartRegularPostprocessor

BASE_DATA_PATH = "/home/sese/Insight-Agent/Clova-PubAgent/dart_api_data"

class DocumentSearcher:
    """순수 문서 검색 및 로드 기능만 제공"""

    def __init__(self):
        self.base_path = BASE_DATA_PATH
        self.postprocessor = DartRegularPostprocessor()

    def find_similar_company_names(self, target_name: str, file_list: List[str]) -> List[str]:
        """파일 리스트에서 유사한 회사명 찾기"""
        candidates = []

        for filename in file_list:
            if filename.endswith('.json'):
                try:
                    if '_' in filename:
                        company_part = filename.split('_', 1)[1].replace('.json', '')
                        similarity = SequenceMatcher(None, target_name, company_part).ratio()
                        if similarity > 0.5:  # 50% 이상 유사도
                            candidates.append((filename, company_part, similarity))
                except:
                    continue

        # 유사도 순으로 정렬
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[:5]  # 상위 5개만 반환

    def find_and_load_disclosure(self, company_name: str, year: int, quarter: int) -> Optional[Dict]:
        """회사명, 연도, 분기로 공시 파일 검색 및 로드"""
        if not all([company_name, year, quarter]):
            print("파일 검색에 필요한 정보가 부족합니다.")
            return None

        target_path = os.path.join(self.base_path, str(year), f"Q{quarter}", "companies")

        if not os.path.exists(target_path):
            print(f"경로를 찾을 수 없습니다: {target_path}")
            return None

        try:
            file_list = os.listdir(target_path)

            exact_match = None
            partial_matches = []

            for filename in file_list:
                if filename.endswith('.json') and '_' in filename:
                    try:
                        file_company_name = filename.split('_', 1)[1].replace('.json', '')
                        # 정확히 일치하는 경우
                        if company_name == file_company_name:
                            exact_match = filename
                            break
                        # 부분 매칭 후보 저장
                        elif company_name in file_company_name or file_company_name in company_name:
                            partial_matches.append((filename, file_company_name))
                    except:
                        continue

            # 정확 매칭 우선
            if exact_match:
                file_path = os.path.join(target_path, exact_match)
                print(f"파일을 찾았습니다: {exact_match}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    processed_data = self.postprocessor.process_regular_data(raw_data)
                    return {"raw_data": raw_data, "processed_data": processed_data}

            # 부분 매칭이 여러 개 있으면 가장 짧은 이름 선택
            if partial_matches:
                partial_matches.sort(key=lambda x: len(x[1]))  # 이름 길이 기준 정렬
                best_match = partial_matches[0][0]
                file_path = os.path.join(target_path, best_match)
                print(f"부분 매칭 파일을 사용합니다: {best_match}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    processed_data = self.postprocessor.process_regular_data(raw_data)
                    return {"raw_data": raw_data, "processed_data": processed_data}

            # 유사도 검색
            similar_companies = self.find_similar_company_names(company_name, file_list)
            if similar_companies:
                print(f"정확한 매칭을 찾지 못했습니다. 유사한 회사들:")
                for filename, company_part, similarity in similar_companies:
                    print(f"  - {company_part} (유사도: {similarity:.2f})")

                best_match = similar_companies[0][0]
                file_path = os.path.join(target_path, best_match)
                print(f"가장 유사한 파일을 사용합니다: {best_match}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    processed_data = self.postprocessor.process_regular_data(raw_data)
                    return {"raw_data": raw_data, "processed_data": processed_data}

            print(f"'{company_name}'와 유사한 회사를 찾지 못했습니다.")
            return None

        except Exception as e:
            print(f"파일 검색 중 오류 발생: {e}")
            return None

    def get_company_quarterly_reports(self, company_name: str) -> Dict:
        """회사명으로 사용 가능한 분기 보고서 목록 조회"""
        print(f"[SEARCHER] {company_name}의 분기 보고서 목록 조회 시작")

        available_reports = []

        # 2024, 2025년의 모든 분기 검색
        for year in [2022,2023,2024, 2025]:
            for quarter in [1, 2, 3, 4]:
                target_path = os.path.join(self.base_path, str(year), f"Q{quarter}", "companies")

                if not os.path.exists(target_path):
                    continue

                try:
                    file_list = os.listdir(target_path)

                    for filename in file_list:
                        if filename.endswith('.json') and '_' in filename:
                            try:
                                file_company_name = filename.split('_', 1)[1].replace('.json', '')

                                # 정확 매칭 또는 부분 매칭
                                if (company_name == file_company_name or
                                    company_name in file_company_name or
                                    file_company_name in company_name):

                                    # 파일이 실제로 존재하는지 확인
                                    file_path = os.path.join(target_path, filename)
                                    if os.path.exists(file_path):
                                        available_reports.append({
                                            "year": year,
                                            "quarter": quarter,
                                            "company_name": file_company_name,
                                            "filename": filename,
                                            "file_path": file_path
                                        })
                                        break  # 같은 분기에서 첫 번째 매칭만 취함
                            except:
                                continue

                except Exception as e:
                    print(f"경로 {target_path} 검색 중 오류: {e}")
                    continue

        if not available_reports:
            return {"error": f"'{company_name}'에 해당하는 분기 보고서를 찾을 수 없습니다."}

        # 연도, 분기 순으로 정렬 (최신순)
        available_reports.sort(key=lambda x: (x["year"], x["quarter"]), reverse=True)

        return {
            "company_name": company_name,
            "available_reports": available_reports,
            "total_count": len(available_reports),
            "success": True
        }

    def get_company_data(self, company_name: str, year: int, quarter: int) -> Dict:
        """회사명, 연도, 분기로 직접 원본 데이터 조회"""
        print(f"[SEARCHER] {company_name} {year}년 {quarter}분기 데이터 조회 시작")

        target_path = os.path.join(self.base_path, str(year), f"Q{quarter}", "companies")

        if not os.path.exists(target_path):
            return {"error": f"{year}년 {quarter}분기 데이터 경로를 찾을 수 없습니다."}

        try:
            file_list = os.listdir(target_path)

            exact_match = None
            partial_matches = []

            for filename in file_list:
                if filename.endswith('.json') and '_' in filename:
                    try:
                        file_company_name = filename.split('_', 1)[1].replace('.json', '')

                        # 정확히 일치하는 경우
                        if company_name == file_company_name:
                            exact_match = filename
                            break
                        # 부분 매칭 후보 저장
                        elif company_name in file_company_name or file_company_name in company_name:
                            partial_matches.append((filename, file_company_name))
                    except:
                        continue

            # 정확 매칭 우선
            if exact_match:
                file_path = os.path.join(target_path, exact_match)
                print(f"파일을 찾았습니다: {exact_match}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    processed_data = self.postprocessor.process_regular_data(data)
                    return {
                        "company_name": data.get("metadata", {}).get("corp_name"),
                        "year": year,
                        "quarter": quarter,
                        "raw_data": data,
                        "processed_data": processed_data,
                        "success": True
                    }

            # 부분 매칭이 있으면 사용
            if partial_matches:
                partial_matches.sort(key=lambda x: len(x[1]))  # 이름 길이 기준 정렬
                best_match = partial_matches[0][0]
                file_path = os.path.join(target_path, best_match)
                print(f"부분 매칭 파일을 사용합니다: {best_match}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    processed_data = self.postprocessor.process_regular_data(data)
                    return {
                        "company_name": data.get("metadata", {}).get("corp_name"),
                        "year": year,
                        "quarter": quarter,
                        "raw_data": data,
                        "processed_data": processed_data,
                        "success": True
                    }

            return {"error": f"'{company_name}'의 {year}년 {quarter}분기 데이터를 찾을 수 없습니다."}

        except Exception as e:
            return {"error": f"파일 검색 중 오류 발생: {str(e)}"}