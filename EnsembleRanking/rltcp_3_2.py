import merger
import terminal_checker
import reward_converter
import math

from predictor import Predictor
from command_graph import CommandGraph
from test_case import TestCase
from edge import Edge

class RLTCP3_2:
    def __init__(
        self, graph_merge_discount, penalty_decay_rate,
        max_past_step, factor_reduction_amt, training_max_ite=200, number_of_epochs=1
    ):
        self.training_max_ite = training_max_ite
        self.graph_merge_discount = graph_merge_discount
        self.penalty_decay_rate = penalty_decay_rate
        self.max_past_step = max_past_step
        self.factor_reduction_amt = factor_reduction_amt
        self.number_of_epochs = number_of_epochs

    def __str__(self):
        discount = self.graph_merge_discount
        decay = self.penalty_decay_rate
        max_it = self.training_max_ite
        max_pst = self.max_past_step
        factor = self.factor_reduction_amt
        return 'rltcp3_2 {}_{}_{}_{}'.format(discount, decay, max_pst, factor)

    def prioritize_suites(self, suites):
        predictor = Predictor()
        old_command_graph = CommandGraph()
        iteration = 0
        result = {'test_cases': [], 'order': [], 'run_result': []}
        failed_step = set()
        passed_step = set()
        test_steps = set()

        all_results = [tr for _, tr, _ in suites]
        for suite, test_result, r_path in suites:

            # forget failed step by decay value
            if (int(math.ceil((1-self.penalty_decay_rate)*len(suites)))) % (iteration + 1) == 0:
                failed_step.clear()

            first_run = True
            done = False
            print('RLTCP3 - iter ' + str(iteration))
            test_cases = []

            for test_id in suite.keys():
                test_content = suite[test_id]
                test_cases.append(TestCase(test_id, test_content))

            total_time = 0
            max_time = self.training_max_ite
            while not done and total_time < max_time:
                cg = old_command_graph
                order = predictor.predict(cg, test_cases)
                chosen_order = order
                done = terminal_checker.should_terminate(test_result, test_cases, chosen_order)

                penalty_for_failed_tests = 0
                if first_run:
                    penalty_for_failed_tests = 10
                    if iteration > 0:
                        cg = self.reward_current_release(cg, failed_step, passed_step, test_cases)
                    order = predictor.predict(cg, test_cases)
                    result['test_cases'].append(test_cases)
                    result['order'].append(order)
                    result['run_result'].append(test_result)


                reward_graph = self.build_reward(
                    test_result, test_cases, chosen_order, penalty_for_failed_tests, all_results, failed_step, passed_step, test_steps
                )
                old_command_graph = merger.merge_fail_step_3_2(failed_step, reward_graph, cg, self.graph_merge_discount)

                total_time += 1
                first_run = False

            iteration += 1

        return result

    def build_reward(self, test_result, test_cases, chosen_order, penalty_for_failed_tests, all_results, all_failed_steps, all_pass_step, test_steps):
        return reward_converter.convert3_2(test_result, test_cases, chosen_order, penalty_for_failed_tests, self.penalty_decay_rate, all_results, self.max_past_step, self.factor_reduction_amt, all_failed_steps,all_pass_step, test_steps)

    def reward_current_release(self, subgraph, fail_steps, passed_steps, new_test_cases):
        sg = subgraph
        for test in new_test_cases:
            for step_left, step_right in zip(test.test_content[0::2], test.test_content[1::2]):
                vertices = step_left + step_right
                if step_left in fail_steps:
                    add_value = -1
                elif step_right in fail_steps:
                    add_value = 10.5
                else:
                    add_value = 0
                add_value -= 3.5
                edge = Edge(vertices, step_left, step_right, add_value)
                sg.add_or_update(sg.edges, edge)
        return sg