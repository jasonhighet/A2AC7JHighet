#!/usr/bin/env python3
"""
Neo4j Code Query Script

Simple script to explore and verify the ingested code AST data.
Demonstrates various useful queries for the agent system.

Usage:
    python query_neo4j_code.py [query_name]
"""

import os
import argparse
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class Neo4jCodeQuerier:
    """Query Neo4j for code AST information."""

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def run_query(self, query: str, parameters: dict = None):
        """Execute a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def print_results(self, results, title: str):
        """Pretty print query results."""
        print(f"\n{'=' * 60}")
        print(f"📊 {title}")
        print('=' * 60)

        if not results:
            print("No results found.")
            return

        for i, record in enumerate(results, 1):
            print(f"\n{i}. {record}")

        print(f"\n{'=' * 60}")
        print(f"Total: {len(results)} results")

    # ===== Predefined Queries =====

    def query_database_stats(self):
        """Get overall statistics about the database."""
        query = """
        MATCH (c:Commit) WITH count(c) as commits
        MATCH (f:File) WITH commits, count(f) as files
        MATCH (fn:Function) WITH commits, files, count(fn) as functions
        MATCH (cl:Class) WITH commits, files, functions, count(cl) as classes
        RETURN commits, files, functions, classes
        """
        results = self.run_query(query)
        self.print_results(results, "Database Statistics")

    def query_features_overview(self):
        """Get an overview of all features with their commit counts."""
        query = """
        MATCH (c:Commit)
        WITH c.feature_id as feature_id, c.feature_name as feature_name,
             count(c) as commit_count
        ORDER BY feature_id
        RETURN feature_id, feature_name, commit_count
        """
        results = self.run_query(query)
        self.print_results(results, "Features Overview")

    def query_functions_by_feature(self, feature_id: str = None):
        """List all functions, optionally filtered by feature."""
        if feature_id:
            query = """
            MATCH (fn:Function)
            WHERE fn.feature_id = $feature_id
            RETURN fn.name as name, fn.params as parameters,
                   fn.start_line as start_line, fn.feature_id as feature
            ORDER BY fn.name
            """
            params = {'feature_id': feature_id}
            title = f"Functions in {feature_id}"
        else:
            query = """
            MATCH (fn:Function)
            RETURN fn.name as name, fn.params as parameters,
                   fn.start_line as start_line, fn.feature_id as feature
            ORDER BY fn.feature_id, fn.name
            LIMIT 20
            """
            params = {}
            title = "All Functions (first 20)"

        results = self.run_query(query, params)
        self.print_results(results, title)

    def query_files_with_most_functions(self):
        """Find files with the most function definitions."""
        query = """
        MATCH (f:File)-[:CONTAINS_FUNCTION]->(fn:Function)
        WITH f.path as file, f.language as language, count(fn) as func_count
        ORDER BY func_count DESC
        LIMIT 10
        RETURN file, language, func_count
        """
        results = self.run_query(query)
        self.print_results(results, "Files with Most Functions")

    def query_commit_changes(self, commit_id: str = None):
        """Show what a commit modified."""
        if not commit_id:
            # Show first commit
            query = """
            MATCH (c:Commit)
            RETURN c.id as commit_id
            ORDER BY c.id
            LIMIT 1
            """
            result = self.run_query(query)
            if result:
                commit_id = result[0]['commit_id']
            else:
                print("No commits found")
                return

        query = """
        MATCH (c:Commit {id: $commit_id})
        OPTIONAL MATCH (c)-[:MODIFIES]->(f:File)
        OPTIONAL MATCH (c)-[:ADDS_FUNCTION]->(fn:Function)
        OPTIONAL MATCH (c)-[:ADDS_CLASS]->(cl:Class)
        RETURN c.id as commit,
               c.feature_name as feature,
               collect(DISTINCT f.path) as files,
               collect(DISTINCT fn.name) as functions,
               collect(DISTINCT cl.name) as classes
        """
        results = self.run_query(query, {'commit_id': commit_id})
        self.print_results(results, f"Commit Details: {commit_id}")

    def query_feature_complexity(self):
        """Analyze code complexity by feature."""
        query = """
        MATCH (c:Commit)-[:ADDS_FUNCTION]->(fn:Function)
        WITH c.feature_id as feature, count(fn) as total_functions,
             avg(size(fn.params)) as avg_params
        RETURN feature, total_functions, round(avg_params, 2) as avg_parameters
        ORDER BY total_functions DESC
        """
        results = self.run_query(query)
        self.print_results(results, "Feature Code Complexity")

    def query_files_by_language(self):
        """Count files by programming language."""
        query = """
        MATCH (f:File)
        WITH f.language as language, count(f) as file_count
        ORDER BY file_count DESC
        RETURN language, file_count
        """
        results = self.run_query(query)
        self.print_results(results, "Files by Language")

    def query_function_calls_potential(self):
        """Find functions that might be calling other functions (by name matching)."""
        query = """
        MATCH (fn1:Function), (fn2:Function)
        WHERE fn1.name CONTAINS fn2.name
          AND fn1.name <> fn2.name
          AND id(fn1) <> id(fn2)
        RETURN fn1.name as caller, fn2.name as potential_callee,
               fn1.feature_id as caller_feature, fn2.feature_id as callee_feature
        LIMIT 10
        """
        results = self.run_query(query)
        self.print_results(results, "Potential Function Calls")

    def query_cross_feature_analysis(self):
        """Analyze how features differ in implementation."""
        query = """
        MATCH (c:Commit)
        WITH c.feature_id as feature,
             count(DISTINCT c) as commits
        OPTIONAL MATCH (f:File {feature_id: feature})
        WITH feature, commits, count(DISTINCT f) as files
        OPTIONAL MATCH (fn:Function {feature_id: feature})
        WITH feature, commits, files, count(fn) as functions
        OPTIONAL MATCH (cl:Class {feature_id: feature})
        RETURN feature, commits, files, functions, count(cl) as classes
        ORDER BY feature
        """
        results = self.run_query(query)
        self.print_results(results, "Cross-Feature Analysis")


def main():
    parser = argparse.ArgumentParser(description='Query Neo4j code AST database')
    parser.add_argument(
        'query',
        nargs='?',
        default='stats',
        choices=['stats', 'features', 'functions', 'files', 'commits',
                'complexity', 'languages', 'calls', 'analysis', 'all'],
        help='Query to run'
    )
    parser.add_argument(
        '--feature',
        type=str,
        help='Filter by feature ID (e.g., feature1)'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🔍 Neo4j Code AST Query Tool")
    print("=" * 60)

    try:
        querier = Neo4jCodeQuerier()
    except Exception as e:
        print(f"\n❌ Error connecting to Neo4j: {e}")
        return

    try:
        if args.query == 'stats' or args.query == 'all':
            querier.query_database_stats()

        if args.query == 'features' or args.query == 'all':
            querier.query_features_overview()

        if args.query == 'functions' or args.query == 'all':
            querier.query_functions_by_feature(args.feature)

        if args.query == 'files' or args.query == 'all':
            querier.query_files_with_most_functions()

        if args.query == 'commits':
            querier.query_commit_changes()

        if args.query == 'complexity' or args.query == 'all':
            querier.query_feature_complexity()

        if args.query == 'languages' or args.query == 'all':
            querier.query_files_by_language()

        if args.query == 'calls':
            querier.query_function_calls_potential()

        if args.query == 'analysis' or args.query == 'all':
            querier.query_cross_feature_analysis()

        print("\n" + "=" * 60)
        print("✨ Query complete!")
        print("=" * 60)
        print("\nTry these queries:")
        print("  python query_neo4j_code.py stats")
        print("  python query_neo4j_code.py features")
        print("  python query_neo4j_code.py functions --feature feature1")
        print("  python query_neo4j_code.py all")

    finally:
        querier.close()


if __name__ == "__main__":
    main()
