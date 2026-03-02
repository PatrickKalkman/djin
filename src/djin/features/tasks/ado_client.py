"""
ABOUTME: Azure DevOps REST API client for fetching work items.
ABOUTME: Uses WIQL queries and PAT authentication to retrieve tasks worked on for a given date.
"""

import os
from typing import Any, Dict, List

import requests
from loguru import logger

from djin.common.errors import AzureDevOpsError


def _get_ado_headers() -> Dict[str, str]:
    """Build HTTP headers with PAT-based Basic auth."""
    pat = os.environ.get("ADO_PAT")
    if not pat:
        raise AzureDevOpsError("ADO_PAT environment variable is not set.")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Basic {_encode_pat(pat)}",
    }


def _encode_pat(pat: str) -> str:
    """Encode PAT for Basic auth (username is empty, password is the PAT)."""
    import base64

    token = base64.b64encode(f":{pat}".encode()).decode()
    return token


def _next_day(date_str: str) -> str:
    """Return the date string for the day after date_str."""
    from datetime import datetime, timedelta

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return (dt + timedelta(days=1)).strftime("%Y-%m-%d")


def get_worked_on_items(org: str, project: str, date_str: str) -> List[Dict[str, Any]]:
    """
    Fetch work items assigned to the authenticated user that were active on the given date.

    Args:
        org: Azure DevOps organization name.
        project: Azure DevOps project name.
        date_str: Date in YYYY-MM-DD format.

    Returns:
        List of normalized task dicts with keys: key, summary, status, type, priority,
        assignee, worklog_seconds.

    Raises:
        AzureDevOpsError: If the API call fails.
    """
    headers = _get_ado_headers()
    base_url = f"https://dev.azure.com/{org}/{project}"

    # WIQL query: items assigned to me, changed on target date, not in "New" state
    wiql_query = (
        "SELECT [System.Id] FROM WorkItems "
        "WHERE [System.AssignedTo] = @Me "
        f"AND [System.ChangedDate] >= '{date_str}' "
        f"AND [System.ChangedDate] < '{_next_day(date_str)}' "
        "AND [System.State] <> 'New' "
        "ORDER BY [System.ChangedDate] DESC"
    )

    logger.info(f"Executing WIQL query against {org}/{project} for date {date_str}")
    logger.debug(f"WIQL: {wiql_query}")

    wiql_url = f"{base_url}/_apis/wit/wiql?api-version=7.1"
    wiql_response = requests.post(
        wiql_url,
        headers=headers,
        json={"query": wiql_query},
        timeout=30,
    )
    if not wiql_response.ok:
        body = wiql_response.text
        logger.error(f"WIQL query failed ({wiql_response.status_code}): {body}")
        raise AzureDevOpsError(f"WIQL query failed ({wiql_response.status_code}): {body}")

    work_item_refs = wiql_response.json().get("workItems", [])
    if not work_item_refs:
        logger.info(f"No work items found for {date_str}")
        return []

    ids = [str(ref["id"]) for ref in work_item_refs]
    logger.info(f"Found {len(ids)} work item IDs, fetching details")

    # Fetch full details via batch endpoint
    batch_url = (
        f"https://dev.azure.com/{org}/_apis/wit/workitemsbatch?api-version=7.1"
    )
    batch_response = requests.post(
        batch_url,
        headers=headers,
        json={
            "ids": [int(i) for i in ids],
            "fields": [
                "System.Id",
                "System.Title",
                "System.State",
                "System.WorkItemType",
                "Microsoft.VSTS.Common.Priority",
                "System.AssignedTo",
            ],
        },
        timeout=30,
    )
    if not batch_response.ok:
        body = batch_response.text
        logger.error(f"Batch fetch failed ({batch_response.status_code}): {body}")
        raise AzureDevOpsError(f"Batch work item fetch failed ({batch_response.status_code}): {body}")

    raw_items = batch_response.json().get("value", [])
    logger.info(f"Fetched details for {len(raw_items)} work items")

    return [_normalize_work_item(item) for item in raw_items]


def _normalize_work_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert an ADO work item response into the normalized task dict format."""
    fields = item.get("fields", {})
    item_id = item.get("id", fields.get("System.Id", 0))
    assigned_to = fields.get("System.AssignedTo", {})

    return {
        "key": f"DA-{item_id}",
        "summary": fields.get("System.Title", ""),
        "status": fields.get("System.State", ""),
        "type": fields.get("System.WorkItemType", ""),
        "priority": str(fields.get("Microsoft.VSTS.Common.Priority", "")),
        "assignee": assigned_to.get("displayName", "") if isinstance(assigned_to, dict) else str(assigned_to),
        "worklog_seconds": 0,
    }
