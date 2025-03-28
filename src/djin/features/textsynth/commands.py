"""
Command handlers for report generation.
"""

from rich.console import Console
from rich.panel import Panel

from djin.cli.commands import register_command
from djin.features.textsynth.agent import ReportAgent

# Create console for rich output
console = Console()
# Create report agent
report_agent = ReportAgent()


def daily_report_command(args):
    """Generate a daily report of tasks."""
    try:
        # Generate daily report
        report = report_agent.generate_daily_report()

        # Display report
        console.print(Panel(report, title="Daily Report", border_style="green"))

        return True
    except Exception as e:
        console.print(f"[red]Error generating daily report: {str(e)}[/red]")
        return False


def weekly_report_command(args):
    """Generate a weekly report of tasks."""
    try:
        # Generate weekly report
        report = report_agent.generate_weekly_report()

        # Display report
        console.print(Panel(report, title="Weekly Report", border_style="green"))

        return True
    except Exception as e:
        console.print(f"[red]Error generating weekly report: {str(e)}[/red]")
        return False


def custom_report_command(args):
    """Generate a custom report of tasks."""
    try:
        # Default to 7 days if no argument provided
        days = 7

        # Parse days argument if provided
        if args and args[0].isdigit():
            days = int(args[0])

        # Generate custom report
        report = report_agent.generate_custom_report(days=days)

        # Display report
        console.print(Panel(report, title=f"Custom Report (Last {days} Days)", border_style="green"))

        return True
    except Exception as e:
        console.print(f"[red]Error generating custom report: {str(e)}[/red]")
        return False


# Register report commands
register_command(
    "report daily",
    daily_report_command,
    "Generate a daily report of your tasks",
)

register_command(
    "report weekly",
    weekly_report_command,
    "Generate a weekly report of your tasks",
)

register_command(
    "report custom",
    custom_report_command,
    "Generate a custom report of your tasks. Optional: specify number of days to look back (default: 7)",
)
