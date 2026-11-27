"""Tests for the CyberMentor benchmark suite."""

from bench.benchmark_catalog import (
    benchmark_catalog_filtering,
    benchmark_vulnerability_detection_accuracy,
    benchmark_testclient_endpoints,
    run_benchmark,
)


def test_benchmark_catalog_filtering():
    res = benchmark_catalog_filtering(iterations=10)
    assert res["operations"] == 30
    assert res["throughput_ops_sec"] > 0
    assert res["p50_ms"] >= 0


def test_benchmark_vulnerability_detection_accuracy():
    res = benchmark_vulnerability_detection_accuracy()
    assert res["total_challenges"] > 0
    assert res["accuracy_pct"] == 100.0


def test_benchmark_testclient_endpoints():
    res = benchmark_testclient_endpoints(iterations=5)
    assert res["total_requests"] == 20
    assert res["throughput_req_sec"] > 0
    assert res["p50_ms"] >= 0


def test_run_benchmark_output(tmp_path):
    report_file = tmp_path / "test_report.md"
    res = run_benchmark(report_file)
    assert res["catalog_filtering"]["operations"] > 0
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "Benchmark Summary" in content
    assert "Catalog Query Throughput" in content
