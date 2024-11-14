import logging
from document_processor import DocumentProcessor
import yaml
import os
from pathlib import Path

def test_yaml_configs():
    """Test loading YAML configurations"""
    print("\n=== Testing YAML Configurations ===")
    config_files = [
        'config/company_info.yaml',
        'config/products.yaml',
        'config/sales_responses.yaml'
    ]
    
    for config_file in config_files:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"\nLoaded {config_file}:")
                for key in config.keys():
                    print(f"- Found section: {key}")
        except Exception as e:
            print(f"Error loading {config_file}: {str(e)}")

def test_document_processing():
    """Test processing documents from documents1 folder"""
    print("\n=== Testing Document Processing ===")
    processor = DocumentProcessor()
    
    # List documents in documents1
    docs_dir = Path("documents1")
    print("\nDocuments found in documents1:")
    for file in docs_dir.glob("*.*"):
        if file.suffix.lower() in ['.pdf', '.docx', '.txt']:
            print(f"- {file.name}")
    
    # Process documents
    print("\nProcessing documents...")
    processor.process_documents()
    
    # Test queries
    test_queries = [
        "מה זה אוטוקול?",
        "איך עובדת ההגנה?",
        "מי זה מובנה גלובל?",
        "מה היתרונות של המוצר?",
        "איך עובד המוצר?"
    ]
    
    print("\nTesting queries:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = processor.query_knowledge(query)
        if results:
            print("Results:")
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(result[:200] + "..." if len(result) > 200 else result)
        else:
            print("No results found")

def test_combined_knowledge():
    """Test combining YAML and document knowledge"""
    print("\n=== Testing Combined Knowledge ===")
    processor = DocumentProcessor()
    
    # Test core knowledge
    print("\nTesting core knowledge:")
    topics = ["company", "product", "advantages", "security"]
    for topic in topics:
        print(f"\nTopic: {topic}")
        info = processor.get_core_knowledge(topic)
        print(info[:200] + "..." if len(info) > 200 else info)
    
    # Test combined queries
    print("\nTesting combined knowledge queries:")
    test_queries = [
        "מה היתרונות של מובנה גלובל?",
        "איך עובד מוצר האוטוקול?",
        "מה הביטחונות במוצר?",
        "איך מתבצעת ההשקעה?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = processor.query_knowledge(query)
        if results:
            print("Results:")
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(result[:200] + "..." if len(result) > 200 else result)
        else:
            print("No results found")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('document_processor.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    print("Starting document processor tests...")
    test_yaml_configs()
    test_document_processing()
    test_combined_knowledge()
    print("\nTests completed. Check document_processor.log for details.")