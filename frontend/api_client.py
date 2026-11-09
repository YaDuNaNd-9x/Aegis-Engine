
import os
import requests

API_BASE_URL = os.getenv(
    "AEGIS_API_URL",
    "http://127.0.0.1:8000"
)

TIMEOUT = 180


def get(endpoint, params=None):
    response = requests.get(
        f"{API_BASE_URL}{endpoint}",
        params=params,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response


def post(endpoint, json=None, files=None, data=None):
    response = requests.post(
        f"{API_BASE_URL}{endpoint}",
        json=json,
        files=files,
        data=data,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response


def get_health():
    return get("/api/v1/health/")


def send_chat(message):
    return post(
        "/api/v1/chat/",
        json={"message": message},
    )


def upload_document(uploaded_file):
    return post(
        "/api/v1/documents/upload",
        files={
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type,
            )
        },
    )


def search_documents(query):
    return post(
        "/api/v1/documents/search",
        json={"query": query},
    )


def get_document_stats():
    return get("/api/v1/documents/stats")


def analyze_csv(uploaded_file, question):
    return post(
        "/api/v1/analysis/csv",
        files={
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "text/csv",
            )
        },
        data={"instruction": question},
    )


def generate_report(payload):
    return post(
        "/api/v1/reports/generate",
        json=payload,
    )


def get_reports():
    return get("/api/v1/reports/")


def download_report(report_id):
    return get(f"/api/v1/reports/download/{report_id}")


def get_audit_logs(params=None):
    return get("/api/v1/audit/", params=params)


def get_audit_stats():
    return get("/api/v1/audit/stats")
