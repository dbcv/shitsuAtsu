import time

from django.utils.deprecation import MiddlewareMixin

from .models import AccessLog


class AccessLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 静的ファイルやメディアへのアクセスは除外
        if (
            request.path.startswith("/static/")
            or request.path.startswith("/media/")
            or request.path.startswith("/admin/")
            or request.path.endswith("png")
        ):
            return

        user = request.user if request.user.is_authenticated else None
        ip = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
        referer = request.META.get("HTTP_REFERER", "")

        AccessLog.objects.create(
            user=user,
            path=request.path,
            method=request.method,
            ip_address=ip,
            user_agent=user_agent,
            referer=referer,
        )

    def _get_client_ip(self, request):
        # X-Forwarded-For 対応（Nginxやリバースプロキシ経由でも取得可能）
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")


class TimingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.perf_counter()

    def process_response(self, request, response):
        elapsed = time.perf_counter() - getattr(
            request, "start_time", time.perf_counter()
        )
        latency_ms = elapsed * 1000
        response["X-Request-Latency-ms"] = f"{latency_ms:.2f}"

        if hasattr(response, "content"):
            size = len(response.content)
        elif hasattr(response, "streaming_content"):
            size = 0
            for chunk in response.streaming_content:
                size += len(chunk)
        else:
            size = 0

        response["X-Response-Size-bytes"] = str(size)
        print(
            f"Request to {request.path} took {latency_ms:.2f} ms and returned {size} bytes"
        )
        return response
