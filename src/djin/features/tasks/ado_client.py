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


def _execute_wiql(base_url: str, headers: Dict[str, str], wiql_query: str) -> List[int]:
    """Run a WIQL query and return the matching work item IDs."""
    wiql_url = f"{base_url}/_apis/wit/wiql?api-version=7.1"
    logger.debug(f"WIQL: {wiql_query}")
    response = requests.post(
        wiql_url,
        headers=headers,
        json={"query": wiql_query},
        timeout=30,
    )
    if not response.ok:
        body = response.text
        logger.error(f"WIQL query failed ({response.status_code}): {body}")
        raise AzureDevOpsError(f"WIQL query failed ({response.status_code}): {body}")

    return [ref["id"] for ref in response.json().get("workItems", [])]


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

    # Query A: items assigned to me, changed on target date, not in "New" state
    changed_query = (
        "SELECT [System.Id] FROM WorkItems "
        "WHERE [System.AssignedTo] = @Me "
        f"AND [System.ChangedDate] >= '{date_str}' "
        f"AND [System.ChangedDate] < '{_next_day(date_str)}' "
        "AND [System.State] <> 'New' "
        "AND [System.WorkItemType] <> 'Epic' "
        "ORDER BY [System.ChangedDate] DESC"
    )

    logger.info(f"Executing WIQL queries against {org}/{project} for date {date_str}")
    changed_ids = _execute_wiql(base_url, headers, changed_query)
    logger.info(f"Query A (changed on date): {len(changed_ids)} work items")

    # Query B: items that were in active states at end of target date (ASOF)
    asof_ids: List[int] = []
    try:
        asof_query = (
            "SELECT [System.Id] FROM WorkItems "
            "WHERE [System.AssignedTo] = @Me "
            "AND [System.State] IN ('In Progress', 'Committed', 'Active', 'Resolved', 'Approved', 'Doing') "
            "AND [System.WorkItemType] <> 'Epic' "
            f"ASOF '{date_str}T23:59:59Z'"
        )
        asof_ids = _execute_wiql(base_url, headers, asof_query)
        logger.info(f"Query B (active via ASOF): {len(asof_ids)} work items")
    except AzureDevOpsError:
        logger.warning("ASOF query failed, falling back to ChangedDate-only results")

    # Combine and deduplicate, preserving order (changed-on-date first)
    seen: set[int] = set()
    all_ids: List[int] = []
    for wid in changed_ids + asof_ids:
        if wid not in seen:
            seen.add(wid)
            all_ids.append(wid)

    if not all_ids:
        logger.info(f"No work items found for {date_str}")
        return []

    logger.info(f"Found {len(all_ids)} unique work item IDs, fetching details")

    # Fetch full details via batch endpoint
    batch_url = (
        f"https://dev.azure.com/{org}/_apis/wit/workitemsbatch?api-version=7.1"
    )
    batch_response = requests.post(
        batch_url,
        headers=headers,
        json={
            "ids": all_ids,
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
