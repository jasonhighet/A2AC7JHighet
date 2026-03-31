"""Constants for the Investigator Agent.

This module centralizes all magic strings and constants used throughout the codebase
to prevent brittleness and make refactoring easier.
"""

# ===== Tool Names =====
# These must match the @tool decorated function names exactly

TOOL_GET_JIRA_DATA = "get_jira_data"
TOOL_GET_ANALYSIS = "get_analysis"
TOOL_LIST_PLANNING_DOCS = "list_planning_docs"
TOOL_READ_PLANNING_DOC = "read_planning_doc"
TOOL_SEARCH_PLANNING_DOCS = "search_planning_docs"

ALL_TOOL_NAMES = [
    TOOL_GET_JIRA_DATA,
    TOOL_GET_ANALYSIS,
    TOOL_LIST_PLANNING_DOCS,
    TOOL_READ_PLANNING_DOC,
    TOOL_SEARCH_PLANNING_DOCS,
]

# ===== Analysis Types =====
# These are the valid values for the analysis_type parameter of get_analysis

# Metrics
ANALYSIS_UNIT_TEST_RESULTS = "metrics/unit_test_results"
ANALYSIS_TEST_COVERAGE = "metrics/test_coverage_report"
ANALYSIS_PIPELINE_RESULTS = "metrics/pipeline_results"
ANALYSIS_PERFORMANCE_BENCHMARKS = "metrics/performance_benchmarks"
ANALYSIS_SECURITY_SCAN = "metrics/security_scan_results"

VALID_METRICS = [
    ANALYSIS_UNIT_TEST_RESULTS,
    ANALYSIS_TEST_COVERAGE,
    ANALYSIS_PIPELINE_RESULTS,
    ANALYSIS_PERFORMANCE_BENCHMARKS,
    ANALYSIS_SECURITY_SCAN,
]

# Reviews
ANALYSIS_SECURITY_REVIEW = "reviews/security"
ANALYSIS_UAT_REVIEW = "reviews/uat"
ANALYSIS_STAKEHOLDERS_REVIEW = "reviews/stakeholders"

VALID_REVIEWS = [
    ANALYSIS_SECURITY_REVIEW,
    ANALYSIS_UAT_REVIEW,
    ANALYSIS_STAKEHOLDERS_REVIEW,
]

VALID_ANALYSIS_TYPES = VALID_METRICS + VALID_REVIEWS

# ===== Decision Types =====
# Valid readiness decisions the agent can make

DECISION_READY = "ready"
DECISION_NOT_READY = "not_ready"
DECISION_NEEDS_INFO = "needs_info"
DECISION_UNKNOWN = "unknown"

VALID_DECISIONS = [
    DECISION_READY,
    DECISION_NOT_READY,
    DECISION_NEEDS_INFO,
    DECISION_UNKNOWN,
]

# ===== Evaluation Keys =====
# Keys used in evaluation outputs

EVAL_KEY_FEATURE_IDENTIFICATION = "feature_identification"
EVAL_KEY_TOOL_USAGE = "tool_usage"
EVAL_KEY_DECISION_QUALITY = "decision_quality"

# Expected output keys from test scenarios
OUTPUT_KEY_EXPECTED_FEATURE_ID = "expected_feature_id"
OUTPUT_KEY_EXPECTED_DECISION = "expected_decision"
OUTPUT_KEY_SHOULD_IDENTIFY_FEATURE = "should_identify_feature"
OUTPUT_KEY_SHOULD_CALL_JIRA = "should_call_jira"
OUTPUT_KEY_SHOULD_CALL_ANALYSIS = "should_call_analysis"
OUTPUT_KEY_SHOULD_CITE_FAILURES = "should_cite_failures"
OUTPUT_KEY_SHOULD_CITE_TEST_METRICS = "should_cite_test_metrics"
OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED = "analysis_types_required"
OUTPUT_KEY_MUST_CHECK_BOTH_METRICS = "must_check_both_metrics"

# ===== Run Types =====
# LangSmith run types

RUN_TYPE_TOOL = "tool"
RUN_TYPE_CHAIN = "chain"
RUN_TYPE_LLM = "llm"
