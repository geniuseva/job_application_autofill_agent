import os
import argparse
import logging
from core.orchestrator import run_orchestrator
from core.evaluation import run_evaluation_with_orchestrator, EvaluationFramework

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the job application autofill agent"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Job Application Autofill Agent')
    parser.add_argument('--url', type=str, help='URL of the job application form')
    parser.add_argument('--evaluate', action='store_true', help='Run evaluation on test URLs')
    parser.add_argument('--test-urls', type=str, help='Path to file containing test URLs')
    parser.add_argument('--ground-truth', type=str, help='Path to ground truth file for evaluation')
    args = parser.parse_args()
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OpenAI API key not found in environment variables")
        print("Please set your OpenAI API key using: export OPENAI_API_KEY='your-api-key'")
        return
    
    # Run evaluation if requested
    if args.evaluate:
        # Load test URLs from file or use defaults
        test_urls = []
        if args.test_urls:
            try:
                with open(args.test_urls, 'r') as f:
                    test_urls = [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                logger.error(f"Error loading test URLs: {str(e)}")
                return
        else:
            # Use default test URLs
            test_urls = [
                "https://example.com/job-application1",
                "https://example.com/job-application2"
            ]
        
        # Run evaluation
        logger.info(f"Running evaluation on {len(test_urls)} test URLs")
        from core.orchestrator import orchestrator_workflow
        
        evaluation_report, report_text = run_evaluation_with_orchestrator(
            orchestrator_workflow, test_urls, args.ground_truth
        )
        
        # Print evaluation summary
        print("\nEvaluation Summary:")
        print(f"Total test cases: {evaluation_report['test_cases_count']}")
        print(f"Accuracy: {evaluation_report['accuracy']['accuracy']:.2f}%")
        print(f"Total time: {evaluation_report['time']['total_time']:.2f} seconds")
        
        # Print report location
        print("\nDetailed report saved to: evaluation_report.md")
        
    # Run autofill on a single URL if provided
    elif args.url:
        logger.info(f"Running autofill on URL: {args.url}")
        result = run_orchestrator(args.url)
        
        # Print results
        if result:
            print("\nAutofill Results:")
            print(f"Success: {result.get('success', False)}")
            print(f"Filled fields: {len(result.get('filled_fields', []))}")
            print(f"Not filled fields: {len(result.get('not_filled_fields', []))}")
            
            if result.get('metrics'):
                print(f"Fill rate: {result['metrics'].get('fill_rate', 0):.2f}%")
            
            print(f"Final URL: {result.get('final_url', '')}")
        else:
            print("Autofill failed. Check logs for details.")
    
    # If no URL or evaluation flag is provided, show help
    else:
        parser.print_help()

if __name__ == "__main__":
    main()