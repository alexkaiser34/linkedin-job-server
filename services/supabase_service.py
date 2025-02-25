def process_supabase_webhook(data):
    """
    Process webhook data from Supabase when new rows are added
    
    Args:
        data (dict): The webhook payload from Supabase containing new row data
        
    Returns:
        dict: Response with processing results
    """
    try:
        # For Supabase database webhooks, the structure might be different
        # than the example. Let's handle both potential formats.
        
        # Check if this is a standard webhook format
        if 'type' in data and 'table' in data and 'record' in data:
            event_type = data.get('type')
            table_name = data.get('table')
            new_record = data.get('record', {})
            
            # Only process INSERT events
            if event_type.lower() != 'insert':
                return {
                    "success": True,
                    "message": f"Ignored {event_type} event (only processing INSERTs)"
                }
                
            # Process the new row
            print(f"New row added to table {table_name}: {new_record}")
            
            # Here you would add your business logic for the new row
            # For example, sending notifications, updating other systems, etc.
            
            return {
                "success": True,
                "message": f"Processed new row in table {table_name}",
                "data": {
                    "table": table_name,
                    "record_id": new_record.get('id'),
                    "record": new_record
                }
            }
            
        # Alternative format: data might be an array of records or have a different structure
        elif isinstance(data, list):
            # Handle array of records
            processed_records = []
            
            for record in data:
                processed_records.append({
                    "record_id": record.get('id'),
                    "data": record
                })
                
            print(f"Processed {len(processed_records)} new records")
            
            return {
                "success": True,
                "message": f"Processed {len(processed_records)} new records",
                "data": processed_records
            }
            
        # If we can't determine the format, just log what we received
        else:
            print(f"Received webhook data in unknown format: {data}")
            
            return {
                "success": True,
                "message": "Processed webhook with unknown format",
                "data": data
            }
            
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing webhook: {str(e)}")
        
        # Return error response
        return {
            "success": False,
            "error": str(e)
        } 