# This implementation demonstrates the Factory design pattern in a FastAPI context with several key components:
# Key Features:
# 1. Abstract Base Class (DataProcessor)

# Defines the interface that all concrete processors must implement
# Ensures consistent behavior across different processor types

# 2. Concrete Implementations

# JSONProcessor: Handles JSON data parsing and validation
# XMLProcessor: Processes XML data and extracts structure info
# CSVProcessor: Parses CSV data and provides statistics

# 3. Factory Class (DataProcessorFactory)

# Encapsulates the creation logic for different processors
# Uses a registry pattern to map processor types to classes
# Provides methods to create processors and list available types

# 4. FastAPI Integration

# /process endpoint: Uses the factory to create processors based on request type
# /processors endpoint: Lists available processor types
# /processor/{type}/metadata endpoint: Gets metadata for specific processors
# Proper error handling with HTTP status codes

# Usage Examples:
# To test this API, you can send POST requests to /process:
# json{
#   "data": "{\"name\": \"John\", \"age\": 30}",
#   "processor_type": "json"
# }
# The factory pattern provides several benefits here:

# Extensibility: Easy to add new processor types without modifying existing code
# Decoupling: Client code doesn't need to know about specific processor classes
# Centralized Creation: All processor creation logic is in one place
# Type Safety: Using enums ensures only valid processor types are accepted

# To run this, save the code and execute:
# bashpip install fastapi uvicorn
# python your_file.py
# Then visit http://localhost:8000/docs to see the interactive API documentation.

## IMPLEMENTATION BELOW ##

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum

# Pydantic models for request/response
class ProcessorType(str, Enum):
    JSON = "json"
    XML = "xml"
    CSV = "csv"

class DataRequest(BaseModel):
    data: str
    processor_type: ProcessorType

class ProcessedResponse(BaseModel):
    original_data: str
    processed_data: Dict[str, Any]
    processor_used: str
    metadata: Dict[str, Any]

# Abstract base class for data processors
class DataProcessor(ABC):
    @abstractmethod
    def process(self, data: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        pass

# Concrete processor implementations
class JSONProcessor(DataProcessor):
    def process(self, data: str) -> Dict[str, Any]:
        import json
        try:
            parsed = json.loads(data)
            return {
                "type": "json",
                "keys": list(parsed.keys()) if isinstance(parsed, dict) else [],
                "length": len(str(parsed)),
                "parsed_content": parsed
            }
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format", "type": "json"}
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "processor": "JSONProcessor",
            "version": "1.0",
            "supported_operations": ["parse", "validate", "extract_keys"]
        }

class XMLProcessor(DataProcessor):
    def process(self, data: str) -> Dict[str, Any]:
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            return {
                "type": "xml",
                "root_tag": root.tag,
                "children_count": len(root),
                "attributes": root.attrib,
                "text_content": root.text or ""
            }
        except ET.ParseError:
            return {"error": "Invalid XML format", "type": "xml"}
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "processor": "XMLProcessor",
            "version": "1.0",
            "supported_operations": ["parse", "extract_elements", "validate_structure"]
        }

class CSVProcessor(DataProcessor):
    def process(self, data: str) -> Dict[str, Any]:
        import csv
        from io import StringIO
        try:
            csv_reader = csv.reader(StringIO(data))
            rows = list(csv_reader)
            return {
                "type": "csv",
                "row_count": len(rows),
                "column_count": len(rows[0]) if rows else 0,
                "headers": rows[0] if rows else [],
                "sample_data": rows[1:3] if len(rows) > 1 else []
            }
        except Exception as e:
            return {"error": f"Invalid CSV format: {str(e)}", "type": "csv"}
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "processor": "CSVProcessor",
            "version": "1.0",
            "supported_operations": ["parse", "count_rows", "extract_headers"]
        }

# Factory class
class DataProcessorFactory:
    _processors = {
        ProcessorType.JSON: JSONProcessor,
        ProcessorType.XML: XMLProcessor,
        ProcessorType.CSV: CSVProcessor
    }
    
    @classmethod
    def create_processor(cls, processor_type: ProcessorType) -> DataProcessor:
        processor_class = cls._processors.get(processor_type)
        if not processor_class:
            raise ValueError(f"Unsupported processor type: {processor_type}")
        return processor_class()
    
    @classmethod
    def get_available_processors(cls) -> List[str]:
        return list(cls._processors.keys())

# FastAPI app
app = FastAPI(title="Data Processor API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Data Processor API using Factory Pattern"}

@app.get("/processors")
async def get_available_processors():
    """Get list of available data processors"""
    return {
        "available_processors": DataProcessorFactory.get_available_processors(),
        "count": len(DataProcessorFactory.get_available_processors())
    }

@app.post("/process", response_model=ProcessedResponse)
async def process_data(request: DataRequest):
    """Process data using the specified processor type"""
    try:
        # Use factory to create the appropriate processor
        processor = DataProcessorFactory.create_processor(request.processor_type)
        
        # Process the data
        processed_data = processor.process(request.data)
        metadata = processor.get_metadata()
        
        return ProcessedResponse(
            original_data=request.data,
            processed_data=processed_data,
            processor_used=request.processor_type.value,
            metadata=metadata
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/processor/{processor_type}/metadata")
async def get_processor_metadata(processor_type: ProcessorType):
    """Get metadata for a specific processor type"""
    try:
        processor = DataProcessorFactory.create_processor(processor_type)
        return {
            "processor_type": processor_type.value,
            "metadata": processor.get_metadata()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Example usage and test endpoints
@app.get("/examples")
async def get_examples():
    """Get example data for testing different processors"""
    return {
        "json_example": '{"name": "John", "age": 30, "city": "New York"}',
        "xml_example": '<person><name>John</name><age>30</age><city>New York</city></person>',
        "csv_example": "name,age,city\nJohn,30,New York\nJane,25,Los Angeles"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
