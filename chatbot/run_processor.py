from document_processor import DocumentProcessor

def main():
    try:
        # Initialize processor
        processor = DocumentProcessor()
        
        # Process documents
        processor.process_documents()
        
        # Test queries to verify processing
        test_queries = [
            "מה זה אוטוקול?",
            "איך עובדת ההגנה?",
            "מי זה מובנה גלובל?",
            "מה היתרונות של המוצר?",
            "איך עובד המוצר?"
        ]
        
        print("\nTesting document knowledge with queries:")
        for query in test_queries:
            print(f"\nQuery: {query}")
            results = processor.query_knowledge(query)
            print("Results:")
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(result)

    except Exception as e:
        print(f"Error in document processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()
