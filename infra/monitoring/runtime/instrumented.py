"""Compose entry point; backend source stays owned by Member 2."""
import os
from secret_injection import inject
inject()
from app.main import app as backend
from instrumentation import MetricsApp

app = MetricsApp(backend, os.environ['MEMBER4_METRICS_TOKEN_FILE'])
