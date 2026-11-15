"""
ADLS Event Listener Controller

Receives Azure Event Grid events when parquet files are created, updated, or deleted
in Azure Data Lake Storage and triggers real-time migration to ClickHouse.

Azure Setup Required:
1. Go to your Storage Account in Azure Portal
2. Navigate to Events > + Event Subscription
3. Set Endpoint Type: Web Hook
4. Set Endpoint URL: https://your-domain.com/api/v1/adls-listener/events/
5. Filter to event types: Blob Created, Blob Deleted
6. Optionally filter by subject prefix/suffix (e.g., .parquet)
"""

import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

# Thread pool for async processing (don't block Event Grid)
_executor = ThreadPoolExecutor(max_workers=3)


@method_decorator(csrf_exempt, name='dispatch')
class ADLSEventListenerView(View):
    """
    Webhook endpoint for Azure Event Grid ADLS events.
    
    Handles:
    - Event Grid subscription validation
    - Blob created events -> Migrate to ClickHouse
    - Blob deleted events -> Remove from ClickHouse
    """

    def post(self, request):
        """Handle incoming Event Grid events."""
        try:
            # Log request headers for debugging
            logger.debug(f"[ADLS LISTENER] Request headers: {dict(request.headers)}")
            logger.debug(f"[ADLS LISTENER] Content-Type: {request.content_type}")
            
            body = request.body.decode('utf-8')
            logger.debug(f"[ADLS LISTENER] Request body (first 500 chars): {body[:500]}")
            
            # Handle empty body (ngrok warning page might cause this)
            if not body or len(body.strip()) == 0:
                logger.warning("[ADLS LISTENER] Empty request body received - might be ngrok warning page")
                return JsonResponse({
                    'error': 'Empty request body',
                    'hint': 'If using ngrok, ensure you bypass the warning page or use ngrok with --request-header option'
                }, status=400)
            
            events = json.loads(body)
            
            if not isinstance(events, list):
                events = [events]
            
            results = []
            for event in events:
                event_type = event.get('eventType', '')
                
                # Handle Event Grid subscription validation
                if event_type == 'Microsoft.EventGrid.SubscriptionValidationEvent':
                    logger.info("[ADLS LISTENER] Processing validation event")
                    return self._handle_validation(event)
                
                # Process blob events
                result = self._process_blob_event(event)
                results.append(result)
            
            return JsonResponse({
                'status': 'success',
                'processed': len(results),
                'results': results
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"[ADLS LISTENER] Invalid JSON in request body: {e}")
            logger.error(f"[ADLS LISTENER] Body content: {request.body.decode('utf-8')[:500]}")
            return JsonResponse({
                'error': 'Invalid JSON',
                'details': str(e)
            }, status=400)
        except Exception as e:
            logger.exception(f"[ADLS LISTENER] Error processing ADLS event: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    def _handle_validation(self, event):
        """Handle Event Grid subscription validation handshake."""
        validation_code = event.get('data', {}).get('validationCode')
        
        if not validation_code:
            logger.error("[ADLS LISTENER] Validation event missing validationCode")
            logger.error(f"[ADLS LISTENER] Event data: {event}")
            return JsonResponse({'error': 'Missing validationCode'}, status=400)
        
        logger.info(f"[ADLS LISTENER] Subscription validation request received")
        logger.info(f"[ADLS LISTENER] Validation Code: {validation_code}")
        print(f"\n{'='*60}")
        print(f"✅ EVENT GRID VALIDATION REQUEST RECEIVED")
        print(f"   Validation Code: {validation_code}")
        print(f"{'='*60}\n")
        
        # Return validation response
        response = JsonResponse({'validationResponse': validation_code})
        response['Content-Type'] = 'application/json'
        return response
    
    def get(self, request):
        """Handle GET requests (useful for testing and ngrok bypass)."""
        return JsonResponse({
            'status': 'active',
            'service': 'adls-event-listener',
            'endpoint': '/api/v1/adls-listener/events/',
            'note': 'This endpoint expects POST requests from Azure Event Grid'
        })

    def _process_blob_event(self, event) -> dict:
        """Process and handle blob storage events."""
        event_type = event.get('eventType', 'Unknown')
        data = event.get('data', {})
        subject = event.get('subject', '')
        
        # Parse blob info
        container, blob_path = self._parse_blob_subject(subject)
        
        # Check if it's a parquet file
        is_parquet = blob_path.lower().endswith('.parquet') if blob_path else False
        
        event_info = {
            'event_id': event.get('id'),
            'event_type': event_type,
            'event_time': event.get('eventTime'),
            'container': container,
            'blob_path': blob_path,
            'url': data.get('url'),
            'content_type': data.get('contentType'),
            'content_length': data.get('contentLength'),
            'is_parquet': is_parquet
        }
        
        # Log the event
        self._log_event(event_type, event_info)
        
        # Process parquet files
        if is_parquet:
            return self._handle_parquet_event(event_type, container, blob_path, event_info)
        
        return {'status': 'skipped', 'reason': 'not a parquet file'}

    def _parse_blob_subject(self, subject: str) -> tuple:
        """Parse container and blob path from Event Grid subject."""
        try:
            # Subject format: /blobServices/default/containers/{container}/blobs/{blob-path}
            parts = subject.split('/containers/')
            if len(parts) > 1:
                rest = parts[1]
                container_and_blob = rest.split('/blobs/')
                container = container_and_blob[0]
                blob_path = container_and_blob[1] if len(container_and_blob) > 1 else ''
                return container, blob_path
        except Exception as e:
            logger.warning(f"Could not parse blob subject: {subject}, error: {e}")
        
        return None, None

    def _log_event(self, event_type: str, info: dict):
        """Log event with detailed information."""
        timestamp = datetime.now().isoformat()
        separator = "=" * 70
        
        action_map = {
            'Microsoft.Storage.BlobCreated': ('NEW FILE CREATED', '📁'),
            'Microsoft.Storage.BlobDeleted': ('FILE DELETED', '🗑️'),
            'Microsoft.Storage.BlobRenamed': ('FILE RENAMED', '✏️'),
        }
        
        action, emoji = action_map.get(event_type, (event_type, '📌'))
        
        log_message = f"""
{separator}
{emoji} ADLS EVENT: {action}
{separator}
Timestamp:        {timestamp}
Event ID:         {info.get('event_id')}
Event Time:       {info.get('event_time')}
Container:        {info.get('container')}
Blob Path:        {info.get('blob_path')}
Is Parquet:       {info.get('is_parquet')}
Content Length:   {info.get('content_length')} bytes
{separator}
"""
        logger.info(log_message)
        print(log_message)

    def _handle_parquet_event(self, event_type: str, container: str,
                               blob_path: str, event_info: dict) -> dict:
        """
        Handle parquet file events - trigger migration to ClickHouse.

        Uses async processing to not block Event Grid (which has timeout limits).
        Each request gets its own service instance to avoid ClickHouse concurrency issues.
        """
        from infrastructure.services.adls_event_migration_service import get_event_migration_service

        service = None
        try:
            # Create new service instance for this request (avoids ClickHouse concurrency issues)
            service = get_event_migration_service()

            if event_type == 'Microsoft.Storage.BlobCreated':
                # Process file creation/update
                logger.info(f"[ADLS LISTENER] Triggering migration for: {blob_path}")

                # Run migration (can be async for large files)
                result = service.process_blob_created(container, blob_path, event_info)

                return {
                    'status': 'processed',
                    'action': 'migrate',
                    'blob_path': blob_path,
                    'success': result.get('success'),
                    'rows_imported': result.get('rows_imported', 0),
                    'clickhouse_table': result.get('clickhouse_table'),
                    'error': result.get('error')
                }

            elif event_type == 'Microsoft.Storage.BlobDeleted':
                # Process file deletion
                logger.info(f"[ADLS LISTENER] Triggering deletion for: {blob_path}")

                result = service.process_blob_deleted(container, blob_path, event_info)

                return {
                    'status': 'processed',
                    'action': 'delete',
                    'blob_path': blob_path,
                    'success': result.get('success'),
                    'rows_deleted': result.get('rows_deleted', 0),
                    'clickhouse_table': result.get('clickhouse_table'),
                    'error': result.get('error')
                }

            return {'status': 'skipped', 'reason': f'unhandled event type: {event_type}'}

        except Exception as e:
            logger.error(f"[ADLS LISTENER] Error handling parquet event: {e}", exc_info=True)
            return {
                'status': 'error',
                'action': event_type,
                'blob_path': blob_path,
                'error': str(e)
            }
        finally:
            # Always close the service to release ClickHouse connection
            if service:
                try:
                    service.close()
                except Exception as e:
                    logger.warning(f"[ADLS LISTENER] Error closing service: {e}")


class ADLSEventHealthView(View):
    """Health check endpoint for the ADLS listener."""

    def get(self, request):
        # Check if migration service can be initialized
        service_status = 'unknown'
        service = None
        try:
            from infrastructure.services.adls_event_migration_service import get_event_migration_service
            service = get_event_migration_service()
            service_status = 'healthy'
        except Exception as e:
            service_status = f'error: {str(e)}'
        finally:
            if service:
                try:
                    service.close()
                except Exception:
                    pass

        return JsonResponse({
            'status': 'healthy',
            'service': 'adls-event-listener',
            'migration_service': service_status,
            'timestamp': datetime.now().isoformat()
        })
