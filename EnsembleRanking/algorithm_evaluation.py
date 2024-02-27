import time

class AlgorithmEvaluation:
    def __init__(self, suites):
        self.suites = suites

    def start_evaluation(self, algorithms):
        res = { 'test_cases': [], 'order': [], 'run_result': []}
        for alg in algorithms:
            start_time = time.time()
            execution = alg.prioritize_suites(self.suites)
            res['test_cases'].append(execution['test_cases'])
            res['order'].append(execution['order'])
            res['run_result'].append(execution['run_result'])
            print(str(alg) + "--- %s seconds ---" % (time.time() - start_time))
        return res
