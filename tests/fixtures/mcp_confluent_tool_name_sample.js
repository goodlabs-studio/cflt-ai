// Minimal hand-crafted excerpt of @confluentinc/mcp-confluent
// dist/confluent/tools/tool-name.js (shape circa v1.3.0).
//
// Purpose: offline parser/classifier fixture for
// tests/test_regenerate_tool_classification.py. Covers every D-05
// verb-prefix branch (list, read, get, search, detect, check, describe,
// query, create, update, alter, add, delete, remove) plus both explicit
// overrides (produce-message, consume-messages).
//
// DO NOT regenerate from npm. This file is intentionally static so unit
// tests stay deterministic and network-free.

export var ToolName;
(function (ToolName) {
    // read-only tier — verb prefixes
    ToolName["LIST_TOPICS"] = "list-topics";
    ToolName["READ_ENVIRONMENT"] = "read-environment";
    ToolName["GET_TOPIC_CONFIG"] = "get-topic-config";
    ToolName["SEARCH_TOPICS_BY_TAG"] = "search-topics-by-tag";
    ToolName["DETECT_FLINK_STATEMENT_ISSUES"] = "detect-flink-statement-issues";
    ToolName["CHECK_FLINK_STATEMENT_HEALTH"] = "check-flink-statement-health";
    ToolName["DESCRIBE_FLINK_TABLE"] = "describe-flink-table";
    ToolName["QUERY_METRICS"] = "query-metrics";
    // engineer tier — verb prefixes
    ToolName["CREATE_TOPICS"] = "create-topics";
    ToolName["UPDATE_TABLEFLOW_TOPIC"] = "update-tableflow-topic";
    ToolName["ALTER_TOPIC_CONFIG"] = "alter-topic-config";
    ToolName["ADD_TAGS_TO_TOPIC"] = "add-tags-to-topic";
    // break-glass tier — verb prefixes
    ToolName["DELETE_TOPICS"] = "delete-topics";
    ToolName["REMOVE_TAG_FROM_ENTITY"] = "remove-tag-from-entity";
    // break-glass tier — explicit overrides (verb-prefix would not match)
    ToolName["PRODUCE_MESSAGE"] = "produce-message";
    ToolName["CONSUME_MESSAGES"] = "consume-messages";
})(ToolName || (ToolName = {}));
