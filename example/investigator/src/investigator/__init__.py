def main():
    """Entry point that delegates to the CLI module."""
    import runpy
    runpy.run_path("cli.py", run_name="__main__")
