import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from multiprocessing import allow_connection_pickling
from typing import TypedDict

from rich.live import Live
from rich.panel import Panel

from db_config import db
from env import (
    EMAIL,
    HARVEST_ACCOUNT_ID,
    HARVEST_TOKEN,
    PROJECT_ID,
    TASK_ID,
)
from errors import UserInfoError
from model import HarvestClient, HarvestMeta, HarvestProject, HarvestTask, User
from utils import get_task_length_in_mins


class RemoteHarvestTask(TypedDict):
    spent_date: str
    started_time: str
    ended_time: str
    hours: str
    notes: str
    project_id: str
    task_id: str


HARVEST_HEADERS = {
    "User-Agent": f"MyIntegration ({EMAIL})",
    "Authorization": "Bearer " + str(HARVEST_TOKEN),
    "Harvest-Account-Id": str(HARVEST_ACCOUNT_ID),
}


def get_user_id() -> str:
    user = User.select().limit(1)
    if user:
        return user[0].id
    else:
        print("User ID not cached, getting it from Harvest API..")
        url = "https://api.harvestapp.com/v2/users/me"
        request = urllib.request.Request(url=url, headers=HARVEST_HEADERS)
        with urllib.request.urlopen(request, timeout=5) as response:
            responseCode = response.getcode()
            if responseCode != 200:
                raise UserInfoError("Request to Harvest failed.")

            responseBody = response.read().decode("utf-8")
            jsonResponse = json.loads(responseBody)
            userID = jsonResponse["id"]
            print(f"User ID is {userID}.")
            User.create(id=userID)
            return userID


def pull_weekly_harvest_hours(KW=None):
    user_id = get_user_id()
    if KW:
        today = datetime.fromisocalendar(datetime.now().year, KW, 2)
    else:
        today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    friday = today + timedelta(days=(4 - today.weekday()))
    fromDate = monday.strftime("%Y%m%d")
    toDate = friday.strftime("%Y%m%d")
    url = f"https://api.harvestapp.com/v2/reports/time/team?from={fromDate}&to={toDate}"
    jsonResponse = json.loads(api_to_json(url))
    if not jsonResponse["results"] or user_id not in [
        str(x["user_id"]) for x in jsonResponse["results"]
    ]:
        hours = 0.0
    else:
        hours = next(
            x for x in jsonResponse["results"] if user_id in str(x["user_id"])
        )["total_hours"]
    HarvestMeta.delete().execute()
    HarvestMeta.create(hours=hours)


def api_to_json(url: str):
    assert all(var is not None for var in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN)), (
        "Environment variable for Harvest upload is missing."
    )
    request = urllib.request.Request(url=url, headers=HARVEST_HEADERS)
    with urllib.request.urlopen(request, timeout=5) as response:
        responseCode = response.getcode()
        if responseCode != 200:
            raise UserInfoError("Request to Harvest failed.")

        responseBody = response.read().decode("utf-8")
        return responseBody


def pull_projects_clients_tasks():
    projectAssignmentAPIResponse = json.loads(
        api_to_json("https://api.harvestapp.com/v2/users/me/project_assignments")
    )
    projectBudgetAPIResponse = json.loads(
        api_to_json("https://api.harvestapp.com/v2/reports/project_budget")
    )["results"]
    projects_budgets = {
        str(result["project_id"]): result for result in projectBudgetAPIResponse
    }

    for projectAssignment in projectAssignmentAPIResponse["project_assignments"]:
        clientId = str(projectAssignment["client"]["id"])
        clientName = str(projectAssignment["client"]["name"])
        client, _ = HarvestClient.get_or_create(clientId=clientId, name=clientName)

        projectId = str(projectAssignment["project"]["id"])
        projectName = str(projectAssignment["project"]["name"])
        projectHourly = float(projectAssignment["hourly_rate"])

        remote_project = projects_budgets.get(str(projectId))
        budget = remote_project["budget"] if remote_project else None
        budget_remaining = (
            remote_project["budget_remaining"] if remote_project else None
        )
        budget_spent = remote_project["budget_spent"] if remote_project else None
        project, _ = HarvestProject.get_or_create(
            projectId=projectId,
            defaults={
                "client": client,
                "name": projectName,
                "hourly_rate": projectHourly,
                "budget": budget,
                "budget_spent": budget_spent,
                "budget_remaining": budget_remaining,
            },
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
            raise UserInfoError(
                f"Request failed: Couldn't push task {data['notes']} to Harvest."
            )


def push_task(task):
    assert all(var is not None for var in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN)), (
        "Environment variable for Harvest upload is missing."
    )
    time_spent = get_task_length_in_mins(task) / 60
    assert time_spent >= 0, "Spent time shouldn't be negative."
    if time_spent == 0:
        return

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
        "started_time": task.start_time.strftime("%H:%M"),
        "ended_time": task.end_time.strftime("%H:%M"),
        "hours": hours,
        "notes": notes,
        "project_id": project_id,
        "task_id": task_id,
    }
    push_harvest_task(data)


def pull():
    with Live(Panel("Pulling weekly hours...", expand=False)) as live:
        pull_weekly_harvest_hours()

        for table in [HarvestProject, HarvestTask, HarvestClient]:
            table.drop_table()
            table.create_table()
        live.update(Panel("Pulling projects + clients...", expand=False))
        pull_projects_clients_tasks()
        live.update(Panel("Updated local db + weekly hours.", expand=False))
