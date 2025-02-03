from utils import fzf, get_short_uuid
from model import HarvestClient, HarvestProject, HarvestTask, Preset
from task_utils import start_task
import pretty_print


def add_preset():
    name = input("Name? ")
    clientId = fzf({x.clientId: x.name for x in HarvestClient.select()}, "Client?")
    client = HarvestClient.select().where(HarvestClient.clientId == clientId)[0]
    projectId = fzf({x.projectId: x.name for x in client.projects}, "Project?")
    project = HarvestProject.select().where(HarvestProject.projectId == projectId)[0]
    taskId = fzf({x.taskId: x.name for x in project.tasks}, "Task?")
    harvestTask = HarvestTask.select().where(HarvestTask.taskId == taskId)[0]
    uuid = get_short_uuid()
    Preset.create(
        **{"uuid": uuid, "name": name, "project": project, "task": harvestTask}
    )
    print(f'Created preset "{name}"')


def show_preset():
    presets = Preset.select()
    pretty_print.show_presets(presets)


def start_preset():
    presets = Preset.select()
    uuid = fzf(
        {preset.uuid: preset.name for preset in presets},
        prompt="Which preset to start?",
    )
    preset = Preset.select().where(Preset.uuid == uuid).limit(1)[0]
    start_task(
        preset.name, preset.task.taskId, preset.project.projectId, stopPrevious=True
    )
    print(f'Started task from preset "{preset.name}"')


def delete_preset():
    presets = Preset.select()
    uuid = fzf(
        {preset.uuid: preset.name for preset in presets},
        prompt="Which preset to delete?",
    )
    preset = Preset.select().where(Preset.uuid == uuid).limit(1)[0]
    name = preset.name
    preset.delete_instance()
    print(f'Deleted preset "{name}"')
