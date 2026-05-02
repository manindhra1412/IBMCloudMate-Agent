from ibm_cloud_sdk_core import ApiException
from ibmcloudant.cloudant_v1 import CloudantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from langchain.tools import Tool
import json
import os

def get_cloudant_client():
    """Initialize and return a Cloudant client"""
    authenticator = IAMAuthenticator(os.getenv("IAM_API_KEY"), url="https://iam.test.cloud.ibm.com")
    client = CloudantV1(authenticator=authenticator)
    client.set_service_url(os.getenv("CLOUDANT_URL"))
    print("IAM_API_KEY from env:", os.getenv("IAM_API_KEY"))

    print(f"Connected to Cloudant Service ✅")
    return client

def cloudant_create_db(query: str) -> str:
    """Create a new database"""
    try:
        db_name = query.strip()
        if not db_name:
            return "Error: Database name not provided"
            
        try:
            client = get_cloudant_client()
            
            try:
                print(f"Creating database: {db_name}")
                put_database_result = client.put_database(db=db_name).get_result()
                if put_database_result["ok"]:
                    return f'Successfully created database "{db_name}"'
            except ApiException as ae:
                if ae.status_code == 412:
                    return f'Database "{db_name}" already exists'
                return f"Error creating database: {str(ae)}"
                
        except Exception as e:
            return f"Error connecting to Cloudant: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_delete_db(query: str) -> str:
    """Delete a database"""
    try:
        db_name = query.strip()
        if not db_name:
            return "Error: Database name not provided"
            
        try:
            client = get_cloudant_client()
            
            try:
                delete_database_result = client.delete_database(db=db_name).get_result()
                if delete_database_result["ok"]:
                    return f'Successfully deleted database "{db_name}"'
            except ApiException as ae:
                if ae.status_code == 404:
                    return f'Database "{db_name}" does not exist'
                return f"Error deleting database: {str(ae)}"
                
        except Exception as e:
            return f"Error connecting to Cloudant: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_get_docs(query: str) -> str:
    """Get all documents from a database"""
    try:
        db_name = query.strip()
        if not db_name:
            return "Error: Database name not provided"
            
        try:
            client = get_cloudant_client()
            
            try:
                result = client.post_all_docs(
                    db=db_name,
                    include_docs=True,
                    limit=100
                ).get_result()
                
                if not result.get('rows'):
                    return f'No documents found in database "{db_name}"'
                    
                docs = [doc['doc'] for doc in result['rows']]
                formatted_docs = []
                for doc in docs:
                    if '_id' in doc:
                        doc_id = doc.pop('_id')
                    if '_rev' in doc:
                        doc.pop('_rev')
                    formatted_docs.append({
                        'id': doc_id,
                        'content': doc
                    })
                
                return f'Found {len(docs)} documents in database "{db_name}":\n{json.dumps(formatted_docs, indent=2)}'
                
            except ApiException as ae:
                if ae.status_code == 404:
                    return f'Database "{db_name}" does not exist'
                return f"Error getting documents: {str(ae)}"
                
        except Exception as e:
            return f"Error connecting to Cloudant: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_query_docs(query: str) -> str:
    """Query documents in a database"""
    try:
        parts = query.strip().split(' ', 2)
        if len(parts) != 3:
            return "Error: Please provide database name, field, and value to filter by"
            
        db_name, field, value = parts
            
        try:
            client = get_cloudant_client()
            
            try:
                selector = {field: value}
                
                result = client.post_find(
                    db=db_name,
                    selector=selector
                ).get_result()
                
                if not result.get('docs'):
                    return f'No documents found in database "{db_name}" matching {field}={value}'
                    
                return f'Found {len(result["docs"])} documents matching {field}={value}:\n{json.dumps(result["docs"], indent=2)}'
                
            except ApiException as ae:
                if ae.status_code == 404:
                    return f'Database "{db_name}" does not exist'
                return f"Error querying documents: {str(ae)}"
                
        except Exception as e:
            return f"Error connecting to Cloudant: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_create_doc(query: str) -> str:
    """Create a new document in a database"""
    try:
        parts = query.strip().split(' ', 1)
        if len(parts) != 2:
            return "Error: Please provide database name and document JSON"
            
        db_name, doc_json = parts
        
        try:
            doc = json.loads(doc_json)
            client = get_cloudant_client()
            
            try:
                result = client.post_document(
                    db=db_name,
                    document=doc
                ).get_result()
                
                return f'Successfully created document with ID "{result["id"]}" in database "{db_name}"'
                
            except ApiException as ae:
                if ae.status_code == 404:
                    return f'Database "{db_name}" does not exist'
                return f"Error creating document: {str(ae)}"
                
        except json.JSONDecodeError:
            return "Error: Invalid JSON format for document"
        except Exception as e:
            return f"Error connecting to Cloudant: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_update_doc(query: str) -> str:
    """Update an existing document"""
    try:
        parts = query.strip().split(' ', 2)
        if len(parts) != 3:
            return "Error: Please provide database name, document ID, and document JSON"
            
        db_name, doc_id, doc_json = parts
        
        try:
            doc = json.loads(doc_json)
            client = get_cloudant_client()
            
            try:
                current_doc = client.get_document(
                    db=db_name,
                    doc_id=doc_id
                ).get_result()
                
                doc['_rev'] = current_doc['_rev']
                result = client.put_document(
                    db=db_name,
                    doc_id=doc_id,
                    document=doc
                ).get_result()
                
                return f'Successfully updated document "{doc_id}" in database "{db_name}"'
                
            except ApiException as ae:
                if ae.status_code == 404:
                    return f'Document "{doc_id}" not found in database "{db_name}"'
                return f"Error updating document: {str(ae)}"
                
        except json.JSONDecodeError:
            return "Error: Invalid JSON format for document"
        except Exception as e:
            return f"Error connecting to Cloudant: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_delete_doc(query: str) -> str:
    """Delete a document from a database"""
    try:
        parts = query.strip().split(' ', 1)
        if len(parts) != 2:
            return "Error: Please provide database name and document ID"
            
        db_name, doc_id = parts
        
        try:
            client = get_cloudant_client()
            
            try:
                current_doc = client.get_document(
                    db=db_name,
                    doc_id=doc_id
                ).get_result()
                
                result = client.delete_document(
                    db=db_name,
                    doc_id=doc_id,
                    rev=current_doc['_rev']
                ).get_result()
                
                return f'Successfully deleted document "{doc_id}" from database "{db_name}"'
                
            except ApiException as ae:
                if ae.status_code == 404:
                    return f'Document "{doc_id}" not found in database "{db_name}"'
                return f"Error deleting document: {str(ae)}"
                
        except Exception as e:
            return f"Error connecting to Cloudant: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_get_doc(query: str) -> str:
    """Get a specific document from a database"""
    try:
        parts = query.strip().split(' ', 1)
        if len(parts) != 2:
            return "Error: Please provide database name and document ID"
            
        db_name, doc_id = parts
        
        try:
            client = get_cloudant_client()
            
            try:
                result = client.get_document(
                    db=db_name,
                    doc_id=doc_id
                ).get_result()
                
                # Remove internal Cloudant fields
                if '_id' in result:
                    doc_id = result.pop('_id')
                if '_rev' in result:
                    result.pop('_rev')
                    
                return f'Document "{doc_id}" from database "{db_name}":\n{json.dumps(result, indent=2)}'
                
            except ApiException as ae:
                if ae.status_code == 404:
                    return f'Document "{doc_id}" not found in database "{db_name}"'
                return f"Error getting document: {str(ae)}"
                
        except Exception as e:
            return f"Error connecting to Cloudant: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_get_all_dbs(query: str) -> str:
    """Get all databases"""
    try:
        client = get_cloudant_client()
        
        try:
            result = client.get_all_dbs().get_result()
            return f"Available databases:\n{json.dumps(result, indent=2)}"
            
        except ApiException as ae:
            return f"Error getting databases: {str(ae)}"
            
    except Exception as e:
        return f"Error connecting to Cloudant: {str(e)}"

def cloudant_complex_query(query: str) -> str:
    """Query documents in a Cloudant database using multiple conditions"""
    try:
        # Expected format: "db_name|query_json"
        parts = query.split("|", 1)
        if len(parts) != 2:
            return "Error: Invalid format. Use 'db_name|query_json'"
            
        db_name, query_json = parts
        try:
            query_obj = json.loads(query_json)
        except json.JSONDecodeError:
            return "Error: Invalid JSON query"
            
        service = get_cloudant_client()
        
        # Execute the query with all fields
        response = service.post_find(
            db=db_name,
            selector=query_obj.get('selector', {}),
            fields=query_obj.get('fields', None),  # Return all fields if not specified
            sort=query_obj.get('sort', []),
            limit=query_obj.get('limit', 25),
            skip=query_obj.get('skip', 0)
        ).get_result()
        
        # Format the response to show complete documents
        result = {
            "total_docs": len(response.get('docs', [])),
            "documents": response.get('docs', [])
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_create_index(query: str) -> str:
    """Create an index in a Cloudant database"""
    try:
        # Expected format: "db_name|index_json"
        parts = query.split("|", 1)
        if len(parts) != 2:
            return "Error: Invalid format. Use 'db_name|index_json'"
            
        db_name, index_json = parts
        try:
            index_def = json.loads(index_json)
        except json.JSONDecodeError:
            return "Error: Invalid JSON index definition"
            
        service = get_cloudant_client()
        
        # Create the index
        response = service.post_index(
            db=db_name,
            index=index_def
        ).get_result()
        
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_list_indexes(query: str) -> str:
    """List all indexes in a Cloudant database"""
    try:
        db_name = query.strip()
        if not db_name:
            return "Error: Database name not provided"
            
        service = get_cloudant_client()
        response = service.get_indexes(db=db_name).get_result()
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

def cloudant_delete_index(query: str) -> str:
    """Delete an index from a Cloudant database"""
    try:
        # Expected format: "db_name|index_name|design_doc_id"
        parts = query.split("|")
        if len(parts) != 3:
            return "Error: Invalid format. Use 'db_name|index_name|design_doc_id'"
            
        db_name, index_name, design_doc_id = parts
        service = get_cloudant_client()
        
        response = service.delete_index(
            db=db_name,
            ddoc=design_doc_id,
            index=index_name
        ).get_result()
        
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

# Create Tool instances
cloudant_tools = [
    Tool(
        name="cloudant_create_db",
        func=cloudant_create_db,
        description="Create a new database. Input format: 'database_name'"
    ),
    Tool(
        name="cloudant_delete_db",
        func=cloudant_delete_db,
        description="Delete a database. Input format: 'database_name'"
    ),
    Tool(
        name="cloudant_get_docs",
        func=cloudant_get_docs,
        description="Get all documents from a database. Input format: 'database_name'"
    ),
    Tool(
        name="cloudant_query_docs",
        func=cloudant_query_docs,
        description="Query documents in a database. Input format: 'database_name field value'"
    ),
    Tool(
        name="cloudant_create_doc",
        func=cloudant_create_doc,
        description="Create a new document in a database. Input format: 'database_name document_json'"
    ),
    Tool(
        name="cloudant_update_doc",
        func=cloudant_update_doc,
        description="Update an existing document. Input format: 'database_name doc_id document_json'"
    ),
    Tool(
        name="cloudant_delete_doc",
        func=cloudant_delete_doc,
        description="Delete a document from a database. Input format: 'database_name doc_id'"
    ),
    Tool(
        name="cloudant_get_doc",
        func=cloudant_get_doc,
        description="Get a specific document from a database. Input format: 'database_name doc_id'"
    ),
    Tool(
        name="cloudant_get_all_dbs",
        func=cloudant_get_all_dbs,
        description="Get all databases"
    ),
    Tool(
        name="cloudant_complex_query",
        func=cloudant_complex_query,
        description="Query documents in a Cloudant database using multiple conditions. Input format: 'db_name|query_json'"
    ),
    Tool(
        name="cloudant_create_index",
        func=cloudant_create_index,
        description="Create an index in a Cloudant database. Input format: 'db_name|index_json'"
    ),
    Tool(
        name="cloudant_list_indexes",
        func=cloudant_list_indexes,
        description="List all indexes in a Cloudant database. Input format: 'db_name'"
    ),
    Tool(
        name="cloudant_delete_index",
        func=cloudant_delete_index,
        description="Delete an index from a Cloudant database. Input format: 'db_name|index_name|design_doc_id'"
    )
] 