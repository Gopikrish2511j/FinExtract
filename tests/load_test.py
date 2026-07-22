from locust import HttpUser, task, between

class FinExtractLoadTester(HttpUser):
    wait_time = between(1, 2)

    @task
    def test_list_documents(self):
        self.client.get("/api/documents")

    @task
    def test_results_load(self):
        # Stress test the results calculation for a sample doc ID
        self.client.get("/api/results/1")
