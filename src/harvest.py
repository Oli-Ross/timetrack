import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import TypedDict

from env import EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN, PROJECT_ID, TASK_ID
from model import HarvestClient, HarvestMeta, HarvestProject, HarvestTask
from utils import get_task_length_in_mins


class RemoteHarvestTask(TypedDict):
    spent_date: str
    hours: str
    notes: str
    project_id: str
    task_id: str


HARVEST_HEADERS = {
    "User-Agent": f"MyIntegration ({EMAIL})",
    "Authorization": "Bearer " + str(HARVEST_TOKEN),
    "Harvest-Account-Id": str(HARVEST_ACCOUNT_ID),
}


def pull_weekly_harvest_hours(KW=None):
    assert all(var is not None for var in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN)), (
        "Environment variable for Harvest upload is missing."
    )
    if KW:
        today = datetime.fromisocalendar(datetime.now().year, KW, 2)
    else:
        today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    friday = today + timedelta(days=(4 - today.weekday()))
    fromDate = monday.strftime("%Y%m%d")
    toDate = friday.strftime("%Y%m%d")
    url = f"https://api.harvestapp.com/v2/reports/time/team?from={fromDate}&to={toDate}"
    request = urllib.request.Request(url=url, headers=HARVEST_HEADERS)
    with urllib.request.urlopen(request, timeout=5) as response:
        responseCode = response.getcode()
        if responseCode != 200:
            raise Exception("Request to Harvest failed.")

        responseBody = response.read().decode("utf-8")
        jsonResponse = json.loads(responseBody)

    if not jsonResponse["results"]:
        hours = 0.0
    else:
        hours = jsonResponse["results"][0]["total_hours"]
    HarvestMeta.delete().execute()
    HarvestMeta.create(hours=hours)


def pull_projects_clients_tasks():
    assert all(var is not None for var in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN)), (
        "Environment variable for Harvest upload is missing."
    )
    url = "https://api.harvestapp.com/v2/users/me/project_assignments"
    request = urllib.request.Request(url=url, headers=HARVEST_HEADERS)
    for table in [HarvestProject, HarvestTask, HarvestClient]:
        table.drop_table()
        table.create_table()
    with urllib.request.urlopen(request, timeout=5) as response:
        responseCode = response.getcode()
        if responseCode != 200:
            raise Exception("Request to Harvest failed.")

        responseBody = response.read().decode("utf-8")
        jsonResponse = json.loads(responseBody)

    for projectAssignment in jsonResponse["project_assignments"]:
        clientId = str(projectAssignment["client"]["id"])
        clientName = str(projectAssignment["client"]["name"])
        client, _ = HarvestClient.get_or_create(clientId=clientId, name=clientName)

        projectId = str(projectAssignment["project"]["id"])
        projectName = str(projectAssignment["project"]["name"])
        project, _ = HarvestProject.get_or_create(
            projectId=projectId, client=client, name=projectName
        )
        for taskAssignment in projectAssignment["task_assignments"]:
            taskId = str(taskAssignment["task"]["id"])
            taskName = str(taskAssignment["task"]["name"])
            HarvestTask.get_or_create(
                taskId=taskId,
                project=project,
                client=client,
                name=taskName,
            )


def push_harvest_task(data: RemoteHarvestTask):
    data_encoded = urllib.parse.urlencode(data).encode("ascii")
    url = "https://api.harvestapp.com/v2/time_entries"
    request = urllib.request.Request(
        url=url, headers=HARVEST_HEADERS, data=data_encoded
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        responseCode = response.getcode()
        if responseCode != 201:
            responseBody = response.read().decode("utf-8")
            jsonResponse = json.loads(responseBody)
            print(json.dumps(jsonResponse, sort_keys=True, indent=2))
            raise Exception(
                f"Request failed: Couldn't push task {task.uuid} to Harvest."
            )


def push_task(task):
    assert all(var is not None for var in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN)), (
        "Environment variable for Harvest upload is missing."
    )
    time_spent = get_task_length_in_mins(task) / 60
    assert time_spent > 0, "Spent time shouldn't be negative."

    spent_date = task.start_time.strftime("%Y-%m-%d")
    hours = f"{time_spent:.2f}"
    notes = task.name
    defaultUsed = False
    if task.taskId:
        task_id = task.taskId
    else:
        task_id = TASK_ID
        defaultUsed = True
    if task.projectId:
        project_id = task.projectId
    else:
        project_id = PROJECT_ID
        defaultUsed = True
    if defaultUsed:
        print(
            f'Task "{task.name}" with UUID {task.uuid} has missing task info + is pushed as default task.'
        )

    data: RemoteHarvestTask = {
        "spent_date": spent_date,
        "hours": hours,
        "notes": notes,
        "project_id": project_id,
        "task_id": task_id,
    }
    push_harvest_task(data)


def pull():
    pull_weekly_harvest_hours()
    pull_projects_clients_tasks()
    print("Updated local db + weekly hours.")
