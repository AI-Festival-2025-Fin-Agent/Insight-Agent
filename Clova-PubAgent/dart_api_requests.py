#!/usr/bin/env python3
"""
DART Open API 요청 스크립트
28개 정기보고서 주요정보 API 엔드포인트 모음

HTML 문서 분석 결과:
- 모든 API는 동일한 4개 필수 파라미터를 사용
- JSON/XML 형태로 응답 제공
- 삼성전자(00126380) 2018년 사업보고서(11011) 예시 포함

사용법:
1. API 키 발급: https://opendart.fss.or.kr/
2. API_KEY 변수에 실제 키 입력
3. 원하는 함수 호출하여 데이터 조회
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, Optional

# API 키 설정 (실제 키로 교체 필요)

AVAILABLE_API_KEYS = {
    'key1': 'efd...', 
    'key2': 'e30...', 
    'key3': '653...', 
    'key4': 'af3...', 
    'key5': '618...', 
    'key6': '287...'  
}

# 기본 API 키 (환경변수나 인자로 변경 가능)
API_KEY = AVAILABLE_API_KEYS.get('key3', '653...')
# 기본 파라미터 (문서에서 확인한 예시값)
DEFAULT_PARAMS = {
    'corp_code': '00126380',  # 삼성전자
    'bsns_year': '2018',      # 사업연도
    'reprt_code': '11011'     # 사업보고서
}

def set_api_key(key_name: str = None, custom_key: str = None):
    """API 키 설정"""
    global API_KEY
    if custom_key:
        API_KEY = custom_key
    elif key_name and key_name in AVAILABLE_API_KEYS:
        API_KEY = AVAILABLE_API_KEYS[key_name]
    else:
        print(f"사용 가능한 키: {list(AVAILABLE_API_KEYS.keys())}")

def get_current_api_key():
    """현재 API 키 반환"""
    return API_KEY

def make_api_request(api_name: str, params: Dict = None, format_type: str = 'json') -> Optional[Dict]:
    """
    DART API 요청 공통 함수
    
    Args:
        api_name: API 엔드포인트 이름
        params: 추가 파라미터 (기본값 사용시 None)
        format_type: 'json' 또는 'xml'
    """
    base_url = f"https://opendart.fss.or.kr/api/{api_name}.{format_type}"
    
    # 파라미터 설정
    request_params = {
        'crtfc_key': API_KEY,
        **DEFAULT_PARAMS,
        **(params or {})
    }
    
    try:
        print(f"📡 요청: {api_name}")
        print(f"   URL: {base_url}")
        print(f"   Params: {request_params}")
        
        response = requests.get(base_url, params=request_params, timeout=30)
        
        if response.status_code == 200:
            if format_type == 'json':
                data = response.json()
                status = data.get('status', 'N/A')
                message = data.get('message', 'N/A')
                
                print(f"✅ 성공 - Status: {status}, Message: {message}")
                
                if 'list' in data and data['list']:
                    print(f"   데이터 개수: {len(data['list'])}")
                    if data['list']:
                        print(f"   첫 레코드 필드: {list(data['list'][0].keys())}")
                else:
                    print("   ⚠️  리스트 데이터 없음")
                
                return data
            else:
                print(f"✅ XML 응답 수신 (길이: {len(response.text)})")
                return {'xml_content': response.text}
        else:
            print(f"❌ HTTP 오류 {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

# =============================================================================
# 28개 DART API 함수들 (HTML 문서 분석 결과)
# =============================================================================

def api_01_irdsSttus(params=None):
    """주식발행 감소현황 (page_2019004.html)"""
    return make_api_request('irdsSttus', params)

def api_02_alotMatter(params=None):
    """배당에 관한 사항 (page_2019005.html)"""
    return make_api_request('alotMatter', params)

def api_03_tesstkAcqsDspsSttus(params=None):
    """자기주식 취득 및 처분 현황 (page_2019006.html)"""
    return make_api_request('tesstkAcqsDspsSttus', params)

def api_04_hyslrSttus(params=None):
    """최대주주 현황 (page_2019007.html)"""
    return make_api_request('hyslrSttus', params)

def api_05_hyslrChgSttus(params=None):
    """최대주주 변동현황 (page_2019008.html)"""
    return make_api_request('hyslrChgSttus', params)

def api_06_mrhlSttus(params=None):
    """소액주주 현황 (page_2019009.html)"""
    return make_api_request('mrhlSttus', params)

def api_07_exctvSttus(params=None):
    """임원 현황 (page_2019010.html)"""
    return make_api_request('exctvSttus', params)

def api_08_empSttus(params=None):
    """직원 현황 (page_2019011.html)"""
    return make_api_request('empSttus', params)

def api_09_hmvAuditIndvdlBySttus(params=None):
    """이사·감사의 개인별 보수현황 (page_2019012.html)"""
    return make_api_request('hmvAuditIndvdlBySttus', params)

def api_10_hmvAuditAllSttus(params=None):
    """이사·감사의 전체 보수현황 (page_2019013.html)"""
    return make_api_request('hmvAuditAllSttus', params)

def api_11_indvdlByPay(params=None):
    """개인별 보수지급 금액(5억이상 상위5인) (page_2019014.html)"""
    return make_api_request('indvdlByPay', params)

def api_12_otrCprInvstmntSttus(params=None):
    """타법인 출자현황 (page_2019015.html)"""
    return make_api_request('otrCprInvstmntSttus', params)

def api_13_stockTotqySttus(params=None):
    """주식의 총수현황 (page_2020002.html)"""
    return make_api_request('stockTotqySttus', params)

def api_14_detScritsIsuAcmslt(params=None):
    """기타증권 발행을 통한 자금조달 내역 (page_2020003.html)"""
    return make_api_request('detScritsIsuAcmslt', params)

def api_15_entrprsBilScritsNrdmpBlce(params=None):
    """기업어음증권 미상환 잔액 (page_2020004.html)"""
    return make_api_request('entrprsBilScritsNrdmpBlce', params)

def api_16_srtpdPsndbtNrdmpBlce(params=None):
    """단기사채 미상환 잔액 (page_2020005.html)"""
    return make_api_request('srtpdPsndbtNrdmpBlce', params)

def api_17_cprndNrdmpBlce(params=None):
    """회사채 미상환 잔액 (page_2020006.html)"""
    return make_api_request('cprndNrdmpBlce', params)

def api_18_newCaplScritsNrdmpBlce(params=None):
    """신종자본증권 미상환 잔액 (page_2020007.html)"""
    return make_api_request('newCaplScritsNrdmpBlce', params)

def api_19_cndlCaplScritsNrdmpBlce(params=None):
    """조건부자본증권 미상환 잔액 (page_2020008.html)"""
    return make_api_request('cndlCaplScritsNrdmpBlce', params)

def api_20_accnutAdtorNmNdAdtOpinion(params=None):
    """회계감사인의 명칭 및 감사의견 (page_2020009.html)"""
    return make_api_request('accnutAdtorNmNdAdtOpinion', params)

def api_21_adtServcCnclsSttus(params=None):
    """감사용역 체결현황 (page_2020010.html)"""
    return make_api_request('adtServcCnclsSttus', params)

def api_22_accnutAdtorNonAdtServcCnclsSttus(params=None):
    """회계감사인의 비감사용역 체결현황 (page_2020011.html)"""
    return make_api_request('accnutAdtorNonAdtServcCnclsSttus', params)

def api_23_outcmpnyDrctrNdChangeSttus(params=None):
    """사외이사 및 그 변동현황 (page_2020012.html)"""
    return make_api_request('outcmpnyDrctrNdChangeSttus', params)

def api_24_unrstExctvMendngSttus(params=None):
    """등기임원 보수현황 (page_2020013.html)"""
    return make_api_request('unrstExctvMendngSttus', params)

def api_25_drctrAdtAllMendngSttusGmtsckConfmAmount(params=None):
    """이사·감사 전체의 보수현황(주총승인금액) (page_2020014.html)"""
    return make_api_request('drctrAdtAllMendngSttusGmtsckConfmAmount', params)

def api_26_drctrAdtAllMendngSttusMendngPymntamtTyCl(params=None):
    """이사·감사 전체의 보수현황(보수지급금액 유형별) (page_2020015.html)"""
    return make_api_request('drctrAdtAllMendngSttusMendngPymntamtTyCl', params)

def api_27_pssrpCptalUseDtls(params=None):
    """신주인수권증서 자본금 사용내역 (page_2020016.html)"""
    return make_api_request('pssrpCptalUseDtls', params)

def api_28_prvsrpCptalUseDtls(params=None):
    """구주인수권증서 자본금 사용내역 (page_2020017.html)"""
    return make_api_request('prvsrpCptalUseDtls', params)

# =============================================================================
# 유틸리티 함수들
# =============================================================================

def save_data_to_file(data: Dict, filename: str = None, directory: str = "dart_data"):
    """API 응답 데이터를 JSON 파일로 저장"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dart_api_data_{timestamp}.json"
    
    filepath = os.path.join(directory, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 데이터 저장 완료: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ 저장 실패: {e}")
        return None

def save_all_company_data(corp_code: str, year: str = '2024', report_code: str = '11011'):
    """특정 회사의 모든 API 데이터를 수집하고 저장"""
    params = {
        'corp_code': corp_code,
        'bsns_year': year,
        'reprt_code': report_code
    }
    
    print(f"🏢 회사 전체 데이터 수집 중 (고유번호: {corp_code}, 연도: {year})")
    
    # 모든 API 함수 목록
    all_apis = [
        (api_01_irdsSttus, "주식발행_감소현황"),
        (api_02_alotMatter, "배당에_관한_사항"),
        (api_03_tesstkAcqsDspsSttus, "자기주식_취득_및_처분_현황"),
        (api_04_hyslrSttus, "최대주주_현황"),
        (api_05_hyslrChgSttus, "최대주주_변동현황"),
        (api_06_mrhlSttus, "소액주주_현황"),
        (api_07_exctvSttus, "임원_현황"),
        (api_08_empSttus, "직원_현황"),
        (api_09_hmvAuditIndvdlBySttus, "이사감사_개인별_보수현황"),
        (api_10_hmvAuditAllSttus, "이사감사_전체_보수현황"),
        (api_11_indvdlByPay, "개인별_보수지급_금액"),
        (api_12_otrCprInvstmntSttus, "타법인_출자현황"),
        (api_13_stockTotqySttus, "주식의_총수현황"),
        (api_14_detScritsIsuAcmslt, "기타증권_발행_자금조달_내역"),
        (api_15_entrprsBilScritsNrdmpBlce, "기업어음증권_미상환_잔액"),
        (api_16_srtpdPsndbtNrdmpBlce, "단기사채_미상환_잔액"),
        (api_17_cprndNrdmpBlce, "회사채_미상환_잔액"),
        (api_18_newCaplScritsNrdmpBlce, "신종자본증권_미상환_잔액"),
        (api_19_cndlCaplScritsNrdmpBlce, "조건부자본증권_미상환_잔액"),
        (api_20_accnutAdtorNmNdAdtOpinion, "회계감사인_명칭_및_감사의견"),
        (api_21_adtServcCnclsSttus, "감사용역_체결현황"),
        (api_22_accnutAdtorNonAdtServcCnclsSttus, "회계감사인_비감사용역_체결현황"),
        (api_23_outcmpnyDrctrNdChangeSttus, "사외이사_및_변동현황"),
        (api_24_unrstExctvMendngSttus, "등기임원_보수현황"),
        (api_25_drctrAdtAllMendngSttusGmtsckConfmAmount, "이사감사_전체_보수현황_주총승인금액"),
        (api_26_drctrAdtAllMendngSttusMendngPymntamtTyCl, "이사감사_전체_보수현황_보수지급금액_유형별"),
        (api_27_pssrpCptalUseDtls, "신주인수권증서_자본금_사용내역"),
        (api_28_prvsrpCptalUseDtls, "구주인수권증서_자본금_사용내역")
    ]
    
    company_data = {
        'metadata': {
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': report_code,
            'collection_date': datetime.now().isoformat(),
            'total_apis': len(all_apis)
        },
        'data': {}
    }
    
    successful = 0
    
    for i, (api_func, api_name) in enumerate(all_apis, 1):
        print(f"[{i:2d}/{len(all_apis)}] {api_name}")
        
        try:
            result = api_func(params)
            if result:
                company_data['data'][api_name] = result
                successful += 1
                print(f"   ✅ 성공")
            else:
                print(f"   ❌ 실패")
                company_data['data'][api_name] = None
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            company_data['data'][api_name] = None
        
        # API 호출 간격
        if i < len(all_apis):
            time.sleep(0.5)
    
    # 결과 저장
    company_data['metadata']['successful_apis'] = successful
    filename = f"company_{corp_code}_{year}_{report_code}.json"
    filepath = save_data_to_file(company_data, filename)
    
    print(f"\n📊 수집 완료: {successful}/{len(all_apis)} API 성공")
    print(f"💾 저장 위치: {filepath}")
    
    return company_data

def export_to_excel(json_file: str):
    """JSON 데이터를 Excel 파일로 변환 (pandas 필요)"""
    try:
        import pandas as pd
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        excel_file = json_file.replace('.json', '.xlsx')
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 메타데이터 시트
            metadata_df = pd.DataFrame([data['metadata']])
            metadata_df.to_excel(writer, sheet_name='metadata', index=False)
            
            # 각 API 데이터를 별도 시트로
            for api_name, api_data in data['data'].items():
                if api_data and 'list' in api_data and api_data['list']:
                    df = pd.DataFrame(api_data['list'])
                    # 시트 이름 길이 제한 (31자)
                    sheet_name = api_name[:31] if len(api_name) > 31 else api_name
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"📊 Excel 파일 생성: {excel_file}")
        return excel_file
        
    except ImportError:
        print("❌ pandas가 설치되지 않았습니다. pip install pandas openpyxl")
        return None
    except Exception as e:
        print(f"❌ Excel 변환 실패: {e}")
        return None

def test_all_apis():
    """모든 API를 순차적으로 테스트"""
    api_functions = [
        (api_01_irdsSttus, "주식발행 감소현황"),
        (api_02_alotMatter, "배당에 관한 사항"),
        (api_03_tesstkAcqsDspsSttus, "자기주식 취득 및 처분 현황"),
        (api_04_hyslrSttus, "최대주주 현황"),
        (api_05_hyslrChgSttus, "최대주주 변동현황"),
        (api_06_mrhlSttus, "소액주주 현황"),
        (api_07_exctvSttus, "임원 현황"),
        (api_08_empSttus, "직원 현황"),
        (api_09_hmvAuditIndvdlBySttus, "이사·감사의 개인별 보수현황"),
        (api_10_hmvAuditAllSttus, "이사·감사의 전체 보수현황"),
        (api_11_indvdlByPay, "개인별 보수지급 금액"),
        (api_12_otrCprInvstmntSttus, "타법인 출자현황"),
        (api_13_stockTotqySttus, "주식의 총수현황"),
        (api_14_detScritsIsuAcmslt, "기타증권 발행을 통한 자금조달 내역"),
        (api_15_entrprsBilScritsNrdmpBlce, "기업어음증권 미상환 잔액"),
        (api_16_srtpdPsndbtNrdmpBlce, "단기사채 미상환 잔액"),
        (api_17_cprndNrdmpBlce, "회사채 미상환 잔액"),
        (api_18_newCaplScritsNrdmpBlce, "신종자본증권 미상환 잔액"),
        (api_19_cndlCaplScritsNrdmpBlce, "조건부자본증권 미상환 잔액"),
        (api_20_accnutAdtorNmNdAdtOpinion, "회계감사인의 명칭 및 감사의견"),
        (api_21_adtServcCnclsSttus, "감사용역 체결현황"),
        (api_22_accnutAdtorNonAdtServcCnclsSttus, "회계감사인의 비감사용역 체결현황"),
        (api_23_outcmpnyDrctrNdChangeSttus, "사외이사 및 그 변동현황"),
        (api_24_unrstExctvMendngSttus, "등기임원 보수현황"),
        (api_25_drctrAdtAllMendngSttusGmtsckConfmAmount, "이사·감사 전체의 보수현황(주총승인금액)"),
        (api_26_drctrAdtAllMendngSttusMendngPymntamtTyCl, "이사·감사 전체의 보수현황(보수지급금액 유형별)"),
        (api_27_pssrpCptalUseDtls, "신주인수권증서 자본금 사용내역"),
        (api_28_prvsrpCptalUseDtls, "구주인수권증서 자본금 사용내역")
    ]
    
    print("🚀 DART API 전체 테스트 시작")
    print("=" * 60)
    
    successful = 0
    total = len(api_functions)
    
    for i, (api_func, description) in enumerate(api_functions, 1):
        print(f"\n[{i:2d}/{total}] {description}")
        print("-" * 40)
        
        result = api_func()
        if result:
            successful += 1
        
        # API 호출 간격 (서버 부하 방지)
        if i < total:
            time.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"🎯 테스트 완료: {successful}/{total} 성공")
    print("=" * 60)

def search_company_data(corp_code: str, year: str = '2024', report_code: str = '11011'):
    """특정 회사의 모든 데이터 조회"""
    params = {
        'corp_code': corp_code,
        'bsns_year': year,
        'reprt_code': report_code
    }
    
    print(f"🏢 회사 데이터 조회 (고유번호: {corp_code}, 연도: {year})")
    
    # 주요 API만 선별 테스트
    key_apis = [
        (api_04_hyslrSttus, "최대주주 현황"),
        (api_07_exctvSttus, "임원 현황"),
        (api_08_empSttus, "직원 현황"),
        (api_13_stockTotqySttus, "주식의 총수현황"),
    ]
    
    results = {}
    for api_func, description in key_apis:
        print(f"\n📊 {description}")
        result = api_func(params)
        results[description] = result
    
    return results

def main():
    """메인 실행 함수"""
    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌ API 키가 설정되지 않았습니다!")
        print()
        print("🔑 API 키 발급 방법:")
        print("1. https://opendart.fss.or.kr/ 접속")
        print("2. 회원가입 및 로그인")
        print("3. 인증키 신청/관리 메뉴에서 API 키 발급")
        print("4. 스크립트 상단의 API_KEY 변수에 키 입력")
        print()
        print("📝 사용 예시:")
        print("   API_KEY = 'your_40_character_api_key_here'")
        return
    
    print("🎯 DART Open API 테스트 프로그램")
    print(f"📡 API 키: {API_KEY[:10]}...")
    print(f"📊 총 API 개수: 28개")
    print(f"🏢 기본 회사: 삼성전자 (00126380)")
    print()
    
    while True:
        print("=" * 50)
        print("1. 전체 API 테스트")
        print("2. 개별 API 테스트")
        print("3. 특정 회사 조회")
        print("4. 회사 전체 데이터 수집 및 저장")
        print("5. JSON을 Excel로 변환")
        print("6. 종료")
        print("=" * 50)
        
        choice = input("선택하세요 (1-6): ").strip()
        
        if choice == '1':
            test_all_apis()
        elif choice == '2':
            print("개별 API 테스트 예시:")
            print("result = api_04_hyslrSttus()  # 최대주주 현황")
            api_04_hyslrSttus()
        elif choice == '3':
            corp_code = input("회사 고유번호 (8자리, 기본값 00126380): ").strip() or "00126380"
            year = input("사업연도 (기본값 2024): ").strip() or "2024"
            search_company_data(corp_code, year)
        elif choice == '4':
            corp_code = input("회사 고유번호 (8자리, 기본값 00126380): ").strip() or "00126380"
            year = input("사업연도 (기본값 2024): ").strip() or "2024"
            report_code = input("보고서 코드 (기본값 11011): ").strip() or "11011"
            print("\n🚀 전체 데이터 수집을 시작합니다...")
            save_all_company_data(corp_code, year, report_code)
        elif choice == '5':
            json_files = [f for f in os.listdir('.') if f.endswith('.json') and 'company_' in f]
            if json_files:
                print("📁 JSON 파일 목록:")
                for i, f in enumerate(json_files, 1):
                    print(f"  {i}. {f}")
                try:
                    idx = int(input("변환할 파일 번호: ")) - 1
                    if 0 <= idx < len(json_files):
                        export_to_excel(json_files[idx])
                    else:
                        print("❌ 잘못된 번호입니다.")
                except ValueError:
                    print("❌ 숫자를 입력하세요.")
            else:
                print("❌ JSON 파일이 없습니다. 먼저 데이터를 수집하세요.")
        elif choice == '6':
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()