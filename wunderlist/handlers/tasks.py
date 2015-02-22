# encoding: utf-8

from wunderlist.util import workflow
from wunderlist.models.task_parser import TaskParser
from workflow.background import is_running
from datetime import date
from random import random

_calendar = u'📅'
_star = u'★'
_recurrence = u'↻'

def _task(args):
	return TaskParser(' '.join(args))

def filter(args):
	task = _task(args)
	subtitle = []
	wf = workflow()

	if task.starred:
		subtitle.append(_star)

	if task.due_date:
		today = date.today()
		if task.due_date == today:
			date_format = 'Today'
		if task.due_date.year == today.year:
			date_format = '%a, %b %d'
		else:
			date_format = '%b %d, %Y'

		subtitle.append('%s Due %s' % (_calendar, task.due_date.strftime(date_format)))

	if task.recurrence_type:
		subtitle.append(u'%s Every %d %s%s' % (_recurrence, task.recurrence_count, task.recurrence_type, 's' if task.recurrence_count != 1 else ''))

	subtitle.append(task.title or 'Begin typing to add a new task')

	if task.has_list_prompt:
		lists = wf.stored_data('lists')
		if lists:
			for list in lists:
				# Show some full list names and some concatenated in command
				# suggestions
				sample_command = list['title']
				if random() > 0.5:
					sample_command = sample_command[:int(len(sample_command) * .75)]
				wf.add_item(list['title'], 'Assign task to this list, e.g. %s: %s' % (sample_command.lower(), task.title), autocomplete=task.phrase_with(list_title=list['title']))
		elif is_running('sync'):
			wf.add_item('Your lists are being synchronized', 'Please try again in a few moments')
	
	# Task has an unfinished recurrence phrase
	elif task.has_recurrence_prompt:
		wf.add_item('Every month', 'Same day every month, e.g. every mo', uid="recurrence_1m", autocomplete=task.phrase_with(recurrence='every month'))
		wf.add_item('Every week', 'Same day every week, e.g. every week, every Tuesday', uid="recurrence_1w", autocomplete=task.phrase_with(recurrence='every week'))
		wf.add_item('Every year', 'Same date every year, e.g. every 1 y, every April 15', uid="recurrence_1y", autocomplete=task.phrase_with(recurrence='every year'))
		wf.add_item('Every 3 months', 'Same day every 3 months, e.g. every 3 months', uid="recurrence_3m", autocomplete=task.phrase_with(recurrence='every 3 months'))
		wf.add_item('Remove recurrence', autocomplete=task.phrase_with(recurrence=False))

	# Task has an unfinished due date phrase
	elif task.has_due_date_prompt:
		wf.add_item('Today', 'e.g. due today', autocomplete=task.phrase_with(due_date='due today'))
		wf.add_item('Tomorrow', 'e.g. due tomorrow', autocomplete=task.phrase_with(due_date='due tomorrow'))
		wf.add_item('Next Week', 'e.g. due next week', autocomplete=task.phrase_with(due_date='due next week'))
		wf.add_item('Next Month', 'e.g. due next month', autocomplete=task.phrase_with(due_date='due next month'))
		wf.add_item('Next Year', 'e.g. due next year, due April 15', autocomplete=task.phrase_with(due_date='due next year'))
		wf.add_item('Remove due date', autocomplete=task.phrase_with(due_date=False))

	# Main menu for tasks
	else:
		wf.add_item('Add Task to ' + task.list_title, '   '.join(subtitle), arg=task.phrase, valid=True)

		title = 'Change list' if task.list_title else 'Select a list'
		wf.add_item(title, 'Prefix the task, e.g. Automotive: ' + task.title, autocomplete=task.phrase_with(list_title=True))

		title = 'Change the due date' if task.due_date else 'Set a due date'
		wf.add_item(title, '"due" followed by any date-related phrase, e.g. due next Tuesday; due May 4', autocomplete=task.phrase_with(due_date=True))

		title = 'Change the recurrence' if task.recurrence_type else 'Make it a recurring task'
		wf.add_item(title, '"every" followed by a unit of time, e.g. every 2 months; every year; every 4w', autocomplete=task.phrase_with(recurrence=True))

		if task.starred:
			wf.add_item('Unstar', 'Remove * from the task', autocomplete=task.phrase_with(starred=False))
		else:
			wf.add_item('Star', 'End the task with * (asterisk)', autocomplete=task.phrase_with(starred=True))

def commit(args):
	from wunderlist.api import tasks
	task = _task(args)

	tasks.create_task(task.list_id, task.title, assignee_id=task.assignee_id, 
		recurrence_type=task.recurrence_type, recurrence_count=task.recurrence_count, 
		due_date=task.due_date, starred=task.starred, completed=task.completed
	)