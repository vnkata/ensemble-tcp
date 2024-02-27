import pathlib
import csv
import json
import re
import text_sim
import pprint
from runner import TestResult, TestCaseStatus
import xml.dom.minidom


current_proj_dir = pathlib.Path(__file__).parent.parent


def extract_command_from_string(str):
  prefix = 'WebUI.'
  if str.startswith(prefix):
    return str[len(prefix):].rstrip() # remove the WebUI part and any trailing whitespaces
  return None


def read_commands_from_test_script(path):
  lines = []
  with open(path, 'r') as tscr_file:
    # read set of lines from the test script
    lines = tscr_file.readlines()

  commands = []
  for line in lines:
    command = extract_command_from_string(line)
    if command != None:
      commands.append(command)

  return commands


# this function gets the relative path of the script file
# to the Scripts folder and pads 'Test Cases' to the left
# of the path to construct the test case id
def extract_id_from_test_case_file(path):
  tscr_dir = str(current_proj_dir / 'SampleProject/Scripts')
  tscr_file_location = pathlib.PurePath(path).parent # parent is the folder with the actual test case name

  try:
    tscr_id = 'Test Cases/' + str(tscr_file_location.relative_to(tscr_dir))
    return tscr_id
  except ValueError:
    return None


def get_test_cases_scripts():
  tscr_dir = str(current_proj_dir / 'SampleProject/Scripts')
  tscr_pattern = '*.groovy'

  id_script_dict = {}
  for tscr_file in pathlib.Path(tscr_dir).rglob(tscr_pattern):
    abs_path = str(tscr_file.resolve())
    test_case_id = extract_id_from_test_case_file(abs_path)

    assert(test_case_id != None, 'Cannot extract TestCaseId from Test Case')

    id_script_dict[test_case_id] = abs_path

  return id_script_dict


def get_test_case_commands_from_json(path):
  SUITES = 'suites'
  TESTS = 'tests'
  FAIL = 'fail'
  SCRIPT = 'code'
  ERR = 'err'
  ERR_MSG = 'message'
  TITLE = 'title'

  id_commands_dict = {}
  test_results = TestResult()

  def get_fail_step(commands, err_obj):
    command_idx = 0 # the index of the current command
    max_sim = 0 # the current max similarity
    likely_fail_step = 0 # the step that likely failed
    for command in commands:
      if err_obj in command:
        return command_idx # found the obj
      else:
        sim_to_obj = text_sim.get_sim(command, err_obj)
        if sim_to_obj > max_sim:
          max_sim = sim_to_obj
          likely_fail_step = command_idx

      command_idx += 1

    return likely_fail_step

  def extract_err_obj(msg):
    match_obj = re.match(r"CypressError: Timed out retrying: Expected to find element: '(.*)', but never found it.", msg, re.M | re.I)
    if (match_obj):
      return match_obj.group(1)
    else:
      return msg

  def extract_commands(script):
    # removedComment = re.sub(r'(?m)^ *\/\/.*\n?', '', script)
    return script.split('\n')

  def process_test(test, test_id):
    id = test_id
    
    # avoid duplicate id
    while id in id_commands_dict:
      id += '_'

    is_fail = test[FAIL]
    script = test[SCRIPT]
    commands = extract_commands(script) # get commands by watching carriage return
    
    if is_fail:
      msg = test[ERR][ERR_MSG]
      err_obj = extract_err_obj(msg) # try my best to get the test object from error message
      fail_step = get_fail_step(commands, err_obj) # try my best to predict the fail step
      id_commands_dict[id] = commands[0:fail_step + 1]
      test_results.add_test_case_result(id, TestCaseStatus(True, commands[fail_step]))
    else:
      id_commands_dict[id] = commands
      test_results.add_test_case_result(id, TestCaseStatus(False, None))

  # receive list of tests
  def explore_tests(tests, parent_title):
    for test in tests:
      title = test[TITLE]
      process_test(test, parent_title + '/' + title)

  # receive list of suites
  def explore_suites(suites, parent_title):
    for suite in suites:
      title = suite[TITLE]
      explore_suites(suite[SUITES], parent_title + '/' + title)
      explore_tests(suite[TESTS], parent_title + '/' + title)

  with open(path, 'r', encoding="utf8") as json_file:
    data = json.load(json_file)
    explore_suites(data[SUITES][SUITES], '')

  return (id_commands_dict, test_results)

def get_test_case_commands_from_json_operationcode(path):
  RESULTS = 'results' 
  SUITES = 'suites'
  TESTS = 'tests'
  FAIL = 'fail'
  SCRIPT = 'code'
  ERR = 'err'
  ERR_MSG = 'message'
  TITLE = 'title'

  id_commands_dict = {}
  test_results = TestResult()

  def get_fail_step(commands, err_obj):
    command_idx = 0 # the index of the current command
    max_sim = 0 # the current max similarity
    likely_fail_step = 0 # the step that likely failed
    for command in commands:
      if err_obj in command:
        return command_idx # found the obj
      else:
        sim_to_obj = text_sim.get_sim(command, err_obj)
        if sim_to_obj > max_sim:
          max_sim = sim_to_obj
          likely_fail_step = command_idx

      command_idx += 1

    return likely_fail_step

  def extract_err_obj(msg):
    match_obj = re.match(r"CypressError: Timed out retrying: Expected to find element: '(.*)', but never found it.", msg, re.M | re.I)
    if (match_obj):
      return match_obj.group(1)
    else:
      return msg

  def extract_commands(script):
    removedComment = re.sub(r'(?m)^ *\/\/.*\n?', '', script)
    return script.split(';\n')

  def process_test(test, test_id):
    id = test_id
    
    # avoid duplicate id
    while id in id_commands_dict:
      id += '_'

    is_fail = test[FAIL]
    script = test[SCRIPT]
    commands = extract_commands(script) # get commands by watching carriage return
    
    if is_fail:
      msg = test[ERR][ERR_MSG]
      err_obj = extract_err_obj(msg) # try my best to get the test object from error message
      fail_step = get_fail_step(commands, err_obj) # try my best to predict the fail step
      id_commands_dict[id] = commands[0:fail_step + 1]
      test_results.add_test_case_result(id, TestCaseStatus(True, commands[fail_step]))
    else:
      id_commands_dict[id] = commands
      test_results.add_test_case_result(id, TestCaseStatus(False, None))

  # receive list of tests
  def explore_tests(tests, parent_title):
    for test in tests:
      title = test[TITLE]
      process_test(test, parent_title + '/' + title)

  # receive list of suites
  def explore_suites(suites, parent_title):
    for suite in suites:
      title = suite[TITLE]
      explore_suites(suite[SUITES], parent_title + '/' + title)
      explore_tests(suite[TESTS], parent_title + '/' + title)

  with open(path, 'r', encoding="utf8") as json_file:
    data = json.load(json_file)
    explore_suites(data[RESULTS], '')

  return (id_commands_dict, test_results)

def get_test_case_commands_from_json_VETS(path):
  RESULTS = 'results'
  SUITES = 'suites'
  TESTS = 'tests'
  FAIL = 'fail'
  SCRIPT = 'code'
  ERR = 'err'
  ERR_MSG = 'message'
  TITLE = 'title'

  id_commands_dict = {}
  test_results = TestResult()

  def get_fail_step(commands, err_obj):
    command_idx = 0  # the index of the current command
    max_sim = 0  # the current max similarity
    likely_fail_step = 0  # the step that likely failed
    for command in commands:
      if err_obj in command:
        return command_idx  # found the obj
      else:
        sim_to_obj = text_sim.get_sim(command, err_obj)
        if sim_to_obj > max_sim:
          max_sim = sim_to_obj
          likely_fail_step = command_idx

      command_idx += 1

    return likely_fail_step

  def extract_err_obj(msg):
    match_obj = re.match(r"CypressError: Timed out retrying: Expected to find element: '(.*)', but never found it.",
                         msg, re.M | re.I)
    if (match_obj):
      return match_obj.group(1)
    else:
      return msg

  def extract_commands(script):
    removedComment = re.sub(r'(?m)^ *\/\/.*\n?', '', script)
    return removedComment.split(';\n')

  def process_test(test, test_id):
    id = test_id

    # avoid duplicate id
    while id in id_commands_dict:
      id += '_'

    is_fail = test[FAIL]
    script = test[SCRIPT]
    commands = extract_commands(script)  # get commands by watching carriage return

    if is_fail:
      msg = test[ERR][ERR_MSG]
      err_obj = extract_err_obj(msg)  # try my best to get the test object from error message
      fail_step = get_fail_step(commands, err_obj)  # try my best to predict the fail step
      id_commands_dict[id] = commands[0:fail_step + 1]
      test_results.add_test_case_result(id, TestCaseStatus(True, commands[fail_step]))
    else:
      id_commands_dict[id] = commands
      test_results.add_test_case_result(id, TestCaseStatus(False, None))

  # receive list of tests
  def explore_tests(tests, parent_title):
    for test in tests:
      title = test[TITLE]
      process_test(test, parent_title + '/' + title)

  # receive list of suites
  def explore_suites(suites, parent_title):
    for suite in suites:
      title = suite[TITLE]
      explore_suites(suite[SUITES], parent_title + '/' + title)
      explore_tests(suite[TESTS], parent_title + '/' + title)

  with open(path, 'r', encoding="utf8") as json_file:
    data = json.load(json_file)
    explore_suites(data[RESULTS], '')

  return (id_commands_dict, test_results)

def get_test_case_commands_from_xml(path):
    doc = xml.dom.minidom.parse(path)
    all_test_cases = doc.getElementsByTagName('testcase')

    id_commands_dict = {}
    test_results = TestResult()

    for tc in all_test_cases:
        commands = []
        fail_step = None

        tc_id = tc.getAttribute('name')
        tc_status = tc.getAttribute('status')
        raw_commands = tc.getElementsByTagName('system-out')[0].firstChild.nodeValue
        lines = raw_commands.split('\n')
        did_fail = False

        for line in lines:
            if 'TEST_STEP' not in line:
                continue
            content = line.split(' - ')
            status, step = content[1], content[2]
            commands.append(step)

            if status[12:-1] == 'FAILED':
                did_fail = True
                fail_step = step

        id_commands_dict[tc_id] = commands
        test_results.add_test_case_result(
            tc_id, 
            TestCaseStatus(did_fail, fail_step)
        )

    return (id_commands_dict, test_results)


def get_test_case_commands_from_csv(path):
  name_col = 'Suite/Test/Step Name'
  status_col = 'Status'

  test_case_rows = {} # store the rows of test cases
  test_case_index = 0
  with open(path, 'r') as report_file:
    csv_reader = csv.DictReader(report_file)
    for row in csv_reader:
      if row[name_col] == '': # meet a ,,,,,,,
        test_case_index += 1
        continue

      if test_case_index in test_case_rows:
        test_case_rows[test_case_index].append(row)
      else:
        test_case_rows[test_case_index] = [row]

  id_commands_dict = {}
  test_results = TestResult()
  for index in range(1, test_case_index + 1): # start from 1 to ignore the test suite info
    rows = test_case_rows[index]
    test_case_id = rows[0][name_col]
    id_commands_dict[test_case_id] = []
    for row_index in range(1, len(rows)):
      command_name = rows[row_index][name_col]
      id_commands_dict[test_case_id].append(command_name)
    test_case_status = rows[0][status_col]
    if test_case_status == 'FAILED' or test_case_status == 'ERROR':
      test_results.add_test_case_result(test_case_id, TestCaseStatus(True, rows[len(rows) - 1][name_col]))
    else:
      test_results.add_test_case_result(test_case_id, TestCaseStatus(False, None))

  # id_commands_dict = mapping testCaseId <-> array commands
  # test_results.add_test_case_result(....) --> add testCaseId and TestCaseStatus(didFail, idOfTestStepThatFails)
  return (id_commands_dict, test_results)


def get_test_scripts_commands():
  test_case_scripts = get_test_cases_scripts()

  # return a dict with id as key and commands as value
  id_commands_dict = {}
  for test_id, test_script in test_case_scripts.items():
    commands = read_commands_from_test_script(test_script)
    id_commands_dict[test_id] = commands

  return id_commands_dict
