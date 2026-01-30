import psutil, os, subprocess, logging
from kagemori_nginx.config import KagemoriNGINXConfig
from kagemori_nginx.dir import create_directory_for_path

class KagemoriNGINX:
    NGINX_STATE_RUNNING = 1
    NGINX_STATE_STOPPED = 0

    def __init__(self, nginx_binary="nginx", nginx_configuration_path="nginx-conf", nginx_pid_file="nginx.pid", resolver="1.1.1.1", kagemori_socket_file="", listen_socket="", reload_when_start_called_if_running=True):
        self.nginx_binary = nginx_binary
        self.nginx_configuration_path = nginx_configuration_path
        self.nginx_pid_file = os.path.join(nginx_configuration_path, nginx_pid_file)
        self.nginx_state = KagemoriNGINX.NGINX_STATE_STOPPED
        self.kagemori_socket_file = kagemori_socket_file
        self.listen_socket = listen_socket

        create_directory_for_path(self.nginx_configuration_path)
        create_directory_for_path(os.path.join(self.nginx_configuration_path, "logs"))
        create_directory_for_path(os.path.join(self.nginx_configuration_path, "tmp"))
        create_directory_for_path(os.path.join(self.nginx_configuration_path, "tmp", "client_body"))
        create_directory_for_path(os.path.join(self.nginx_configuration_path, "tmp", "proxy"))
        create_directory_for_path(os.path.join(self.nginx_configuration_path, "tmp", "fastcgi"))
        create_directory_for_path(os.path.join(self.nginx_configuration_path, "tmp", "uwsgi"))
        create_directory_for_path(os.path.join(self.nginx_configuration_path, "tmp", "scgi"))

        self.reload_when_start_called_if_running = reload_when_start_called_if_running

        self._nginx_pid = None
        self.config = KagemoriNGINXConfig(
            nginx_configuration_directory = self.nginx_configuration_path,
            nginx_configuration_file = "nginx.conf",
            upstream_socket=self.kagemori_socket_file,
            listen_socket=self.listen_socket,
            resolver=resolver
        )

        self.logger = logging.getLogger()

    def start(self):
        self._update_nginx_pid()
        self._update_nginx_state()

        if self.nginx_state == KagemoriNGINX.NGINX_STATE_STOPPED:
            # Start NGINX
            self._subprocess_start_nginx()
            return True
        
        if self.reload_when_start_called_if_running:
            self._subprocess_reload_nginx()
            return True

        self.logger.warn(f"NGINX seems to already be running. PID {self._nginx_pid}. Consider using reload().")
        return False

    def stop(self):
        self._update_nginx_pid()
        self._update_nginx_state()

        if self.nginx_state == KagemoriNGINX.NGINX_STATE_RUNNING:
            # Stop NGINX
            self._subprocess_stop_nginx()
            return True

        self.logger.warn(f"NGINX is already stopped. No action was taken.")
        return False

    def reload(self):
        self._update_nginx_pid()
        self._update_nginx_state()

        if self.nginx_state == KagemoriNGINX.NGINX_STATE_RUNNING:
            # Reload NGINX
            self._subprocess_reload_nginx()
            return True

        self.logger.warn(f"NGINX is not running. No action was taken.")
        return False

    def _subprocess_reload_nginx(self):
        return subprocess.run([self.nginx_binary, "-p", self.nginx_configuration_path, "-c", "nginx.conf", "-s", "reload"])

    def _subprocess_stop_nginx(self):
        return subprocess.run([self.nginx_binary, "-p", self.nginx_configuration_path, "-c", "nginx.conf", "-s", "stop"])

    def _subprocess_start_nginx(self):
        return subprocess.run([self.nginx_binary, "-p", self.nginx_configuration_path, "-c", "nginx.conf"])

    def _update_nginx_pid(self):
        self._nginx_pid = KagemoriNGINX._get_nginx_pid(self.nginx_pid_file)

    def _update_nginx_state(self):
        state = KagemoriNGINX._get_nginx_state(self._nginx_pid)
        if state:
            self.nginx_state = KagemoriNGINX.NGINX_STATE_RUNNING
        else:
            self.nginx_state = KagemoriNGINX.NGINX_STATE_STOPPED

    @staticmethod
    def _get_nginx_pid(nginx_pid_file):
        if not os.path.exists(nginx_pid_file):
            return None

        with open(nginx_pid_file, "r"):
            return nginx_pid_file.read().strip()

    @staticmethod
    def _get_nginx_state(nginx_pid):
        # TODO: Stale PIDs could cause this to return true when NGINX is not actually running
        return psutil.pid_exists(nginx_pid)
