# 40x Bypass Tool 사용 가이드

이 문서는 `bypass_40x.py` 도구의 사용 방법을 설명합니다.

## 기본 사용법 (Basic Usage)

대상 URL을 지정하여 스크립트를 실행합니다. `http/https` 프로토콜을 생략하면 기본적으로 http로 시도합니다.

```bash
python3 bypass_40x.py --url https://target.com/admin
```

## 상세 출력 모드 (Verbose Mode) - 권장

기본적으로 이 도구는 "의미 있는" 결과(상태 코드 변경 또는 응답 크기의 급격한 차이)만 출력합니다. **모든** 시도 결과를 확인하려면 상세 출력 플래그를 사용하세요.

```bash
python3 bypass_40x.py --url https://target.com/admin --verbose
# 또는
python3 bypass_40x.py --url https://target.com/admin -v
```

## 프록시 사용 (Burp Suite 등)

트래픽을 분석하거나 IP 차단(예: `kt.com` 사례)을 우회해야 할 경우 프록시를 사용하세요.

1.  프록시 설정 (예: Burp Suite가 `127.0.0.1:8080`에서 리스닝 중일 때).
2.  `--proxy` 옵션과 함께 SSL 인증서 오류 무시를 위해 `--insecure` 옵션을 사용합니다.

```bash
python3 bypass_40x.py --url https://target.com/admin --proxy http://127.0.0.1:8080 --insecure
```

## 문제 해결 (Troubleshooting)

### 연결 시간 초과 (Connection Timeouts)
`ConnectTimeoutError` 또는 "Max retries exceeded" 오류가 발생하면, 대상 서버가 방화벽 레벨에서 IP를 차단했을 가능성이 높습니다.
**해결책**: 프록시 서버나 VPN을 사용하여 IP를 변경해서 다시 시도하세요.

### 결과가 출력되지 않음 (Empty Output)
툴이 실행되었는데 Baseline 외에 아무것도 출력되지 않는 경우:
1.  대상 서버가 모든 요청을 리다이렉트(예: 301로 로그인 페이지 이동)하여, Baseline과 상태 코드가 동일하기 때문에 "차이점"이 발견되지 않은 것입니다.
2.  `--verbose` 옵션을 사용하여 실제로 어떤 응답이 오고 있는지 확인하세요.

## 주요 기능 (Features Overview)
- **세션 재사용 (Session Reuse)**: TCP 연결(Keep-Alive)을 재사용하여 속도가 빠르고 의심을 덜 받습니다.
- **브라우저 위장 (Browser Masquerading)**: 실제 브라우저처럼 보이도록 User-Agent 및 Chrome 전용 헤더(`Sec-Ch-Ua` 등)를 전송합니다.
- **스마트 검증 (Smart Validation)**: URL 스키마를 자동으로 수정하고 인자를 검증합니다.

## 포함된 테스트 기법 (Included Bypass Techniques)

이 도구는 다음과 같은 다양한 우회 기법을 자동으로 수행합니다.

### 1. HTTP Verbs (메소드 우회)
ACL이 특정 메소드(예: GET)만 차단할 수 있음을 악용합니다.
- `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`
- `PROPFIND` (WebDAV), `OPTIONS`, `TRACE`, `CONNECT`
- `INVENTED` (존재하지 않는 메소드로 기본 처리 방식 확인)

### 2. HTTP Headers (헤더 조작)
**IP Spoofing (내부망 위장)**
서버가 특정 헤더를 신뢰하여 요청을 로컬호스트나 내부 IP로 인식하도록 속입니다.
- Headers: `X-Forwarded-For`, `X-Originating-IP`, `Client-IP` 등
- Values: `127.0.0.1`, `localhost`, `192.168.1.1` 등

**URL Rewriting (경로 재작성)**
프론트엔드 서버가 헤더의 경로를 실제 경로로 신뢰하는 취약점을 이용합니다.
- `X-Original-URL`, `X-Rewrite-URL` 등

### 3. Path Manipulation (경로 조작)
문자열 기반의 ACL 규칙을 우회하기 위해 경로를 변형합니다.

**탐색 및 정규화 (Traversal & Normalization)**
- `/path/./`, `//path//`, `/path/..;/` (Tomcat 등)

**문자 및 인코딩 (Characters & Encoding)**
- `/path%20` (공백), `/path%09` (탭), `/path?`
- URL 인코딩: `/%2e/path`

**대소문자 변형 (Case Sensitivity)**
- `/PATH`, `/pAtH`

**프레임워크 특화 (Framework Specifics)**
- Tomcat/Java: `/path;`, `/path;param=value`, `/path;index.html`
- ASP.NET/IIS/Nginx: 확장자 추가(`.json`, `.php` 등)

### 4. Protocol Pollution (프로토콜 오염)
- HTTP Smuggling 징후 탐지 (`Transfer-Encoding: chunked`)
- 메소드 오버라이드 (`_method: POST` 바디 사용)

