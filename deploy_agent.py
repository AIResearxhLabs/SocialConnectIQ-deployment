#!/usr/bin/env python3
"""
SocialConnectIQ Deployment Agent - CLI Interface

This is the main entry point for the deployment agent. It provides
a command-line interface for deploying SocialConnectIQ to different
environments (local, staging, production).

Usage:
    python deploy_agent.py --env local
    python deploy_agent.py --env staging --dry-run
    python deploy_agent.py --env production --services api-gateway backend-service
"""

import os
import sys
import argparse
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich import box

from agents.orchestrator import DeploymentOrchestrator
from agents.state import DeploymentState


# Initialize Rich console for beautiful terminal output
console = Console()


def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()


def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    log_dir = os.getenv("LOG_DIRECTORY", "./logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create .gitkeep to track directory
    gitkeep_path = os.path.join(log_dir, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        open(gitkeep_path, 'a').close()


def write_deployment_log(state: DeploymentState):
    """Write deployment logs to file"""
    log_dir = os.getenv("LOG_DIRECTORY", "./logs")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f"deployment-{timestamp}.log")
    
    with open(log_file, 'w') as f:
        f.write(f"Deployment Log - {state['deployment_id']}\n")
        f.write(f"Environment: {state['environment']}\n")
        f.write(f"User: {state['user_email']} ({state['user_role']})\n")
        f.write(f"Status: {state['status']}\n")
        f.write(f"Duration: {state.get('duration_seconds', 0):.1f}s\n")
        f.write(f"\n{'='*80}\n")
        f.write(f"LOGS\n")
        f.write(f"{'='*80}\n\n")
        
        for log_entry in state['logs']:
            timestamp = log_entry.get('timestamp', '')
            level = log_entry.get('level', 'INFO')
            message = log_entry.get('message', '')
            step = log_entry.get('step', '')
            f.write(f"[{timestamp}] [{level:8}] [{step:12}] {message}\n")
        
        if state['errors']:
            f.write(f"\n{'='*80}\n")
            f.write(f"ERRORS\n")
            f.write(f"{'='*80}\n\n")
            for error in state['errors']:
                f.write(f"  • {error}\n")
        
        if state['warnings']:
            f.write(f"\n{'='*80}\n")
            f.write(f"WARNINGS\n")
            f.write(f"{'='*80}\n\n")
            for warning in state['warnings']:
                f.write(f"  • {warning}\n")
    
    return log_file


def display_banner():
    """Display application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║          SocialConnectIQ Deployment Agent            ║
    ║         AI-Powered Deployment Orchestration          ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def display_deployment_info(environment: str, user_email: str, dry_run: bool):
    """Display deployment configuration"""
    info_table = Table(show_header=False, box=box.ROUNDED)
    info_table.add_column("Key", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("🎯 Target Environment", environment.upper())
    info_table.add_row("👤 User", user_email)
    info_table.add_row("🏃 Mode", "DRY RUN (simulation only)" if dry_run else "LIVE DEPLOYMENT")
    info_table.add_row("⏰ Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    console.print(Panel(info_table, title="Deployment Configuration", border_style="cyan"))
    console.print()


def display_logs_realtime(state: DeploymentState):
    """Display deployment logs in real-time with formatting"""
    for log_entry in state['logs'][-5:]:  # Show last 5 log entries
        level = log_entry.get('level', 'INFO')
        message = log_entry.get('message', '')
        step = log_entry.get('step', '')
        
        # Color code by level
        if level == "ERROR":
            style = "bold red"
        elif level == "WARNING":
            style = "yellow"
        elif level == "INFO":
            style = "white"
        else:
            style = "dim"
        
        # Format message
        if message.startswith("✓"):
            style = "bold green"
        elif message.startswith("✗"):
            style = "bold red"
        
        console.print(f"  [{step:12}] {message}", style=style)


def display_preflight_results(preflight_data: dict):
    """Display pre-flight validation results"""
    from rich.table import Table
    from rich import box
    
    if not preflight_data:
        return
    
    console.print("\n")
    console.print("=" * 80)
    console.print("[bold cyan]Pre-Flight Validation Results[/bold cyan]")
    console.print("=" * 80)
    
    # Group checks by category
    checks = preflight_data.get("checks", [])
    categories = {}
    for check in checks:
        cat = check.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(check)
    
    # Display each category
    category_names = {
        "system": "System Checks",
        "config": "Configuration Checks",
        "dependency": "Dependency Checks",
        "permission": "Permission Checks",
        "environment": "Environment Checks"
    }
    
    for cat, name in category_names.items():
        if cat not in categories:
            continue
        
        table = Table(show_header=True, box=box.ROUNDED, title=name)
        table.add_column("Check", style="cyan", no_wrap=False, width=40)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Message", no_wrap=False)
        
        for check in categories[cat]:
            status = check.get("status", "UNKNOWN")
            check_name = check.get("name", "Unknown")
            message = check.get("message", "")
            
            # Style based on status
            if status == "PASS":
                status_text = "[green]✓ PASS[/green]"
            elif status == "FAIL":
                status_text = "[red]✗ FAIL[/red]"
            elif status == "WARN":
                status_text = "[yellow]⚠ WARN[/yellow]"
            else:
                status_text = f"[dim]{status}[/dim]"
            
            table.add_row(check_name, status_text, message)
        
        console.print(table)
        console.print()
    
    # Display summary
    summary = preflight_data.get("summary", "")
    passed = preflight_data.get("passed", False)
    can_proceed = preflight_data.get("can_proceed", False)
    
    if passed:
        console.print(f"[bold green]✅ {summary}[/bold green]")
    elif can_proceed:
        console.print(f"[bold yellow]⚠️  {summary}[/bold yellow]")
    else:
        console.print(f"[bold red]❌ {summary}[/bold red]")
    
    console.print("=" * 80)
    console.print()


def display_final_summary(state: DeploymentState, log_file: str):
    """Display final deployment summary"""
    console.print()
    
    # Status panel
    if state['status'] == 'completed':
        status_emoji = "✅"
        status_text = "DEPLOYMENT SUCCESSFUL"
        status_style = "bold green"
    else:
        status_emoji = "❌"
        status_text = "DEPLOYMENT FAILED"
        status_style = "bold red"
    
    console.print(Panel(
        f"{status_emoji} {status_text}",
        style=status_style,
        box=box.DOUBLE
    ))
    console.print()
    
    # Summary table
    summary_table = Table(show_header=False, box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")
    
    summary_table.add_row("Deployment ID", state['deployment_id'])
    summary_table.add_row("Environment", state['environment'])
    summary_table.add_row("Strategy", state.get('deployment_strategy', 'N/A'))
    summary_table.add_row("Duration", f"{state.get('duration_seconds', 0):.1f} seconds")
    summary_table.add_row("Status", state['status'].upper())
    
    if state['errors']:
        summary_table.add_row("Errors", str(len(state['errors'])))
    if state['warnings']:
        summary_table.add_row("Warnings", str(len(state['warnings'])))
    
    summary_table.add_row("Log File", log_file)
    
    console.print(Panel(summary_table, title="Deployment Summary", border_style="cyan"))
    
    # Display errors if any
    if state['errors']:
        console.print()
        console.print(Panel(
            "\n".join([f"  • {error}" for error in state['errors']]),
            title="Errors",
            border_style="red"
        ))
    
    # Display warnings if any
    if state['warnings']:
        console.print()
        console.print(Panel(
            "\n".join([f"  • {warning}" for warning in state['warnings']]),
            title="Warnings",
            border_style="yellow"
        ))


def main():
    """Main CLI entry point"""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="SocialConnectIQ Deployment Agent - AI-powered deployment orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to local Docker Desktop
  python deploy_agent.py --env local
  
  # Deploy to staging with dry run
  python deploy_agent.py --env staging --dry-run
  
  # Deploy specific services only
  python deploy_agent.py --env local --services api-gateway backend-service
  
  # Deploy without frontend
  python deploy_agent.py --env local --no-frontend
        """
    )
    
    parser.add_argument(
        "--env",
        type=str,
        choices=["local", "staging", "production"],
        default=os.getenv("DEFAULT_ENVIRONMENT", "local"),
        help="Target deployment environment"
    )
    
    parser.add_argument(
        "--services",
        type=str,
        nargs="+",
        default=None,
        help="Specific services to deploy (default: all)"
    )
    
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Skip frontend deployment"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate deployment without making actual changes"
    )
    
    parser.add_argument(
        "--user",
        type=str,
        default=None,
        help="User email (overrides DEPLOYMENT_USER env var)"
    )
    
    args = parser.parse_args()
    
    # Load environment
    load_environment()
    
    # Create logs directory
    create_logs_directory()
    
    # Get user email
    user_email = args.user or os.getenv("DEPLOYMENT_USER")
    if not user_email:
        console.print("[bold red]Error:[/bold red] DEPLOYMENT_USER environment variable not set")
        console.print("Set it with: export DEPLOYMENT_USER=your-email@company.com")
        sys.exit(1)
    
    # Display banner
    display_banner()
    
    # Display deployment info
    display_deployment_info(args.env, user_email, args.dry_run)
    
    try:
        # Initialize orchestrator
        console.print("🤖 Initializing deployment orchestrator...\n")
        orchestrator = DeploymentOrchestrator()
        
        # Execute deployment
        console.print("🚀 Starting deployment workflow...\n")
        
        final_state = orchestrator.deploy(
            environment=args.env,
            user_email=user_email,
            services=args.services,
            deploy_frontend=not args.no_frontend,
            dry_run=args.dry_run
        )
        
        # Display pre-flight validation results if available
        preflight_results = final_state.get("validation_results", {}).get("preflight")
        if preflight_results:
            display_preflight_results(preflight_results)
        
        console.print()
        
        # Write logs to file
        log_file = write_deployment_log(final_state)
        
        # Display summary
        display_final_summary(final_state, log_file)
        
        # Exit with appropriate code
        sys.exit(0 if final_state['status'] == 'completed' else 1)
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Deployment interrupted by user[/yellow]")
        sys.exit(130)
    
    except Exception as e:
        console.print(f"\n\n[bold red]❌ Fatal error:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()