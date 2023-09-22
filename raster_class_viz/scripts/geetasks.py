# -*- coding: utf-8 -*-
"""
Code to handle Google Earth Engine tasks.
"""
import time

from pathlib import Path
# from tenacity import retry, stop_after_attempt, wait_fixed

# from .timeout_decorator import timeout


# @retry(stop=stop_after_attempt(20), wait=wait_fixed(5))
# @timeout(60)
def gee_check_task_status(task):
    """Waits for GEE task to be COMPLETE before moving to the next step of the code.
    """
    task_status = task.status()['state']
    task_description = task.status()['description']
    print(f'\nStart:{task_description}')
    while task_status in ['READY', 'RUNNING']:
        print(f'\tStatus:{task_status}.')
        # time.sleep(60)
        time.sleep(10)
        try:
            task_status = task.status()['state']
        except Exception as e:
            print(e, f' \n task_status not working ')
    print(f'\tStatus:{task_status}.')
    print(f'End:{task_description}')
    return


def remove_0_in_queue(queue: list) -> list:
    """Drop 0s from task list.
    Note, we do not know how the 0s got into the task list.
    """
    clean_queue = []
    for task in queue:
        if task != 0:
            clean_queue.append(task)
    return clean_queue


# return [task for task in queue if task != 0]


def unnest_list_in_queue(queue: list) -> list:
    """If a task in the queue is a task, add the tasks to the queue.
    Else, if a task in the queue is a list of tasks, unnest the list
    and add the individual list item/tasks to the queue.
    """
    clean_queue = []
    for task in queue:
        if not isinstance(task, list):
            clean_queue.append(task)
        elif isinstance(task, list):
            for sub_task in task:
                clean_queue.append(sub_task)
    return clean_queue


def check_on_tasks_in_queue(queue: list) -> None:
    """Clean the tasks in queue, and then try/pop first task in queue.
    If not complete after threhold set here and # of retries, append as
    last item in queue.
    """
    queue = remove_0_in_queue(queue)
    queue = unnest_list_in_queue(queue)
    attempt_counter = {}
    while queue:
        print('queue', queue)
        print('attempt_counter', attempt_counter)
        print('len(queue)', len(queue))
        current_task = queue.pop(0)
        if attempt_for_task_gt_thr(attempt_counter, current_task, thr=30):
            # if a task has been checked on more than `thr` times
            # unsucessfully, bail
            print(current_task, queue)
            assert False
        print(4, type(current_task), current_task)
        try:
            gee_check_task_status(current_task)
            del attempt_counter[current_task]
        except Exception as e:
            queue.append(current_task)
            print('Got an exception. Appending task to the queue.', e)


def attempt_for_task_gt_thr(attempt_counter, task, thr=10) -> bool:
    if task in attempt_counter:
        if attempt_counter[task] > thr:
            return True
        attempt_counter[task] += 1
        return False
    attempt_counter[task] = 1
    return False


def get_gee_split_files(fp):
    """Looks for files whose path only differ from `fp` by having an additional suffix before the extension. These are
    likely the by-product of downloading a large file through GEE, which then saves the downloaded files with the same
    name appended with a suffix of the style 0000000000-0000000000.
    """
    fp = Path(fp)
    files = list(fp.parent.glob(fp.stem + '*-*' + fp.suffix))
    return files


def check_gee_split(fp):
    """Checks if GEE split the downloaded file `fp` in multiple segments. """
    fps = get_gee_split_files(fp)
    are_split = len(fps) > 0
    return are_split, fps


def wait_for_local_sync(path, sleep=10, maxnsleeps=12):
    path = Path(path)

    for i in range(maxnsleeps):  # wait for a max of 120 seconds
        print('in wait FOR loop')
        if not path.exists() and not check_gee_split(path)[0]:
            print(f'Waiting to sync {path} in local Google Drive...{i}')
            print(f'path.exists(): {path.exists()}')
            time.sleep(sleep)
        else:
            break
    return
