#!/usr/bin/env python3
"""
DART API 고속 배치 수집 스크립트 (최적화 버전)
- API 호출 간격 최소화 (0.1초)
- 로그 출력 간소화
- 배치 간 휴식 제거
- 처리 속도 대폭 향상
- start_index / end_index 옵션 추가
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
    api_01_irdsSttus, api_02_alotMatter, api_03_tesstkAcqsDspsSttus, api_04_hyslrSttus,
    api_05_hyslrChgSttus, api_06_mrhlSttus, api_07_exctvSttus, api_08_empSttus,
    api_09_hmvAuditIndvdlBySttus, api_10_hmvAuditAllSttus, api_11_indvdlByPay, api_12_otrCprInvstmntSttus,
    api_13_stockTotqySttus, api_14_detScritsIsuAcmslt, api_15_entrprsBilScritsNrdmpBlce, api_16_srtpdPsndbtNrdmpBlce,
    api_17_cprndNrdmpBlce, api_18_newCaplScritsNrdmpBlce, api_19_cndlCaplScritsNrdmpBlce, api_20_accnutAdtorNmNdAdtOpinion,
    api_21_adtServcCnclsSttus, api_22_accnutAdtorNonAdtServcCnclsSttus, api_23_outcmpnyDrctrNdChangeSttus, api_24_unrstExctvMendngSttus,
    api_25_drctrAdtAllMendngSttusGmtsckConfmAmount, api_26_drctrAdtAllMendngSttusMendngPymntamtTyCl, api_27_pssrpCptalUseDtls, api_28_prvsrpCptalUseDtls,
    set_api_key, get_current_api_key, AVAILABLE_API_KEYS
)

class FastDartCollector:
    def __init__(self, year='2024', quarter='Q4'):
        self.year = year
        self.quarter = quarter
        self.base_dir = Path('dart_api_data')
        self.quarter_dir = self.base_dir / year / quarter
        self.companies_dir = self.quarter_dir / 'companies'
        self.progress_file = self.quarter_dir / 'progress.json'

        # 분기별 보고서 코드 매핑
        self.quarter_codes = {
            'Q1': '11013', 'Q2': '11012', 'Q3': '11014', 'Q4': '11011'
        }

        # 28개 API 함수
        self.api_functions = [
            api_01_irdsSttus, api_02_alotMatter, api_03_tesstkAcqsDspsSttus, api_04_hyslrSttus,
            api_05_hyslrChgSttus, api_06_mrhlSttus, api_07_exctvSttus, api_08_empSttus,
            api_09_hmvAuditIndvdlBySttus, api_10_hmvAuditAllSttus, api_11_indvdlByPay, api_12_otrCprInvstmntSttus,
            api_13_stockTotqySttus, api_14_detScritsIsuAcmslt, api_15_entrprsBilScritsNrdmpBlce, api_16_srtpdPsndbtNrdmpBlce,
            api_17_cprndNrdmpBlce, api_18_newCaplScritsNrdmpBlce, api_19_cndlCaplScritsNrdmpBlce, api_20_accnutAdtorNmNdAdtOpinion,
            api_21_adtServcCnclsSttus, api_22_accnutAdtorNonAdtServcCnclsSttus, api_23_outcmpnyDrctrNdChangeSttus, api_24_unrstExctvMendngSttus,
            api_25_drctrAdtAllMendngSttusGmtsckConfmAmount, api_26_drctrAdtAllMendngSttusMendngPymntamtTyCl, api_27_pssrpCptalUseDtls, api_28_prvsrpCptalUseDtls
        ]

        self.setup_directories()

    def setup_directories(self):
        """디렉토리 구조 생성"""
        self.companies_dir.mkdir(parents=True, exist_ok=True)

    def load_listed_companies(self):
        """상장사 리스트 로드"""
        # companies_file = Path('dart_corpcode_data/listed_unsang_companies_latest.json')
        companies_file = Path('dart_corpcode_data/listed_companies_latest.json')
        try:
            with open(companies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['companies']
        except Exception as e:
            print(f"❌ 상장사 리스트 로드 실패: {e}")
            return []
    
    def load_progress(self):
        """진행상황 로드"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        return {
            'started_at': datetime.now().isoformat(),
            'total': 0, 'completed': 0, 'failed': 0,
            'completed_companies': [], 'failed_companies': []
        }

    def save_progress(self, progress):
        """진행상황 저장"""
        progress['updated_at'] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except:
            pass

    def collect_company_data_fast(self, company, progress):
        """개별 회사 데이터 수집 (고속화 버전)"""
        corp_code = company['corp_code']
        corp_name = company['corp_name']
        stock_code = company.get('stock_code', '')

        # 이미 완료된 회사는 건너뛰기
        if corp_code in progress['completed_companies']:
            return True

        # 파일명 생성
        safe_name = corp_name.replace('/', '_').replace('\\', '_')[:20]
        filename = f"{stock_code}_{safe_name}.json"
        file_path = self.companies_dir / filename

        # 이미 파일이 존재하면 건너뛰기
        if file_path.exists():
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
                'year_quarter': f"{self.year}_{self.quarter}",
                'collection_date': datetime.now().isoformat()
            },
            'api_data': {}
        }

        successful_apis = 0

        for i, api_func in enumerate(self.api_functions):
            try:
                result = api_func(params)
                if result and result.get('status') == '000':
                    if 'list' in result and result['list']:
                        company_data['api_data'][f'api_{i+1:02d}'] = result['list']
                        successful_apis += 1
                time.sleep(0.1)
            except Exception:
                continue

        if successful_apis > 0:
            company_data['metadata']['successful_apis'] = successful_apis
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(company_data, f, ensure_ascii=False, indent=2)
                progress['completed_companies'].append(corp_code)
                return True
            except:
                pass

        progress['failed_companies'].append(corp_code)
        return False

    def run_fast_collection(self, batch_size=100, start_index=0, end_index=None, api_key_name=None):
        """고속 배치 수집 실행"""
        # API 키 설정
        if api_key_name:
            set_api_key(api_key_name)
            print(f"🔑 API 키 설정: {api_key_name} ({get_current_api_key()[:10]}...)")

        print(f"🚀 DART API 고속 수집 시작 ({self.year} {self.quarter})")
        print(f"📍 처리 범위: 인덱스 {start_index} ~ {end_index if end_index else '끝'}")

        companies = self.load_listed_companies()
        if not companies:
            print("❌ 상장사 리스트 로드 실패")
            return

        # 처리 범위 지정
        companies_to_process = companies[start_index:end_index]
        progress = self.load_progress()
        progress['total'] = len(companies_to_process)

        print(f"📊 전체: {len(companies):,}개 | 처리대상: {len(companies_to_process):,}개 | 완료: {len(progress['completed_companies'])}개")

        start_time = time.time()

        for batch_start in range(0, len(companies_to_process), batch_size):
            batch_end = min(batch_start + batch_size, len(companies_to_process))
            batch_companies = companies_to_process[batch_start:batch_end]

            batch_num = (start_index + batch_start) // batch_size + 1

            batch_success = 0
            for i, company in enumerate(batch_companies):
                try:
                    if self.collect_company_data_fast(company, progress):
                        progress['completed'] += 1
                        batch_success += 1
                    else:
                        progress['failed'] += 1

                    if (i + 1) % 10 == 0:
                        self.save_progress(progress)

                except KeyboardInterrupt:
                    print("\n⚠️ 사용자 중단")
                    self.save_progress(progress)
                    return
                except:
                    progress['failed'] += 1
                    continue

            self.save_progress(progress)

            elapsed = time.time() - start_time
            completion_rate = progress['completed'] / progress['total'] * 100
            rate_per_min = progress['completed'] / (elapsed / 60) if elapsed > 0 else 0

            print(f"배치{batch_num:3d}: {batch_success:2d}/{len(batch_companies)} | "
                  f"진행률: {completion_rate:5.1f}% ({progress['completed']:4d}/{progress['total']}) | "
                  f"속도: {rate_per_min:.1f}개/분")

        total_time = time.time() - start_time
        print(f"\n🎯 완료! 소요시간: {total_time/3600:.1f}시간")
        print(f"성공: {progress['completed']}개, 실패: {progress['failed']}개")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='DART API 고속 배치 수집')
    parser.add_argument('--year', default='2024', help='수집 연도')
    parser.add_argument('--quarter', default='Q4', choices=['Q1', 'Q2', 'Q3', 'Q4'], help='수집 분기')
    parser.add_argument('--batch-size', type=int, default=100, help='배치 크기')
    parser.add_argument('--start-index', type=int, default=0, help='처리 시작 인덱스')
    parser.add_argument('--end-index', type=int, default=None, help='처리 종료 인덱스 (미지정 시 끝까지)')
    parser.add_argument('--api-key', choices=list(AVAILABLE_API_KEYS.keys()), help='사용할 API 키 선택')

    args = parser.parse_args()

    collector = FastDartCollector(year=args.year, quarter=args.quarter)
    collector.run_fast_collection(
        batch_size=args.batch_size,
        start_index=args.start_index,
        end_index=args.end_index,
        api_key_name=args.api_key
    )

if __name__ == "__main__":
    main()


"""
nohup python dart_batch_collector_fast.py --year 2022 --quarter Q3 --batch-size 700 --start-index 0    --end-index 700  --api-key key1 > log_key1.txt 2>&1 &
nohup python dart_batch_collector_fast.py --year 2022 --quarter Q3 --batch-size 700 --start-index 700  --end-index 1400 --api-key key2 > log_key2.txt 2>&1 &
nohup python dart_batch_collector_fast.py --year 2022 --quarter Q3 --batch-size 700 --start-index 1400 --end-index 2100 --api-key key3 > log_key3.txt 2>&1 &
nohup python dart_batch_collector_fast.py --year 2022 --quarter Q3 --batch-size 700 --start-index 2100 --end-index 2800 --api-key key4 > log_key4.txt 2>&1 &
nohup python dart_batch_collector_fast.py --year 2022 --quarter Q3 --batch-size 700 --start-index 2800 --end-index 3500 --api-key key5 > log_key5.txt 2>&1 &
nohup python dart_batch_collector_fast.py --year 2022 --quarter Q3 --batch-size 700 --start-index 3500 --end-index 4200 --api-key key6 > log_key6.txt 2>&1 &
"""