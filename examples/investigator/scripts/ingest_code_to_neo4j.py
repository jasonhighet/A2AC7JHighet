#!/usr/bin/env python3
"""
Neo4j Code AST Ingestion Script for Feature Readiness Assessment Agent

This script parses code diffs using TreeSitter, extracts AST representations,
and stores them in Neo4j for graph-based code analysis.

The script:
1. Reads .diff files from the test data
2. Parses the added/modified code using TreeSitter
3. Extracts AST nodes (functions, classes, imports, etc.)
4. Stores AST structure in Neo4j with relationships

Usage:
    python ingest_code_to_neo4j.py [--features feature1,feature2] [--verbose]
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase

try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
    import tree_sitter_python
except ImportError:
    print("❌ Error: tree-sitter libraries not found")
    print("Install with: pip install tree-sitter tree-sitter-languages")
    exit(1)

# Get the project root directory
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
DATA_DIR = PROJECT_ROOT / "data" / "incoming"


class DiffParser:
    """Parses unified diff files to extract code changes."""

    def parse_diff(self, diff_content: str) -> List[Dict]:
        """
        Parse a unified diff file and extract added/modified code blocks.

        Returns list of dicts with:
        - file_path: The file being modified
        - language: Detected language (js, py, sql, etc.)
        - code: The added code content
        - start_line: Line number where code starts (in new file)
        """
        changes = []
        current_file = None
        current_code_lines = []
        current_line_number = 0

        lines = diff_content.split('\n')

        for line in lines:
            # Detect new file header
            if line.startswith('diff --git'):
                # Save previous file's changes
                if current_file and current_code_lines:
                    code = '\n'.join(current_code_lines)
                    language = self._detect_language(current_file)
                    changes.append({
                        'file_path': current_file,
                        'language': language,
                        'code': code,
                        'start_line': current_line_number
                    })
                    current_code_lines = []
                continue

            # Extract new file path
            if line.startswith('+++'):
                # Extract path after 'b/'
                match = re.match(r'\+\+\+ b/(.+)', line)
                if match:
                    current_file = match.group(1)
                continue

            # Track line numbers from hunk headers
            if line.startswith('@@'):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match:
                    current_line_number = int(match.group(1))
                continue

            # Collect added lines (start with '+' but not '+++')
            if line.startswith('+') and not line.startswith('+++'):
                code_line = line[1:]  # Remove the '+' prefix
                current_code_lines.append(code_line)
                current_line_number += 1
            elif not line.startswith('-'):
                # Context lines (no prefix) also increment line number
                current_line_number += 1

        # Don't forget the last file
        if current_file and current_code_lines:
            code = '\n'.join(current_code_lines)
            language = self._detect_language(current_file)
            changes.append({
                'file_path': current_file,
                'language': language,
                'code': code,
                'start_line': current_line_number
            })

        return changes

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()

        language_map = {
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.py': 'python',
            '.sql': 'sql',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
        }

        return language_map.get(ext, 'unknown')


class ASTExtractor:
    """Extracts AST nodes from source code using TreeSitter."""

    def __init__(self):
        # Initialize parsers for different languages
        self.parsers = {}
        self._setup_parsers()

    def _setup_parsers(self):
        """Set up TreeSitter parsers for supported languages."""
        try:
            # JavaScript/TypeScript parser
            js_language = Language(tree_sitter_javascript.language())
            js_parser = Parser(js_language)
            self.parsers['javascript'] = js_parser
            self.parsers['typescript'] = js_parser

            # Python parser
            py_language = Language(tree_sitter_python.language())
            py_parser = Parser(py_language)
            self.parsers['python'] = py_parser

        except Exception as e:
            print(f"⚠️  Warning: Could not initialize all parsers: {e}")

    def extract_ast(self, code: str, language: str) -> Optional[Dict]:
        """
        Parse code and extract AST structure.

        Returns dict with:
        - functions: List of function definitions
        - classes: List of class definitions
        - imports: List of import statements
        - calls: List of function calls
        - tree: Raw tree-sitter tree
        """
        parser = self.parsers.get(language)
        if not parser:
            return None

        try:
            tree = parser.parse(bytes(code, 'utf8'))
            root_node = tree.root_node

            ast_data = {
                'functions': self._extract_functions(root_node, language),
                'classes': self._extract_classes(root_node, language),
                'imports': self._extract_imports(root_node, language),
                'calls': self._extract_calls(root_node, language),
                'exports': self._extract_exports(root_node, language),
            }

            return ast_data
        except Exception as e:
            print(f"⚠️  Error parsing {language} code: {e}")
            return None

    def _extract_functions(self, node, language: str) -> List[Dict]:
        """Extract function definitions from AST."""
        functions = []

        # Node types vary by language
        function_types = {
            'javascript': ['function_declaration', 'arrow_function', 'function_expression',
                          'method_definition'],
            'python': ['function_definition'],
        }

        types_to_find = function_types.get(language, [])

        def traverse(n):
            if n.type in types_to_find:
                func_info = self._extract_function_info(n, language)
                if func_info:
                    functions.append(func_info)

            for child in n.children:
                traverse(child)

        traverse(node)
        return functions

    def _extract_function_info(self, node, language: str) -> Optional[Dict]:
        """Extract detailed information about a function node."""
        try:
            name = None
            params = []

            if language == 'javascript':
                # Find function name
                for child in node.children:
                    if child.type == 'identifier':
                        name = child.text.decode('utf8')
                        break
                    elif child.type == 'property_identifier':
                        name = child.text.decode('utf8')
                        break

                # Find parameters
                for child in node.children:
                    if child.type == 'formal_parameters':
                        for param_child in child.children:
                            if param_child.type in ['identifier', 'required_parameter',
                                                     'optional_parameter']:
                                params.append(param_child.text.decode('utf8'))

            elif language == 'python':
                # Python function structure
                for child in node.children:
                    if child.type == 'identifier':
                        name = child.text.decode('utf8')
                        break

                for child in node.children:
                    if child.type == 'parameters':
                        for param_child in child.children:
                            if param_child.type == 'identifier':
                                params.append(param_child.text.decode('utf8'))

            return {
                'name': name or 'anonymous',
                'parameters': params,
                'start_line': node.start_point[0],
                'end_line': node.end_point[0],
                'start_byte': node.start_byte,
                'end_byte': node.end_byte,
            }
        except Exception as e:
            return None

    def _extract_classes(self, node, language: str) -> List[Dict]:
        """Extract class definitions from AST."""
        classes = []

        class_types = {
            'javascript': ['class_declaration'],
            'python': ['class_definition'],
        }

        types_to_find = class_types.get(language, [])

        def traverse(n):
            if n.type in types_to_find:
                # Extract class name
                for child in n.children:
                    if child.type == 'identifier':
                        classes.append({
                            'name': child.text.decode('utf8'),
                            'start_line': n.start_point[0],
                            'end_line': n.end_point[0],
                        })
                        break

            for child in n.children:
                traverse(child)

        traverse(node)
        return classes

    def _extract_imports(self, node, language: str) -> List[Dict]:
        """Extract import statements from AST."""
        imports = []

        import_types = {
            'javascript': ['import_statement'],
            'python': ['import_statement', 'import_from_statement'],
        }

        types_to_find = import_types.get(language, [])

        def traverse(n):
            if n.type in types_to_find:
                imports.append({
                    'text': n.text.decode('utf8'),
                    'line': n.start_point[0],
                })

            for child in n.children:
                traverse(child)

        traverse(node)
        return imports

    def _extract_calls(self, node, language: str) -> List[Dict]:
        """Extract function/method calls from AST."""
        calls = []

        call_types = {
            'javascript': ['call_expression'],
            'python': ['call'],
        }

        types_to_find = call_types.get(language, [])

        def traverse(n):
            if n.type in types_to_find:
                # Try to extract function name
                for child in n.children:
                    if child.type in ['identifier', 'member_expression']:
                        calls.append({
                            'name': child.text.decode('utf8'),
                            'line': n.start_point[0],
                        })
                        break

            for child in n.children:
                traverse(child)

        traverse(node)
        return calls

    def _extract_exports(self, node, language: str) -> List[Dict]:
        """Extract export statements (for JavaScript/TypeScript)."""
        exports = []

        if language not in ['javascript', 'typescript']:
            return exports

        def traverse(n):
            if n.type == 'export_statement':
                exports.append({
                    'text': n.text.decode('utf8')[:100],  # Truncate long exports
                    'line': n.start_point[0],
                })

            for child in n.children:
                traverse(child)

        traverse(node)
        return exports


class Neo4jCodeIngester:
    """Handles ingestion of code AST into Neo4j graph database."""

    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER,
                 password: str = NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.diff_parser = DiffParser()
        self.ast_extractor = ASTExtractor()

        print(f"✓ Connected to Neo4j at: {uri}")

        # Create indexes and constraints
        self._setup_schema()

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()

    def _setup_schema(self):
        """Create indexes and constraints in Neo4j."""
        with self.driver.session() as session:
            # Create constraints for unique IDs
            constraints = [
                "CREATE CONSTRAINT commit_id IF NOT EXISTS FOR (c:Commit) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
                "CREATE CONSTRAINT function_id IF NOT EXISTS FOR (fn:Function) REQUIRE fn.id IS UNIQUE",
                "CREATE CONSTRAINT class_id IF NOT EXISTS FOR (cl:Class) REQUIRE cl.id IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception:
                    pass  # Constraint may already exist

            # Create indexes for common queries
            indexes = [
                "CREATE INDEX feature_id_idx IF NOT EXISTS FOR (c:Commit) ON (c.feature_id)",
                "CREATE INDEX file_language_idx IF NOT EXISTS FOR (f:File) ON (f.language)",
            ]

            for index in indexes:
                try:
                    session.run(index)
                except Exception:
                    pass

        print("✓ Neo4j schema initialized")

    def ingest_diff_file(self, diff_file_path: Path, feature_id: str,
                        feature_name: str) -> Dict[str, int]:
        """
        Ingest a single diff file into Neo4j.

        Returns statistics about what was ingested.
        """
        stats = {
            'files': 0,
            'functions': 0,
            'classes': 0,
            'imports': 0,
        }

        # Read diff file
        try:
            with open(diff_file_path, 'r', encoding='utf-8') as f:
                diff_content = f.read()
        except Exception as e:
            print(f"✗ Error reading {diff_file_path}: {e}")
            return stats

        # Parse diff to extract code changes
        changes = self.diff_parser.parse_diff(diff_content)

        if not changes:
            print(f"⊘ No code changes found in {diff_file_path.name}")
            return stats

        # Extract commit ID from filename
        commit_id = diff_file_path.stem  # e.g., "commit_001_initial_schema"

        # Create commit node
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Commit {id: $commit_id})
                SET c.feature_id = $feature_id,
                    c.feature_name = $feature_name,
                    c.file_path = $file_path,
                    c.ingested_at = datetime()
            """, {
                'commit_id': commit_id,
                'feature_id': feature_id,
                'feature_name': feature_name,
                'file_path': str(diff_file_path)
            })

        # Process each file change
        for change in changes:
            file_path = change['file_path']
            language = change['language']
            code = change['code']

            # Skip if language not supported
            if language not in ['javascript', 'python']:
                continue

            # Extract AST
            ast_data = self.ast_extractor.extract_ast(code, language)
            if not ast_data:
                continue

            stats['files'] += 1

            # Create file node
            with self.driver.session() as session:
                session.run("""
                    MERGE (f:File {path: $file_path})
                    SET f.language = $language,
                        f.feature_id = $feature_id

                    WITH f
                    MATCH (c:Commit {id: $commit_id})
                    MERGE (c)-[:MODIFIES]->(f)
                """, {
                    'file_path': file_path,
                    'language': language,
                    'feature_id': feature_id,
                    'commit_id': commit_id
                })

            # Create function nodes
            for func in ast_data['functions']:
                stats['functions'] += 1
                func_id = f"{commit_id}:{file_path}:{func['name']}:{func['start_line']}"

                with self.driver.session() as session:
                    session.run("""
                        MERGE (fn:Function {id: $func_id})
                        SET fn.name = $name,
                            fn.parameters = $params,
                            fn.start_line = $start_line,
                            fn.end_line = $end_line,
                            fn.feature_id = $feature_id

                        WITH fn
                        MATCH (f:File {path: $file_path})
                        MERGE (f)-[:CONTAINS_FUNCTION]->(fn)

                        WITH fn
                        MATCH (c:Commit {id: $commit_id})
                        MERGE (c)-[:ADDS_FUNCTION]->(fn)
                    """, {
                        'func_id': func_id,
                        'name': func['name'],
                        'params': func['parameters'],
                        'start_line': func['start_line'],
                        'end_line': func['end_line'],
                        'file_path': file_path,
                        'commit_id': commit_id,
                        'feature_id': feature_id
                    })

            # Create class nodes
            for cls in ast_data['classes']:
                stats['classes'] += 1
                class_id = f"{commit_id}:{file_path}:{cls['name']}:{cls['start_line']}"

                with self.driver.session() as session:
                    session.run("""
                        MERGE (cl:Class {id: $class_id})
                        SET cl.name = $name,
                            cl.start_line = $start_line,
                            cl.end_line = $end_line,
                            cl.feature_id = $feature_id

                        WITH cl
                        MATCH (f:File {path: $file_path})
                        MERGE (f)-[:CONTAINS_CLASS]->(cl)

                        WITH cl
                        MATCH (c:Commit {id: $commit_id})
                        MERGE (c)-[:ADDS_CLASS]->(cl)
                    """, {
                        'class_id': class_id,
                        'name': cls['name'],
                        'start_line': cls['start_line'],
                        'end_line': cls['end_line'],
                        'file_path': file_path,
                        'commit_id': commit_id,
                        'feature_id': feature_id
                    })

            # Store imports (simplified - just count them)
            stats['imports'] += len(ast_data['imports'])

        return stats

    def ingest_feature(self, feature_dir: Path, verbose: bool = False) -> Dict[str, int]:
        """Ingest all code diffs for a feature."""
        feature_id = feature_dir.name

        # Map feature IDs to names
        feature_map = {
            'feature1': 'Maintenance Scheduling & Alert System',
            'feature2': 'QR Code Check-in/out with Mobile App',
            'feature3': 'Advanced Resource Reservation System',
            'feature4': 'Contribution Tracking & Community Credits'
        }
        feature_name = feature_map.get(feature_id, feature_id)

        code_dir = feature_dir / 'code'
        if not code_dir.exists():
            print(f"⊘ No code directory found for {feature_id}")
            return {}

        # Find all .diff files
        diff_files = sorted(code_dir.glob('*.diff'))

        if not diff_files:
            print(f"⊘ No .diff files found in {code_dir}")
            return {}

        print(f"\n📂 Ingesting {feature_id} ({len(diff_files)} commits)")

        total_stats = {
            'commits': 0,
            'files': 0,
            'functions': 0,
            'classes': 0,
            'imports': 0,
        }

        for diff_file in diff_files:
            if verbose:
                print(f"  Processing: {diff_file.name}")

            stats = self.ingest_diff_file(diff_file, feature_id, feature_name)

            total_stats['commits'] += 1
            for key in ['files', 'functions', 'classes', 'imports']:
                total_stats[key] += stats.get(key, 0)

            if verbose:
                print(f"    ✓ {stats.get('functions', 0)} functions, "
                      f"{stats.get('classes', 0)} classes")

        return total_stats

    def reset_database(self):
        """Delete all nodes and relationships (use with caution!)."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✓ Database reset complete")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Ingest code diffs into Neo4j using TreeSitter AST parsing'
    )
    parser.add_argument(
        '--features',
        type=str,
        help='Comma-separated list of features to ingest (e.g., feature1,feature3)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset the database before ingesting'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🚀 Code AST Neo4j Ingestion")
    print("=" * 60)

    # Check Neo4j credentials
    if not NEO4J_PASSWORD or NEO4J_PASSWORD == "password":
        print("\n⚠️  Warning: Using default Neo4j password")
        print("Update NEO4J_PASSWORD in .env for production use")

    # Initialize ingester
    try:
        ingester = Neo4jCodeIngester()
    except Exception as e:
        print(f"\n❌ Error connecting to Neo4j: {e}")
        print("Make sure Neo4j is running on", NEO4J_URI)
        return

    try:
        # Handle reset
        if args.reset:
            print("\n⚠️  Resetting database...")
            ingester.reset_database()

        # Determine which features to process
        if args.features:
            feature_list = [f.strip() for f in args.features.split(',')]
        else:
            # Process all features
            feature_list = [d.name for d in DATA_DIR.iterdir()
                          if d.is_dir() and d.name.startswith('feature')]

        print(f"\n📥 Processing features: {', '.join(feature_list)}")

        # Ingest each feature
        all_stats = {
            'commits': 0,
            'files': 0,
            'functions': 0,
            'classes': 0,
            'imports': 0,
        }

        for feature in feature_list:
            feature_dir = DATA_DIR / feature
            if not feature_dir.exists():
                print(f"\n⚠️  Feature directory not found: {feature}")
                continue

            stats = ingester.ingest_feature(feature_dir, verbose=args.verbose)

            # Aggregate stats
            for key in all_stats:
                all_stats[key] += stats.get(key, 0)

        # Print results
        print("\n" + "=" * 60)
        print("✅ Ingestion Complete!")
        print("=" * 60)
        print(f"Commits processed: {all_stats['commits']}")
        print(f"Files analyzed: {all_stats['files']}")
        print(f"Functions extracted: {all_stats['functions']}")
        print(f"Classes extracted: {all_stats['classes']}")
        print(f"Imports found: {all_stats['imports']}")

        print("\n" + "=" * 60)
        print("✨ Neo4j graph is ready for queries!")
        print("=" * 60)
        print("\nExample Cypher queries:")
        print("  • MATCH (f:Function) RETURN f.name, f.feature_id LIMIT 10")
        print("  • MATCH (c:Commit)-[:ADDS_FUNCTION]->(f:Function) RETURN c, f LIMIT 20")
        print("  • MATCH (f:File)-[:CONTAINS_FUNCTION]->(fn:Function)")
        print("    WHERE f.language = 'javascript' RETURN f.path, count(fn)")

    finally:
        ingester.close()


if __name__ == "__main__":
    main()
