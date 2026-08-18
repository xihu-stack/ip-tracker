"""本地测试用的模拟 OAuth2 SSO 服务器（仅用于开发验证，不部署）。

GET /authorize?redirect_uri&state -> 302 回调地址（带 code+state）
POST /token -> {"access_token": "fake-token"}
GET  /userinfo -> {"preferred_username": "sso_tester"}
"""
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send_json(self, obj):
        body = (str(obj).replace("'", '"')).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/authorize"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            back = q["redirect_uri"][0] + "?code=fakecode123&state=" + urllib.parse.quote(q["state"][0])
            self.send_response(302)
            self.send_header("Location", back)
            self.end_headers()
        elif self.path.startswith("/connect/logout") or self.path.startswith("/logout"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            back = q.get("post_logout_redirect_uri", ["http://127.0.0.1:8000/login"])[0]
            self.send_response(302)
            self.send_header("Location", back)
            self.end_headers()
        elif self.path.startswith("/userinfo"):
            self._send_json('{"access_token":"x","preferred_username":"sso_tester","email":"tester@example.com","name":"SSO测试用户"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith("/token"):
            # 含 id_token，模拟 OIDC 流程（退出时作为 id_token_hint 用）
            fake_id_token = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzc29fdGVzdGVyIiwiaXNzIjoiZmFrZSJ9.fake-signature"
            self._send_json('{"access_token":"fake-token","token_type":"bearer","id_token":"' + fake_id_token + '"}')
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    print("fake SSO on :9999")
    HTTPServer(("127.0.0.1", 9999), Handler).serve_forever()
