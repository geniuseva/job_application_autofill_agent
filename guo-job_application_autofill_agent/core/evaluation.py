import json
import time
import logging
import pandas as pd
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EvaluationFramework:
    """Framework for evaluating the job application autofill multi-agent system"""
    
    def __init__(self, test_cases_file=None):
        """Initialize the evaluation framework"""
        self.test_cases = []
        if test_cases_file:
            self.load_test_cases(test_cases_file)
    
    def load_test_cases(self, file_path):
        """Load test cases from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                self.test_cases = json.load(f)
            logger.info(f"Loaded {len(self.test_cases)} test cases from {file_path}")
        except Exception as e:
            logger.error(f"Error loading test cases: {str(e)}")
    
    def create_test_cases(self, urls, ground_truth_file=None):
        """Create test cases from a list of URLs and optional ground truth file"""
        self.test_cases = []
        
        for url in urls:
            test_case = {
                "url": url,
                "ground_truth": {}
            }
            self.test_cases.append(test_case)
        
        if ground_truth_file:
            try:
                with open(ground_truth_file, 'r') as f:
                    ground_truths = json.load(f)
                
                # Match ground truths to test cases by URL
                for i, test_case in enumerate(self.test_cases):
                    url = test_case["url"]
                    if url in ground_truths:
                        self.test_cases[i]["ground_truth"] = ground_truths[url]
            except Exception as e:
                logger.error(f"Error loading ground truths: {str(e)}")
        
        logger.info(f"Created {len(self.test_cases)} test cases")
    
    def save_test_cases(self, file_path):
        """Save test cases to a JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.test_cases, f, indent=2)
            logger.info(f"Saved {len(self.test_cases)} test cases to {file_path}")
        except Exception as e:
            logger.error(f"Error saving test cases: {str(e)}")
    
    def evaluate_accuracy(self, results):
        """
        Evaluate the accuracy of the autofill results against ground truth
        
        Args:
            results (dict): Dictionary of results keyed by URL
            
        Returns:
            dict: Accuracy metrics
        """
        metrics = {
            "total_fields": 0,
            "correctly_filled": 0,
            "incorrectly_filled": 0,
            "not_filled": 0,
            "accuracy": 0.0
        }
        
        for test_case in self.test_cases:
            url = test_case["url"]
            ground_truth = test_case.get("ground_truth", {})
            
            if url not in results:
                continue
            
            result = results[url]
            
            # Count fields in ground truth
            total_fields = len(ground_truth)
            metrics["total_fields"] += total_fields
            
            # Compare filled fields with ground truth
            filled_fields = result.get("filled_fields", [])
            not_filled_fields = result.get("not_filled_fields", [])
            
            for field_name, expected_value in ground_truth.items():
                if field_name in filled_fields:
                    # Check if the value is correct
                    actual_value = result.get("field_values", {}).get(field_name)
                    if actual_value == expected_value:
                        metrics["correctly_filled"] += 1
                    else:
                        metrics["incorrectly_filled"] += 1
                else:
                    metrics["not_filled"] += 1
        
        # Calculate overall accuracy
        if metrics["total_fields"] > 0:
            metrics["accuracy"] = (metrics["correctly_filled"] / metrics["total_fields"]) * 100
        
        return metrics
    
    def evaluate_tokens(self, token_logs):
        """
        Evaluate token usage across agents
        
        Args:
            token_logs (list): List of token usage logs
            
        Returns:
            dict: Token usage metrics
        """
        metrics = {
            "total_tokens": 0,
            "tokens_by_agent": {},
            "tokens_by_model": {},
            "average_tokens_per_request": 0,
            "total_requests": 0
        }
        
        for log in token_logs:
            agent_name = log.get("agent", "unknown")
            model = log.get("model", "unknown")
            tokens = log.get("tokens", 0)
            
            metrics["total_tokens"] += tokens
            metrics["total_requests"] += 1
            
            # Tokens by agent
            if agent_name not in metrics["tokens_by_agent"]:
                metrics["tokens_by_agent"][agent_name] = 0
            metrics["tokens_by_agent"][agent_name] += tokens
            
            # Tokens by model
            if model not in metrics["tokens_by_model"]:
                metrics["tokens_by_model"][model] = 0
            metrics["tokens_by_model"][model] += tokens
        
        # Calculate average tokens per request
        if metrics["total_requests"] > 0:
            metrics["average_tokens_per_request"] = metrics["total_tokens"] / metrics["total_requests"]
        
        return metrics
    
    def evaluate_time(self, time_logs):
        """
        Evaluate time usage across agents
        
        Args:
            time_logs (list): List of time usage logs
            
        Returns:
            dict: Time usage metrics
        """
        metrics = {
            "total_time": 0,
            "time_by_agent": {},
            "average_time_per_request": 0,
            "total_requests": 0,
            "breakdown": {
                "scraping": 0,
                "mapping": 0,
                "database": 0,
                "autofill": 0,
                "orchestration": 0
            }
        }
        
        for log in time_logs:
            agent_name = log.get("agent", "unknown")
            duration = log.get("duration", 0)
            operation = log.get("operation", "unknown")
            
            metrics["total_time"] += duration
            metrics["total_requests"] += 1
            
            # Time by agent
            if agent_name not in metrics["time_by_agent"]:
                metrics["time_by_agent"][agent_name] = 0
            metrics["time_by_agent"][agent_name] += duration
            
            # Breakdown by operation type
            if "scrape" in operation.lower():
                metrics["breakdown"]["scraping"] += duration
            elif "map" in operation.lower():
                metrics["breakdown"]["mapping"] += duration
            elif "database" in operation.lower() or "db" in operation.lower():
                metrics["breakdown"]["database"] += duration
            elif "fill" in operation.lower() or "autofill" in operation.lower():
                metrics["breakdown"]["autofill"] += duration
            else:
                metrics["breakdown"]["orchestration"] += duration
        
        # Calculate average time per request
        if metrics["total_requests"] > 0:
            metrics["average_time_per_request"] = metrics["total_time"] / metrics["total_requests"]
        
        return metrics
    
    def run_evaluation(self, agent_workflow_function, test_cases=None):
        """
        Run the evaluation on a multi-agent workflow
        
        Args:
            agent_workflow_function: Function that implements the agent workflow
            test_cases (list, optional): Test cases to use, defaults to self.test_cases
            
        Returns:
            dict: Evaluation results
        """
        if test_cases is None:
            test_cases = self.test_cases
        
        results = {}
        token_logs = []
        time_logs = []
        
        logger.info(f"Starting evaluation with {len(test_cases)} test cases")
        
        for test_case in tqdm(test_cases, desc="Running test cases"):
            url = test_case["url"]
            
            # Measure time for this test case
            start_time = time.time()
            
            # Run the agent workflow
            try:
                result, case_token_logs, case_time_logs = agent_workflow_function(url)
                results[url] = result
                token_logs.extend(case_token_logs)
                time_logs.extend(case_time_logs)
            except Exception as e:
                logger.error(f"Error running test case for URL {url}: {str(e)}")
                results[url] = {"error": str(e)}
            
            end_time = time.time()
            
            # Log test case duration
            time_logs.append({
                "agent": "EvaluationFramework",
                "operation": f"test_case_{url}",
                "duration": end_time - start_time
            })
        
        # Evaluate accuracy, token usage, and time usage
        accuracy_metrics = self.evaluate_accuracy(results)
        token_metrics = self.evaluate_tokens(token_logs)
        time_metrics = self.evaluate_time(time_logs)
        
        # Combine metrics into a comprehensive report
        evaluation_report = {
            "accuracy": accuracy_metrics,
            "tokens": token_metrics,
            "time": time_metrics,
            "raw_results": results,
            "test_cases_count": len(test_cases)
        }
        
        return evaluation_report
    
    def compare_workflows(self, workflow_functions, workflow_names=None):
        """
        Compare different agent workflows
        
        Args:
            workflow_functions (list): List of workflow functions to compare
            workflow_names (list, optional): List of names for the workflows
            
        Returns:
            dict: Comparison results
        """
        if workflow_names is None:
            workflow_names = [f"Workflow_{i+1}" for i in range(len(workflow_functions))]
        
        comparison_results = {}
        
        for i, workflow_function in enumerate(workflow_functions):
            workflow_name = workflow_names[i]
            logger.info(f"Evaluating {workflow_name}...")
            
            evaluation_report = self.run_evaluation(workflow_function)
            comparison_results[workflow_name] = evaluation_report
        
        # Create a summary comparison
        summary = {
            "accuracy": {},
            "tokens": {},
            "time": {}
        }
        
        for workflow_name, report in comparison_results.items():
            summary["accuracy"][workflow_name] = report["accuracy"]["accuracy"]
            summary["tokens"][workflow_name] = report["tokens"]["total_tokens"]
            summary["time"][workflow_name] = report["time"]["total_time"]
        
        comparison_results["summary"] = summary
        
        return comparison_results
    
    def generate_report(self, evaluation_report, output_file=None):
        """
        Generate a human-readable report from evaluation results
        
        Args:
            evaluation_report (dict): Evaluation results
            output_file (str, optional): Path to save the report
            
        Returns:
            str: Report text
        """
        report_lines = []
        
        # Add header
        report_lines.append("# Job Application Autofill Evaluation Report")
        report_lines.append("")
        
        # Add accuracy metrics
        report_lines.append("## Accuracy Metrics")
        report_lines.append("")
        accuracy = evaluation_report["accuracy"]
        report_lines.append(f"- Total fields: {accuracy['total_fields']}")
        report_lines.append(f"- Correctly filled: {accuracy['correctly_filled']}")
        report_lines.append(f"- Incorrectly filled: {accuracy['incorrectly_filled']}")
        report_lines.append(f"- Not filled: {accuracy['not_filled']}")
        report_lines.append(f"- Overall accuracy: {accuracy['accuracy']:.2f}%")
        report_lines.append("")
        
        # Add token usage metrics
        report_lines.append("## Token Usage Metrics")
        report_lines.append("")
        tokens = evaluation_report["tokens"]
        report_lines.append(f"- Total tokens: {tokens['total_tokens']}")
        report_lines.append(f"- Total requests: {tokens['total_requests']}")
        report_lines.append(f"- Average tokens per request: {tokens['average_tokens_per_request']:.2f}")
        report_lines.append("")
        
        # Add tokens by agent
        report_lines.append("### Tokens by Agent")
        report_lines.append("")
        for agent, agent_tokens in tokens['tokens_by_agent'].items():
            report_lines.append(f"- {agent}: {agent_tokens}")
        report_lines.append("")
        
        # Add time usage metrics
        report_lines.append("## Time Usage Metrics")
        report_lines.append("")
        time_metrics = evaluation_report["time"]
        report_lines.append(f"- Total time: {time_metrics['total_time']:.2f} seconds")
        report_lines.append(f"- Total requests: {time_metrics['total_requests']}")
        report_lines.append(f"- Average time per request: {time_metrics['average_time_per_request']:.2f} seconds")
        report_lines.append("")
        
        # Add time by agent
        report_lines.append("### Time by Agent")
        report_lines.append("")
        for agent, agent_time in time_metrics['time_by_agent'].items():
            percentage = (agent_time / time_metrics['total_time']) * 100
            report_lines.append(f"- {agent}: {agent_time:.2f} seconds ({percentage:.2f}%)")
        report_lines.append("")
        
        # Add time breakdown by operation
        report_lines.append("### Time Breakdown by Operation")
        report_lines.append("")
        for operation, operation_time in time_metrics['breakdown'].items():
            percentage = (operation_time / time_metrics['total_time']) * 100
            report_lines.append(f"- {operation.capitalize()}: {operation_time:.2f} seconds ({percentage:.2f}%)")
        report_lines.append("")
        
        # Add test cases summary
        report_lines.append("## Test Cases Summary")
        report_lines.append("")
        report_lines.append(f"- Total test cases: {evaluation_report['test_cases_count']}")
        report_lines.append("")
        
        # Combine all lines into a report
        report_text = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                logger.info(f"Evaluation report saved to {output_file}")
            except Exception as e:
                logger.error(f"Error saving evaluation report: {str(e)}")
        
        return report_text

def run_evaluation_with_orchestrator(orchestrator_function, test_urls, ground_truth_file=None):
    """
    Run an evaluation of the orchestrator workflow
    
    Args:
        orchestrator_function: Function that implements the orchestrator workflow
        test_urls (list): List of URLs to test
        ground_truth_file (str, optional): Path to ground truth file
        
    Returns:
        dict: Evaluation report
    """
    # Create an evaluation framework
    evaluator = EvaluationFramework()
    
    # Create test cases
    evaluator.create_test_cases(test_urls, ground_truth_file)
    
    # Run the evaluation
    evaluation_report = evaluator.run_evaluation(orchestrator_function)
    
    # Generate a report
    report_text = evaluator.generate_report(evaluation_report, "evaluation_report.md")
    
    return evaluation_report, report_text

if __name__ == "__main__":
    # If this script is run directly, execute a simple evaluation
    from core.orchestrator import orchestrator_workflow
    
    # Example test URLs
    test_urls = [
        "https://example.com/job-application1",
        "https://example.com/job-application2",
    ]
    
    # Run the evaluation
    evaluation_report, report_text = run_evaluation_with_orchestrator(
        orchestrator_workflow, test_urls
    )
    
    # Print the report
    print(report_text)