import click
import json
import sys
from acme_devops_cli.commands.deployment_status import get_deployment_status, print_table as print_deployments_table
from acme_devops_cli.commands.recent_releases import list_recent_releases, print_table as print_releases_table
from acme_devops_cli.commands.environment_health import check_environment_health, print_table as print_health_table
from acme_devops_cli.commands.promote_release import promote_release

@click.group()
@click.version_option(version="1.0.0")
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, format, verbose):
    """DevOps CLI Tool for infrastructure management."""
    ctx.ensure_object(dict)
    ctx.obj['format'] = format
    ctx.obj['verbose'] = verbose

@cli.command()
@click.option('--app', help='Filter by application ID')
@click.option('--env', help='Filter by environment')
@click.pass_context
def status(ctx, app, env):
    """Get deployment status for applications."""
    result = get_deployment_status(app, env)
    if ctx.obj['format'] == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        print_deployments_table(result)
    sys.exit(0 if result['status'] == 'success' else 1)

@cli.command()
@click.option('--limit', type=int, default=10, help='Limit number of results')
@click.option('--app', help='Filter by application ID')
@click.pass_context
def releases(ctx, limit, app):
    """List recent releases."""
    result = list_recent_releases(limit, app)
    if ctx.obj['format'] == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        print_releases_table(result)
    sys.exit(0 if result['status'] == 'success' else 1)

@cli.command()
@click.option('--env', help='Filter by environment')
@click.option('--app', help='Filter by application ID')
@click.pass_context
def health(ctx, env, app):
    """Check environment health status."""
    result = check_environment_health(env, app)
    if ctx.obj['format'] == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        print_health_table(result)
    sys.exit(0 if result['status'] == 'success' else 1)

@cli.command()
@click.option('--release', required=True, help='Release version to promote')
@click.option('--from', 'from_env', required=True, help='Source environment')
@click.option('--to', 'to_env', required=True, help='Target environment')
@click.option('--app', help='Application ID')
@click.pass_context
def promote(ctx, release, from_env, to_env, app):
    """Promote a release between environments."""
    result = promote_release(
        applicationId=app,
        version=release,
        fromEnvironment=from_env,
        toEnvironment=to_env
    )
    click.echo(json.dumps(result, indent=2))
    sys.exit(0 if result['status'] == 'success' else 1)

def main():
    cli(obj={})

if __name__ == "__main__":
    main()
