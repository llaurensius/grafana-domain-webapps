import yaml
import httpx
import os
from typing import List
from app.config import settings

class PrometheusService:
    @staticmethod
    def sync_targets_file(active_domains: List[str]):
        """Writes active domains to the shared yaml file for Prometheus file_sd_configs"""
        targets_data = []
        if active_domains:
            targets_data.append({
                "targets": active_domains,
                "labels": {
                    "job": "blackbox_dynamic"
                }
            })
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(settings.TARGETS_FILE_PATH), exist_ok=True)
        
        with open(settings.TARGETS_FILE_PATH, 'w') as f:
            yaml.dump(targets_data, f)
            
    _cached_metrics = None
    _cached_time = 0

    @staticmethod
    async def get_cached_metrics():
        import time
        now = time.time()
        # Return cached data if younger than 15 seconds
        if PrometheusService._cached_metrics is not None and (now - PrometheusService._cached_time < 15):
            return PrometheusService._cached_metrics
            
        metrics = await PrometheusService.query_probe_metrics()
        if metrics is not None:
            PrometheusService._cached_metrics = metrics
            PrometheusService._cached_time = now
        return metrics

    @staticmethod
    async def query_probe_metrics():
        """Queries Prometheus for current probe status, SSL expiry, HTTP status codes, and DNS times for all domains"""
        try:
            async with httpx.AsyncClient() as client:
                import asyncio
                
                async def fetch_metric(query: str):
                    res = await client.get(
                        f"{settings.PROMETHEUS_URL}/api/v1/query",
                        params={"query": query}
                    )
                    if res.status_code == 200:
                        return res.json().get('data', {}).get('result', [])
                    return []

                results = await asyncio.gather(
                    fetch_metric('probe_success'),
                    fetch_metric('probe_ssl_earliest_cert_expiry'),
                    fetch_metric('probe_http_status_code'),
                    fetch_metric('probe_dns_lookup_time_seconds'),
                    fetch_metric('probe_ip_addr_hash')
                )

                return {
                    "success": results[0],
                    "ssl": results[1],
                    "status_code": results[2],
                    "dns": results[3],
                    "ip_hash": results[4]
                }
        except Exception as e:
            print(f"Error querying Prometheus: {e}")
            return None # Return None to indicate connection failure
    @staticmethod
    async def check_health() -> dict:
        """Checks if Prometheus is up and has targets configured"""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{settings.PROMETHEUS_URL}/api/v1/query", params={"query": "up"})
                res.raise_for_status()
                data = res.json()
                
                # Check if we have any data returning
                has_data = len(data.get('data', {}).get('result', [])) > 0
                return {
                    "status": "UP",
                    "has_data": has_data
                }
        except Exception as e:
            return {
                "status": "DOWN",
                "has_data": False,
                "error": str(e)
            }

    @staticmethod
    async def fetch_exact_error(url: str) -> str:
        """Fetches exact raw error logs from blackbox exporter for a specific URL"""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"http://monitoring-blackbox:9115/probe", 
                    params={"target": url, "debug": "true", "module": "http_2xx"}
                )
                import re
                errors = []
                for line in resp.text.split('\n'):
                    if 'level=error' in line and 'err=' in line:
                        match = re.search(r'err="((?:\\.|[^"\\])*)"', line)
                        if match:
                            err_str = match.group(1).replace('\\"', '"')
                            if err_str not in errors:
                                errors.append(err_str)
                if errors:
                    return " | ".join(errors)
                return "Unknown error from probe logs"
        except Exception as e:
            return f"Fetch log error: {str(e)}"

    @staticmethod
    async def query_error_classification(instance: str) -> str:
        """Queries detailed metrics to classify why a probe failed"""
        try:
            async with httpx.AsyncClient() as client:
                # Check HTTP Status Code
                resp_status = await client.get(
                    f"{settings.PROMETHEUS_URL}/api/v1/query",
                    params={"query": f'probe_http_status_code{{instance="{instance}"}}'}
                )
                
                # Check DNS Lookup Time
                resp_dns = await client.get(
                    f"{settings.PROMETHEUS_URL}/api/v1/query",
                    params={"query": f'probe_dns_lookup_time_seconds{{instance="{instance}"}}'}
                )
                
                status_code_data = resp_status.json().get('data', {}).get('result', [])
                dns_data = resp_dns.json().get('data', {}).get('result', [])
                
                status_code = float(status_code_data[0]['value'][1]) if status_code_data else 0
                dns_time = float(dns_data[0]['value'][1]) if dns_data else 0
                
                # Error Classifier Logic
                if dns_time == 0 or not dns_data:
                    return "DNS Error / Unreachable"
                if status_code == 0:
                    return "Connection Timeout / SSL Error"
                if 400 <= status_code < 500:
                    return f"HTTP 4xx Client Error (Code: {int(status_code)})"
                if status_code >= 500:
                    return f"HTTP 5xx Server Error (Code: {int(status_code)})"
                
                return "Unknown Error"
        except Exception as e:
            return "Prometheus Fetch Error"
