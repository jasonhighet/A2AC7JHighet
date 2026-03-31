#!/usr/bin/env python
"""CLI interface for the Investigator Agent.

This module provides a simple REPL (Read-Eval-Print Loop) interface for
interacting with the Investigator Agent via command line.

It also supports evaluation modes:
- `python cli.py --create-dataset`: Create evaluation dataset in LangSmith
- `python cli.py --eval`: Run evaluation on the dataset
"""

import argparse
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage
from pydantic import ValidationError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.graph import create_agent_graph
from src.agent.prompts import get_system_prompt
from src.evaluation.runner import run_evaluation, print_evaluation_summary
from src.evaluation.scenarios import create_evaluation_dataset, get_scenario_summary
from src.observability.callbacks import OpenTelemetryCallbackHandler
from src.observability.tracer import (
    force_flush_traces,
    initialize_tracing,
    shutdown_tracing,
)
from src.utils.config import load_config
from src.utils.conversation_persistence import ConversationPersistence


def print_welcome():
    """Print welcome message and usage instructions."""
    print("\n" + "=" * 60)
    print("Investigator Agent CLI")
    print("=" * 60)
    print("\nType your questions and press Enter to submit.")
    print("Type 'exit' or 'quit' to quit.\n")


def print_error(message: str):
    """Print error message with formatting.

    Args:
        message: Error message to display
    """
    print(f"\n❌ Error: {message}\n")


def print_agent_response(response: str):
    """Print agent response with formatting.

    Args:
        response: Agent's response text
    """
    print(f"\nAgent: {response}\n")


def main():
    """Main CLI loop for the Investigator Agent."""
    print_welcome()

    # Load configuration
    try:
        config = load_config()
        config.ensure_trace_directory_exists()
    except ValidationError as e:
        print_error("Configuration validation failed:")
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            print(f"  • {field}: {error['msg']}")
        print(
            "\nPlease check your .env file or environment variables.\n"
            "See .env.example for required configuration."
        )
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Initialize conversation persistence first to get conversation_id
    conversations_dir = Path("data/conversations")
    persistence = ConversationPersistence(
        conversations_dir, config, get_system_prompt()
    )

    # Use conversation_id from persistence for tracing
    conversation_id = persistence.conversation_id

    # Initialize OpenTelemetry tracing with conversation_id
    try:
        tracer = initialize_tracing(
            output_dir=str(config.trace_output_dir),
            service_name="investigator-agent",
            conversation_id=conversation_id,
        )
        print(f"✓ Tracing initialized for conversation: {conversation_id}")
        print(f"✓ Traces will be saved to: {config.trace_output_dir}\n")
    except Exception as e:
        print_error(f"Failed to initialize tracing: {e}")
        sys.exit(1)

    # Initialize the agent graph
    try:
        graph = create_agent_graph(config)
    except Exception as e:
        print_error(f"Failed to initialize agent: {e}")
        shutdown_tracing()
        sys.exit(1)

    # Initialize conversation state
    # LangGraph will maintain state via the messages list
    state = {"messages": []}

    print("✓ Agent initialized successfully")
    print(f"✓ Conversation will be saved to: {persistence.get_filepath()}\n")

    # Create OpenTelemetry callback handler for tracing (using short conversation_id)
    # Extract short ID from conversation_id (e.g., "conv_20251116_223821_f1ad4" -> "conv_f1ad4")
    short_conv_id = (
        f"conv_{conversation_id.split('_')[-1]}"
        if "_" in conversation_id
        else conversation_id
    )
    otel_callback = OpenTelemetryCallbackHandler(
        tracer=tracer, conversation_id=short_conv_id
    )

    # Main conversation loop
    try:
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "q"]:
                    print(f"\nConversation saved to: {persistence.get_filepath()}")
                    print("Goodbye!\n")
                    break

                # Skip empty input
                if not user_input:
                    continue

                # Add user message to state
                user_message = HumanMessage(content=user_input)

                # Invoke the agent graph with the updated state and tracing callbacks
                # The graph will return updated state with agent's response
                result = graph.invoke(
                    {"messages": state["messages"] + [user_message]},
                    config={"callbacks": [otel_callback]},
                )

                # Update state with the result
                state = result

                # Save conversation to disk after each turn
                persistence.save(state["messages"])

                # Extract and display the agent's response
                # The last message should be the agent's response
                if result["messages"]:
                    last_message = result["messages"][-1]
                    print_agent_response(last_message.content)

            except KeyboardInterrupt:
                print(f"\n\nConversation saved to: {persistence.get_filepath()}")
                print("Goodbye!\n")
                break
            except Exception as e:
                print_error(f"An error occurred: {e}")
                # Continue the loop instead of exiting
                continue
    finally:
        # Ensure traces are flushed before exiting
        force_flush_traces()
        shutdown_tracing()


def run_create_dataset_mode():
    """Create evaluation dataset in LangSmith."""
    try:
        # Show summary first
        summary = get_scenario_summary()
        print(f"\n{'=' * 60}")
        print("TEST SCENARIO SUMMARY")
        print(f"{'=' * 60}\n")
        print(f"Total Scenarios: {summary['total']}\n")
        print("By Category:")
        for cat, count in summary["by_category"].items():
            print(f"  - {cat}: {count}")
        print("\nBy Difficulty:")
        for diff, count in summary["by_difficulty"].items():
            print(f"  - {diff}: {count}")
        print(f"\n{'=' * 60}\n")

        # Create dataset
        dataset_name = create_evaluation_dataset()
        print(f"\n✅ Success! Dataset '{dataset_name}' created in LangSmith")
        print("   View at: https://smith.langchain.com/\n")

    except Exception as e:
        print_error(f"Failed to create dataset: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def run_evaluation_mode():
    """Run evaluation on the dataset."""
    try:
        results = run_evaluation()
        print_evaluation_summary(results)
    except Exception as e:
        print_error(f"Failed to run evaluation: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Investigator Agent CLI - Assess feature readiness"
    )

    parser.add_argument(
        "--eval",
        action="store_true",
        help="Run evaluation mode (evaluates agent on test dataset)",
    )

    parser.add_argument(
        "--create-dataset",
        action="store_true",
        help="Create/update evaluation dataset in LangSmith",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Handle special modes
    if args.create_dataset:
        run_create_dataset_mode()
        sys.exit(0)

    if args.eval:
        run_evaluation_mode()
        sys.exit(0)

    # Normal conversation mode
    main()
