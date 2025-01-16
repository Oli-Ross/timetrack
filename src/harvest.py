from datetime import datetime, timedelta
import json
import urllib.request
import urllib.parse

from utils import get_task_length_in_mins
from db_config import db
from model import HarvestClient, HarvestProject, HarvestTask, HarvestMeta
from env import EMAIL, HARVEST_TOKEN, HARVEST_ACCOUNT_ID, TASK_ID, PROJECT_ID


def sync_weekly_harvest_hours(KW=None):
    assert all(
        var is not None for var in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN)
    ), "Environment variable for Harvest upload is missing."
    with db:
        if KW:
            today = datetime.fromisocalendar(datetime.now().year, KW, 2)
        else:
            today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        friday = today + timedelta(days=(4 - today.weekday()))
        fromDate = monday.strftime("%Y%m%d")
        toDate = friday.strftime("%Y%m%d")
        url = f"https://api.harvestapp.com/v2/reports/time/team?from={fromDate}&to={toDate}"
        headers = {
            "User-Agent": f"MyIntegration ({EMAIL})",
            "Authorization": "Bearer " + str(HARVEST_TOKEN),
            "Harvest-Account-Id": str(HARVEST_ACCOUNT_ID),
        }

        request = urllib.request.Request(url=url, headers=headers)
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


def update_local_harvest_db():
    assert all(
        var is not None for var in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN)
    ), "Environment variable for Harvest upload is missing."
    url = "https://api.harvestapp.com/v2/users/me/project_assignments"
    headers = {
        "User-Agent": f"MyIntegration ({EMAIL})",
        "Authorization": "Bearer " + str(HARVEST_TOKEN),
        "Harvest-Account-Id": str(HARVEST_ACCOUNT_ID),
    }

    request = urllib.request.Request(url=url, headers=headers)
    with urllib.request.urlopen(request, timeout=5) as response:
        responseCode = response.getcode()
        if responseCode != 200:
            raise Exception("Request to Harvest failed.")

        responseBody = response.read().decode("utf-8")
        jsonResponse = json.loads(responseBody)

    with db:
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


def push_tasks(unloggedTasks):
    assert unloggedTasks
    assert all(
        var is not None for var in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN)
    ), "Environment variable for Harvest upload is missing."

    for task in unloggedTasks:
        time_spent = get_task_length_in_mins(task) / 60

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

        data = {
            "spent_date": spent_date,
            "hours": hours,
            "notes": notes,
            "project_id": project_id,
            "task_id": task_id,
        }
        data = urllib.parse.urlencode(data).encode("ascii")

        url = "https://api.harvestapp.com/v2/time_entries"
        headers = {
            "User-Agent": f"MyIntegration ({EMAIL})",
            "Authorization": "Bearer " + str(HARVEST_TOKEN),
            "Harvest-Account-Id": str(HARVEST_ACCOUNT_ID),
        }

        request = urllib.request.Request(url=url, headers=headers, data=data)
        with urllib.request.urlopen(request, timeout=5) as response:
            responseCode = response.getcode()
            if responseCode != 201:
                responseBody = response.read().decode("utf-8")
                jsonResponse = json.loads(responseBody)
                print(json.dumps(jsonResponse, sort_keys=True, indent=2))
                raise Exception(
                    f"Request failed: Couldn't push task {task.uuid} to Harvest."
                )


def sync():
    with db:
        sync_weekly_harvest_hours()
        update_local_harvest_db()
