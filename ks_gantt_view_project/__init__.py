# -*- coding: utf-8 -*-

from . import models
from . import controllers
from . import wizard


def uninstall_hook(env):
    xml_ids = [
        'project.open_view_project_all',
        'project.act_project_project_2_project_task_all',
        'project.open_view_project_all_group_stage',
        'project.action_view_my_task',
        'project.action_view_all_task',
    ]

    for xml_id in xml_ids:
        act_window = env.ref(xml_id, raise_if_not_found=False)
        if act_window and act_window.view_mode:
            modes = act_window.view_mode.split(',')
            if 'ks_gantt' in modes:
                modes.remove('ks_gantt')
                act_window.view_mode = ','.join(modes)
