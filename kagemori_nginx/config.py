import os
from chibi_nginx.nginx import to_string

class KagemoriNGINXConfig:
    def __init__(self, nginx_configuration_directory, nginx_configuration_file="nginx.conf", upstream_socket="/tmp/kagemori-user/kagemori.sock", listen_socket="/tmp/kagemori-user/nginx.sock", resolver=""):
        self.default_config = {
            "pid": os.path.join("nginx.pid"),
            "error_log": os.path.join("logs", "error.log"),
            "events": {
                "worker_connections": 768
            },
            "http": {
                "sendfile": "on",
                "types_hash_max_size": 2048,
                "client_body_temp_path": os.path.join("tmp", "client_body"),
                "proxy_temp_path": os.path.join("tmp", "proxy"),
                "fastcgi_temp_path": os.path.join("tmp", "fastcgi"),
                "uwsgi_temp_path": os.path.join("tmp", "uwsgi"),
                "scgi_temp_path": os.path.join("tmp", "scgi"),
                "default_type": "application/octet-stream",
                "gzip": "on",
                "upstream kageauth": {
                    "server": "unix:" + upstream_socket
                },
            }
        }
        self.config = self.default_config
        self.listen_socket = listen_socket
        self.nginx_configuration_directory = nginx_configuration_directory
        self.nginx_configuration_file = nginx_configuration_file
        self.resolver = resolver
        self.write_config()

    def add_server(self, server_name, default_server=False, enable_ssl=False, ssl_certificate=None):
        if self.find_server(server_name) is not None:
            raise KagemoriNGINXConfig.DuplicateServerName(f"{server_name} is already configured")

        if enable_ssl and ssl_certificate is None:
            raise KagemoriNGINXConfig.NoSSLCertificateProvided("enable_ssl is set but ssl_certificate is not set")

        server_config = KagemoriNGINXConfig._generate_server_config(
            listen = self.listen_socket,
            default_server = False,
            resolver = self.resolver,
            server_name = server_name,
            enable_ssl = enable_ssl,
            ssl_certificate = ssl_certificate
        )

        if "server" not in self.config["http"]:
            self.config["http"]["server"] = []
        
        self.config["http"]["server"].append(server_config)
        self.write_config()

    def remove_server(self, server_name):
        if "server" not in self.config["http"]:
            return False

        for i in range(len(self.config["http"]["server"])):
            if self.config["http"]["server"][i]["server_name"] == server_name:
                del self.config["http"]["server"][i]
                self.write_config()
                return True

        return False

    def find_server(self, server_name):
        if "server" not in self.config["http"]:
            return None

        for i in self.config["http"]["server"]:
            if i["server_name"] == server_name:
                return i

        return None

    def write_config(self):
        with open(os.path.join(self.nginx_configuration_directory, self.nginx_configuration_file), "w") as nginx_fp:
            write_data = to_string(self.config)
            nginx_fp.write(write_data)

    @staticmethod
    def _generate_server_config(listen, default_server, resolver, server_name, enable_ssl, ssl_certificate=None):
        listen += "default_server" if default_server else "";
        result = {
            "listen": "unix:" + listen,
            "resolver": resolver,
            "server_name": server_name,
            "location /": {
                "auth_request": "/auth",
                "auth_request_set": ["$kagemori_proxy_target $upstream_http_x_kage_forward", "$kagemori_ssl_cert $upstream_http_x_kage_ssl"],
                "proxy_set_header": ["X-Forwarded-For $proxy_add_x_forwarded_for", "Host $host"],
                "proxy_pass": "https" if enable_ssl else "http" + "://$kagemori_proxy_target",
                "proxy_http_version": "1.1",
                "proxy_set_header": ["Upgrade $http_upgrade", "Connection \"upgrade\"", "Sec-WebSocket-Key $http_sec_websocket_key", "Sec-WebSocket-Version $http_sec_websocket_version", "Sec-WebSocket-Extensions $http_sec_websocket_extensions"],
                "proxy_read_timeout": "86400s"
            },
            "location /auth": {
                "internal": True,
                "proxy_pass": "http://kageauth/api/session",
                "proxy_set_header": ["Host $host", "X-Original-URI $request_uri", "X-Forwarded-For $proxy_add_x_forwarded_for", "X-Forwarded-Proto $scheme"]
            }
        }

        if enable_ssl:
            result["location /"]["proxy_ssl_verify"] = "on"
            result["location /"]["proxy_ssl_trusted_certificate"] = ssl_certificate
            result["location /"]["proxy_ssl_verify_depth"] = "1"

        return result

    class DuplicateServerName(Exception):
        pass

    class NoSSLCertificateProvided(Exception):
        pass
