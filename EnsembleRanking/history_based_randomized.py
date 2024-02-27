from test_case import TestCase
import random

def get_ordered_test_indexes(test_ids, prioritized_order):
    return [test_ids.index(test_id) for test_id in prioritized_order]


class HisBasedRandomNewTestLast:
    def prioritize_suites(self, suites):
        result = {'test_cases': [], 'order': [], 'run_result': []}
        previous_fails = []
        previous_success = []

        for commands, test_result, path in suites:
            suite = commands.keys()

            order_f = []
            order_p = []
            for pfail in previous_fails:
                clone = pfail
                filtered = [element for element in pfail if element in suite]
                random.shuffle(filtered)
                order_f += filtered
            order_f.reverse()
            order_f = list(set(order_f))

            for psuccess in previous_fails:
                clone = psuccess
                filtered = [element for element in pfail if element in suite]
                random.shuffle(filtered)
                order_p += filtered
            order_p.reverse()
            order_p = list(set(order_p))

            order_f_and_p = list(set(order_f + order_p))
            new_tests = [element for element in suite if element not in order_f_and_p]
            prioritized_order = order_f_and_p + new_tests

            test_cases = [TestCase(test_id, None) for test_id in suite]

            result['test_cases'].append(test_cases)
            result['order'].append(
                get_ordered_test_indexes(list(suite), prioritized_order)
            )
            result['run_result'].append(test_result)

            failed_tests = [element for element in prioritized_order
                if test_result.test_did_fail(element)
            ]
            passed_tests = [element for element in prioritized_order
                if not test_result.test_did_fail(element)
            ]
            previous_fails.append(failed_tests)
            previous_success.append(passed_tests)
        return result


class HisBasedRandomNewTestFirst:
    def prioritize_suites(self, suites):
        result = {'test_cases': [], 'order': [], 'run_result': []}
        previous_fails = []
        previous_success = []

        for commands, test_result, path in suites:
            suite = commands.keys()

            order_f = []
            order_p = []
            for pfail in previous_fails:
                clone = pfail
                filtered = [element for element in pfail if element in suite]
                random.shuffle(filtered)
                order_f += filtered
            order_f.reverse()
            order_f = list(set(order_f))

            for psuccess in previous_fails:
                clone = psuccess
                filtered = [element for element in pfail if element in suite]
                random.shuffle(filtered)
                order_p += filtered
            order_p.reverse()
            order_p = list(set(order_p))

            order_f_and_p = list(set(order_f + order_p))
            new_tests = [element for element in suite if element not in order_f_and_p]
            prioritized_order = new_tests + order_f_and_p

            test_cases = [TestCase(test_id, None) for test_id in suite]

            result['test_cases'].append(test_cases)
            result['order'].append(
                get_ordered_test_indexes(list(suite), prioritized_order)
            )
            result['run_result'].append(test_result)

            failed_tests = [element for element in prioritized_order
                if test_result.test_did_fail(element)
            ]
            passed_tests = [element for element in prioritized_order
                if not test_result.test_did_fail(element)
            ]
            previous_fails.append(failed_tests)
            previous_success.append(passed_tests)
        return result
