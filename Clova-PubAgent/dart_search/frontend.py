import requests
from flask import Flask, render_template, request, session
import markdown
import sys

# Python print 버퍼링 비활성화
sys.stdout.flush()

app = Flask(__name__)

# 설정
API_URL = "http://127.0.0.1:6000/summarize"

def convert_raw_data_to_html(raw_data):
    """원본 데이터를 HTML 테이블로 변환"""
    if not raw_data:
        return ""

    html_parts = []

    # API 데이터 처리 (api_01, api_02 등)
    if 'api_data' in raw_data:
        html_parts.append("<h4>📊 API 데이터</h4>")
        api_data = raw_data['api_data']

        for api_key, data_list in api_data.items():
            if isinstance(data_list, list) and data_list:
                html_parts.append(f"<h5>{api_key.upper()}</h5>")
                html_parts.append(dict_list_to_table(data_list))
            elif data_list:  # 단일 딕셔너리인 경우
                html_parts.append(f"<h5>{api_key.upper()}</h5>")
                html_parts.append(dict_to_table(data_list))

    # 메타데이터 처리 (마지막에 표시)
    if 'metadata' in raw_data:
        html_parts.append("<h4>📋 메타데이터</h4>")
        html_parts.append(dict_to_table(raw_data['metadata']))

    return "<div class='raw-data-tables'>" + "".join(html_parts) + "</div>"

def dict_list_to_table(data_list):
    """딕셔너리 리스트를 HTML 테이블로 변환"""
    if not data_list:
        return ""

    # 헤더 생성
    headers = list(data_list[0].keys())
    html = "<table class='data-table'><thead><tr>"
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"

    # 데이터 행 생성
    for row in data_list:
        html += "<tr>"
        for header in headers:
            value = row.get(header, "-")
            html += f"<td>{value}</td>"
        html += "</tr>"

    html += "</tbody></table>"
    return html

def dict_to_table(data_dict):
    """단일 딕셔너리를 HTML 테이블로 변환"""
    if not data_dict:
        return ""

    html = "<table class='data-table'><tbody>"
    for key, value in data_dict.items():
        html += f"<tr><th>{key}</th><td>{value}</td></tr>"
    html += "</tbody></table>"
    return html

@app.route("/", methods=["GET", "POST"])
def index():
    summary = ""
    error = ""
    query = ""
    raw_data = None
    loading = False

    print(f"[FRONTEND] 요청 메소드: {request.method}", flush=True)

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        print(f"[FRONTEND] POST 요청 받음")
        print(f"[FRONTEND] 사용자 질문: '{query}'")

        if not query:
            error = "질문을 입력해주세요."
            print(f"[FRONTEND] 에러: 빈 질문")
        else:
            try:
                print(f"[FRONTEND] API 요청 준비 중...")

                print("[DEBUG] API 요청 시작...")
                response = requests.post(API_URL, json={"query": query}, timeout=120)  # 2분으로 증가
                print(f"[DEBUG] API 응답 상태: {response.status_code}")

                if response.status_code == 200:
                    print("[DEBUG] API 응답 성공, JSON 파싱 중...")
                    result = response.json()
                    raw_summary = result.get("summary", "요약을 생성할 수 없습니다.")
                    raw_data = result.get("raw_data")  # 원본 데이터 받기
                    print(f"[DEBUG] 요약 길이: {len(raw_summary)} 문자")
                    print(f"[DEBUG] 원본 데이터 포함: {'있음' if raw_data else '없음'}")

                    # Markdown을 HTML로 변환
                    summary = markdown.markdown(raw_summary, extensions=['nl2br'])

                    # 원본 데이터를 HTML 테이블로 변환
                    if raw_data:
                        raw_data = convert_raw_data_to_html(raw_data)

                    print("[DEBUG] 마크다운 변환 완료")
                else:
                    print(f"[DEBUG] API 오류 응답: {response.text}")
                    try:
                        error_detail = response.json().get("detail", "알 수 없는 오류")
                    except:
                        error_detail = response.text
                    error = f"요청 처리 중 오류가 발생했습니다: {error_detail}"

            except requests.exceptions.Timeout:
                error = "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            except requests.exceptions.ConnectionError:
                error = "API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
            except requests.exceptions.RequestException as e:
                error = f"네트워크 오류가 발생했습니다: {str(e)}"
            except Exception as e:
                error = f"예상치 못한 오류가 발생했습니다: {str(e)}"

    return render_template(
        "index.html",
        summary=summary,
        error=error,
        query=query,
        raw_data=raw_data,
        loading=loading
    )

@app.route("/analyze_mode", methods=["POST"])
def analyze_mode():
    """모드별 분석 엔드포인트"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        mode = data.get('mode', '')
        summary = data.get('summary', '')

        if not query:
            return {"error": "질문을 입력해주세요."}, 400

        if mode not in ['beginner', 'analyst']:
            return {"error": "올바른 모드를 선택해주세요."}, 400

        print(f"[FRONTEND] 모드 분석 요청: {mode}, 질문: {query}")

        # API 요청
        api_response = requests.post(
            "http://127.0.0.1:6000/analyze_mode",
            json={"query": query, "mode": mode, "summary": summary},
            timeout=60
        )

        if api_response.status_code == 200:
            result = api_response.json()
            # 마크다운을 HTML로 변환
            analysis_html = markdown.markdown(result.get("analysis", ""), extensions=['nl2br'])
            return {"analysis": analysis_html, "success": True}
        else:
            error_detail = api_response.json().get("detail", "알 수 없는 오류")
            return {"error": error_detail}, api_response.status_code

    except Exception as e:
        print(f"[FRONTEND] 모드 분석 오류: {e}")
        return {"error": f"분석 중 오류가 발생했습니다: {str(e)}"}, 500

@app.errorhandler(404)
def not_found(error):
    return render_template("index.html", error="페이지를 찾을 수 없습니다."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("index.html", error="서버 내부 오류가 발생했습니다."), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6001, debug=True)
