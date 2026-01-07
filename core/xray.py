from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from fastapi import FastAPI
from aws_xray_sdk.core.models.trace_header import TraceHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
import os

class XRayMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        recorder = None,
    ) -> None:
        super().__init__(app)
        self.recorder = recorder or xray_recorder

        if not self.recorder.initialized:
            self.recorder.configure(
                service='chatbot',
                sampling=True,
                context_missing='LOG_ERROR',
                plugins=('EC2Plugin', 'ECSPlugin'),
                daemon_address='127.0.0.1:2000',
                dynamic_naming='*'
            )
            patch_all()

    async def dispatch(self, request, call_next):
        # Get trace header
        trace_header = request.headers.get('X-Amzn-Trace-Id', None)
        if trace_header:
            xray_header = TraceHeader.from_header_str(trace_header)
        else:
            xray_header = None

        # Start segment
        segment = self.recorder.begin_segment(
            name='chatbot',
            traceid=xray_header.root if xray_header else None,
            parent_id=xray_header.parent if xray_header else None,
            sampling=xray_header.sampled if xray_header else None,
        )

        try:
            # Add request data to segment
            segment.put_http_meta('url', str(request.url))
            segment.put_http_meta('method', request.method)
            segment.put_http_meta('user_agent', request.headers.get('User-Agent', ''))
            segment.put_http_meta('client_ip', request.client.host)

            # Call next middleware and get response
            response = await call_next(request)

            # Add response data to segment
            segment.put_http_meta('status', response.status_code)
            return response

        except Exception as e:
            # Add error data to segment
            segment.put_error(e)
            raise
        finally:
            # End segment
            self.recorder.end_segment()
