import http.server
import socketserver

# 定义服务器的端口号
PORT = 8056

# 使用SimpleHTTPRequestHandler处理请求
Handler = http.server.SimpleHTTPRequestHandler

# 创建服务器
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Server running at http://localhost:{}".format(PORT))
    # 启动服务器
    httpd.serve_forever()