#!/usr/bin/env python3
"""
DART API 배치 수집 스크립트
- 상장사 3,897개 회사의 모든 API 데이터 수집
- 분기별 디렉토리 구조로 저장
- 진행상황 추적 및 재시작 기능
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import sys

# 기존 dart_api_requests 모듈 임포트
sys.path.append('.')
from dart_api_requests import (
    API_KEY, save_all_company_data, make_api_request,
    api_01_irdsSttus, api_02_alotMatter, api_03_tesstkAcqsDspsSttus, api_04_hyslrSttus,
    api_05_hyslrChgSttus, api_06_mrhlSttus, api_07_exctvSttus, api_08_empSttus,
    api_09_hmvAuditIndvdlBySttus, api_10_hmvAuditAllSttus, api_11_indvdlByPay, api_12_otrCprInvstmntSttus,
    api_13_stockTotqySttus, api_14_detScritsIsuAcmslt, api_15_entrprsBilScritsNrdmpBlce, api_16_srtpdPsndbtNrdmpBlce,
    api_17_cprndNrdmpBlce, api_18_newCaplScritsNrdmpBlce, api_19_cndlCaplScritsNrdmpBlce, api_20_accnutAdtorNmNdAdtOpinion,
    api_21_adtServcCnclsSttus, api_22_accnutAdtorNonAdtServcCnclsSttus, api_23_outcmpnyDrctrNdChangeSttus, api_24_unrstExctvMendngSttus,
    api_25_drctrAdtAllMendngSttusGmtsckConfmAmount, api_26_drctrAdtAllMendngSttusMendngPymntamtTyCl, api_27_pssrpCptalUseDtls, api_28_prvsrpCptalUseDtls
)

class DartBatchCollector:
    def __init__(self, year='2023', quarter='Q4'):
        self.year = year
        self.quarter = quarter
        self.base_dir = Path('dart_api_data')
        self.quarter_dir = self.base_dir / year / quarter
        self.companies_dir = self.quarter_dir / 'companies'
        self.logs_dir = self.base_dir / 'logs'
        self.progress_file = self.quarter_dir / 'progress.json'

        # 분기별 보고서 코드 매핑
        self.quarter_codes = {
            'Q1': '11013',  # 1분기보고서
            'Q2': '11012',  # 반기보고서
            'Q3': '11014',  # 3분기보고서
            'Q4': '11011'   # 사업보고서
        }

        # 28개 API 함수 리스트
        self.api_functions = [
            (api_01_irdsSttus, "증자감자현황"),
            (api_02_alotMatter, "배당에관한사항"),
            (api_03_tesstkAcqsDspsSttus, "자기주식취득및처분현황"),
            (api_04_hyslrSttus, "최대주주현황"),
            (api_05_hyslrChgSttus, "최대주주변동현황"),
            (api_06_mrhlSttus, "소액주주현황"),
            (api_07_exctvSttus, "임원현황"),
            (api_08_empSttus, "직원현황"),
            (api_09_hmvAuditIndvdlBySttus, "이사감사개인별보수현황"),
            (api_10_hmvAuditAllSttus, "이사감사전체보수현황"),
            (api_11_indvdlByPay, "개인별보수지급금액"),
            (api_12_otrCprInvstmntSttus, "타법인출자현황"),
            (api_13_stockTotqySttus, "주식의총수현황"),
            (api_14_detScritsIsuAcmslt, "채무증권발행실적"),
            (api_15_entrprsBilScritsNrdmpBlce, "기업어음증권미상환잔액"),
            (api_16_srtpdPsndbtNrdmpBlce, "단기사채미상환잔액"),
            (api_17_cprndNrdmpBlce, "회사채미상환잔액"),
            (api_18_newCaplScritsNrdmpBlce, "신종자본증권미상환잔액"),
            (api_19_cndlCaplScritsNrdmpBlce, "조건부자본증권미상환잔액"),
            (api_20_accnutAdtorNmNdAdtOpinion, "회계감사인명칭및감사의견"),
            (api_21_adtServcCnclsSttus, "감사용역체결현황"),
            (api_22_accnutAdtorNonAdtServcCnclsSttus, "회계감사인비감사용역체결현황"),
            (api_23_outcmpnyDrctrNdChangeSttus, "사외이사및변동현황"),
            (api_24_unrstExctvMendngSttus, "미등기임원보수현황"),
            (api_25_drctrAdtAllMendngSttusGmtsckConfmAmount, "이사감사전체보수현황주총승인금액"),
            (api_26_drctrAdtAllMendngSttusMendngPymntamtTyCl, "이사감사전체보수현황보수지급금액유형별"),
            (api_27_pssrpCptalUseDtls, "공모자금사용내역"),
            (api_28_prvsrpCptalUseDtls, "사모자금사용내역")
        ]

        self.setup_directories()

    def setup_directories(self):
        """디렉토리 구조 생성"""
        self.companies_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 디렉토리 생성: {self.quarter_dir}")

    def load_listed_companies(self):
        """상장사 리스트 로드"""
        companies_file = Path('dart_corpcode_data/listed_companies_latest.json')

        try:
            with open(companies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            companies = data['companies']
            print(f"✅ 상장사 리스트 로드: {len(companies):,}개")
            return companies
        except Exception as e:
            print(f"❌ 상장사 리스트 로드 실패: {e}")
            return []

    def load_progress(self):
        """진행상황 로드"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                print(f"📊 진행상황 로드: {progress.get('completed', 0)}/{progress.get('total', 0)} 완료")
                return progress
            except Exception as e:
                print(f"⚠️  진행상황 로드 실패: {e}")

        return {
            'started_at': datetime.now().isoformat(),
            'total': 0,
            'completed': 0,
            'failed': 0,
            'completed_companies': [],
            'failed_companies': [],
            'current_batch': 0
        }

    def save_progress(self, progress):
        """진행상황 저장"""
        progress['updated_at'] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  진행상황 저장 실패: {e}")

    def collect_company_data(self, company, progress):
        """개별 회사 데이터 수집"""
        corp_code = company['corp_code']
        corp_name = company['corp_name']
        stock_code = company.get('stock_code', '')

        # 이미 완료된 회사는 건너뛰기
        if corp_code in progress['completed_companies']:
            return True

        print(f"📊 수집 중: {corp_name} ({stock_code}) - {corp_code}")

        # 파일명 생성
        safe_name = corp_name.replace('/', '_').replace('\\', '_')
        filename = f"{stock_code}_{safe_name}.json"
        file_path = self.companies_dir / filename

        # 이미 파일이 존재하면 건너뛰기
        if file_path.exists():
            print(f"   ✅ 이미 존재함: {filename}")
            progress['completed_companies'].append(corp_code)
            return True

        # API 파라미터 설정
        params = {
            'corp_code': corp_code,
            'bsns_year': self.year,
            'reprt_code': self.quarter_codes[self.quarter]
        }

        # 회사 데이터 구조
        company_data = {
            'metadata': {
                'corp_code': corp_code,
                'corp_name': corp_name,
                'stock_code': stock_code,
                'bsns_year': self.year,
                'quarter': self.quarter,
                'reprt_code': self.quarter_codes[self.quarter],
                'collection_date': datetime.now().isoformat(),
                'total_apis': len(self.api_functions)
            },
            'api_data': {}
        }

        successful_apis = 0

        # 각 API 호출
        for i, (api_func, api_name) in enumerate(self.api_functions, 1):
            try:
                print(f"   [{i:2d}/{len(self.api_functions)}] {api_name}")
                result = api_func(params)

                if result and result.get('status') == '000':
                    company_data['api_data'][api_name] = result
                    successful_apis += 1
                    print(f"      ✅ 성공")
                else:
                    company_data['api_data'][api_name] = None
                    status = result.get('status', 'N/A') if result else 'N/A'
                    message = result.get('message', 'N/A') if result else 'N/A'
                    print(f"      ❌ 실패: {status} - {message}")

                # API 호출 간격 (서버 부하 방지)
                time.sleep(0.5)

            except Exception as e:
                print(f"      ❌ 오류: {e}")
                company_data['api_data'][api_name] = None

        # 메타데이터 업데이트
        company_data['metadata']['successful_apis'] = successful_apis
        company_data['metadata']['success_rate'] = successful_apis / len(self.api_functions) * 100

        # 파일 저장
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, ensure_ascii=False, indent=2)

            print(f"   💾 저장 완료: {filename} ({successful_apis}/{len(self.api_functions)} API 성공)")
            progress['completed_companies'].append(corp_code)
            return True

        except Exception as e:
            print(f"   ❌ 저장 실패: {e}")
            progress['failed_companies'].append({
                'corp_code': corp_code,
                'corp_name': corp_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False

    def run_batch_collection(self, batch_size=50, start_from=0):
        """배치 수집 실행"""
        print(f"🚀 DART API 배치 수집 시작")
        print(f"📅 대상: {self.year}년 {self.quarter} ({self.quarter_codes[self.quarter]})")
        print(f"📁 저장 위치: {self.quarter_dir}")
        print("=" * 80)

        # 상장사 리스트 로드
        companies = self.load_listed_companies()
        if not companies:
            print("❌ 상장사 리스트를 로드할 수 없습니다.")
            return

        # 진행상황 로드
        progress = self.load_progress()
        progress['total'] = len(companies)

        # 시작 지점 설정
        companies_to_process = companies[start_from:]

        print(f"📊 수집 계획:")
        print(f"   전체 회사: {len(companies):,}개")
        print(f"   시작 지점: {start_from}")
        print(f"   처리 대상: {len(companies_to_process):,}개")
        print(f"   배치 크기: {batch_size}개")
        print(f"   이미 완료: {len(progress['completed_companies'])}개")
        print()

        # 배치별 처리
        for batch_start in range(0, len(companies_to_process), batch_size):
            batch_end = min(batch_start + batch_size, len(companies_to_process))
            batch_companies = companies_to_process[batch_start:batch_end]

            batch_num = (start_from + batch_start) // batch_size + 1
            print(f"📦 배치 {batch_num} 처리 중 ({batch_start + 1}~{batch_end})")
            print("-" * 60)

            progress['current_batch'] = batch_num

            # 배치 내 회사들 처리
            for i, company in enumerate(batch_companies):
                try:
                    success = self.collect_company_data(company, progress)

                    if success:
                        progress['completed'] += 1
                    else:
                        progress['failed'] += 1

                    # 진행상황 업데이트 (10개마다)
                    if (i + 1) % 10 == 0:
                        self.save_progress(progress)
                        completion_rate = progress['completed'] / progress['total'] * 100
                        print(f"   📈 진행률: {completion_rate:.1f}% ({progress['completed']}/{progress['total']})")

                except KeyboardInterrupt:
                    print("\n⚠️  사용자가 중단했습니다.")
                    self.save_progress(progress)
                    return
                except Exception as e:
                    print(f"   ❌ 예상치 못한 오류: {e}")
                    continue

            # 배치 완료 후 진행상황 저장
            self.save_progress(progress)

            print(f"✅ 배치 {batch_num} 완료")
            print(f"   성공: {progress['completed']}개, 실패: {progress['failed']}개")
            print()

            # 배치 간 휴식 (API 제한 고려)
            if batch_end < len(companies_to_process):
                print("⏳ 배치 간 휴식 (30초)...")
                time.sleep(30)

        # 최종 결과
        print("🎯 배치 수집 완료!")
        print(f"📊 최종 결과:")
        print(f"   성공: {progress['completed']}개")
        print(f"   실패: {progress['failed']}개")
        print(f"   성공률: {progress['completed']/progress['total']*100:.1f}%")
        print(f"💾 데이터 저장 위치: {self.companies_dir}")

def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='DART API 배치 데이터 수집')
    parser.add_argument('--year', default='2023', help='수집 연도 (기본값: 2023)')
    parser.add_argument('--quarter', default='Q4', choices=['Q1', 'Q2', 'Q3', 'Q4'],
                       help='수집 분기 (기본값: Q4)')
    parser.add_argument('--batch-size', type=int, default=50, help='배치 크기 (기본값: 50)')
    parser.add_argument('--start-from', type=int, default=0, help='시작 회사 인덱스 (기본값: 0)')

    args = parser.parse_args()

    collector = DartBatchCollector(year=args.year, quarter=args.quarter)
    collector.run_batch_collection(
        batch_size=args.batch_size,
        start_from=args.start_from
    )

if __name__ == "__main__":
    main()
# nohup python dart_batch_collector_fast.py --year 2023 --quarter Q4 --batch-size 100 --start-index 3099 --end-index 3799 --api-key 3 > dart_key4_3099-3799.log 2>&1    