"""
Rack Precompute Service - Background service to precompute and cache rack data
Runs periodically to warm up caches and reduce API response times.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from infrastructure.services.cache_service import CacheService
from infrastructure.services.analysis.analysis_base_service import AnalysisService
from config.redis_cache_config import CacheConfig

logger = logging.getLogger(__name__)


class RackPrecomputeService:
    """
    Background service to precompute rack data for faster API responses.
    Automatically discovers sites and tables, then precomputes rack data.
    """
    
    def __init__(self):
        self.cache_service = CacheService()
        self.analysis_service = AnalysisService()
        self._running = False
        self._thread = None
        
        # Configuration
        self.precompute_interval = 1800  # 30 minutes
        self.max_concurrent_sites = 2   # Conservative for background processing
        self.max_tables_per_site = 5    # Limit to most important tables
        
        logger.info("RackPrecomputeService initialized")
    
    def start_background_precompute(self):
        """Start background precompute thread"""
        if self._running:
            logger.warning("Background precompute already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._background_loop, daemon=True)
        self._thread.start()
        logger.info("Started background rack precompute service")
    
    def stop_background_precompute(self):
        """Stop background precompute thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=30)
        logger.info("Stopped background rack precompute service")
    
    def _background_loop(self):
        """Background loop for precomputing rack data"""
        while self._running:
            try:
                logger.info("Starting background rack precompute cycle")
                start_time = time.time()
                
                # Precompute racks for discovered sites/tables
                precomputed_count = self._precompute_popular_racks()
                
                cycle_time = time.time() - start_time
                logger.info(f"Background precompute cycle completed: {precomputed_count} entries in {cycle_time:.2f}s")
                
                # Wait for next cycle
                time.sleep(self.precompute_interval)
                
            except Exception as e:
                logger.error(f"Error in background precompute cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retry on error
    
    def _precompute_popular_racks(self) -> int:
        """
        Precompute rack data for popular site/table combinations.
        Returns number of entries precomputed.
        """
        try:
            # Step 1: Discover available sites
            sites = self._discover_sites()
            if not sites:
                logger.warning("No sites discovered for precompute")
                return 0
            
            logger.info(f"Discovered {len(sites)} sites for precompute")
            
            precomputed_count = 0
            
            # Step 2: Process sites in parallel
            with ThreadPoolExecutor(max_workers=self.max_concurrent_sites) as executor:
                future_to_site = {
                    executor.submit(self._precompute_site_racks, site): site
                    for site in sites[:10]  # Limit to first 10 sites
                }
                
                for future in as_completed(future_to_site, timeout=300):  # 5 minute timeout
                    site = future_to_site[future]
                    try:
                        site_precomputed = future.result()
                        precomputed_count += site_precomputed
                        logger.info(f"Precomputed {site_precomputed} entries for site {site}")
                    except Exception as e:
                        logger.error(f"Error precomputing site {site}: {e}")
            
            return precomputed_count
            
        except Exception as e:
            logger.error(f"Error in popular racks precompute: {e}")
            return 0
    
    def _discover_sites(self) -> List[str]:
        """Discover available sites from cache or directory listing"""
        try:
            # Try to get sites from cache first
            cached_sites = self.cache_service.get("all_sites_directories", prefix="directory_data")
            if cached_sites and cached_sites.get("sites"):
                return [site["name"] for site in cached_sites["sites"]]
            
            # Fallback to direct discovery
            directories = self.analysis_service.get_all_directories()
            return [site["name"] for site in directories] if directories else []
            
        except Exception as e:
            logger.error(f"Error discovering sites: {e}")
            return []
    
    def _precompute_site_racks(self, site_id: str) -> int:
        """
        Precompute rack data for a single site.
        Returns number of table entries precomputed.
        """
        try:
            # Get tables for this site
            tables = self._discover_site_tables(site_id)
            if not tables:
                return 0
            
            # Limit to most important tables (by name patterns)
            priority_tables = self._prioritize_tables(tables)[:self.max_tables_per_site]
            
            precomputed = 0
            
            for table_name in priority_tables:
                try:
                    # Check if already cached
                    table_cache_key = f"table_racks_{site_id}_{table_name}"
                    if self.cache_service.get(table_cache_key, prefix="rack_data"):
                        continue  # Already cached
                    
                    # Precompute rack data
                    logger.debug(f"Precomputing racks for {site_id}/{table_name}")
                    racks_data = self.analysis_service.get_unique_racks(site_id, [table_name])
                    table_racks = racks_data.get("racks", [])
                    
                    if table_racks:
                        # Cache the results (45 minute TTL for precomputed data)
                        self.cache_service.set(
                            table_cache_key,
                            table_racks,
                            ttl=2700,  # 45 minutes
                            prefix="rack_data"
                        )
                        precomputed += 1
                        logger.debug(f"Precomputed {len(table_racks)} racks for {site_id}/{table_name}")
                    
                except Exception as e:
                    logger.warning(f"Error precomputing {site_id}/{table_name}: {e}")
                    continue
            
            return precomputed
            
        except Exception as e:
            logger.error(f"Error precomputing site {site_id}: {e}")
            return 0
    
    def _discover_site_tables(self, site_id: str) -> List[str]:
        """Discover tables for a site"""
        try:
            # Try cache first
            cache_key = f"tables_site_{site_id}"
            cached_tables = self.cache_service.get(cache_key, prefix="directory_data")
            if cached_tables:
                return [table["tableName"] for table in cached_tables]
            
            # Fallback to direct discovery
            subdirectories = self.analysis_service.get_subdirectories(site_id)
            return [table["name"] for table in subdirectories] if subdirectories else []
            
        except Exception as e:
            logger.error(f"Error discovering tables for site {site_id}: {e}")
            return []
    
    def _prioritize_tables(self, tables: List[str]) -> List[str]:
        """
        Prioritize tables based on naming patterns (most likely to contain racks).
        """
        priority_patterns = [
            'normalization',
            'chemical',
            'rack',
            'equipment',
            'unit',
            'station'
        ]
        
        # Score tables based on priority patterns
        scored_tables = []
        for table in tables:
            score = 0
            table_lower = table.lower()
            
            for i, pattern in enumerate(priority_patterns):
                if pattern in table_lower:
                    score += (len(priority_patterns) - i)  # Higher score for earlier patterns
            
            scored_tables.append((table, score))
        
        # Sort by score (descending) and return table names
        scored_tables.sort(key=lambda x: x[1], reverse=True)
        return [table for table, score in scored_tables]
    
    def force_precompute_site(self, site_id: str, table_ids: List[str] = None) -> Dict:
        """
        Force precompute rack data for a specific site (manual trigger).
        
        Args:
            site_id: Site identifier
            table_ids: Optional list of specific tables, otherwise discovers all
            
        Returns:
            Dict with precompute results
        """
        try:
            start_time = time.time()
            logger.info(f"Force precomputing racks for site {site_id}")
            
            if not table_ids:
                table_ids = self._discover_site_tables(site_id)
            
            if not table_ids:
                return {"success": False, "message": f"No tables found for site {site_id}"}
            
            precomputed = 0
            failed = 0
            
            for table_name in table_ids:
                try:
                    racks_data = self.analysis_service.get_unique_racks(site_id, [table_name])
                    table_racks = racks_data.get("racks", [])
                    
                    if table_racks:
                        table_cache_key = f"table_racks_{site_id}_{table_name}"
                        self.cache_service.set(
                            table_cache_key,
                            table_racks,
                            ttl=3600,  # 1 hour for manual precompute
                            prefix="rack_data"
                        )
                        precomputed += 1
                    
                except Exception as e:
                    logger.error(f"Error in force precompute {site_id}/{table_name}: {e}")
                    failed += 1
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "message": f"Force precompute completed for {site_id}",
                "precomputed": precomputed,
                "failed": failed,
                "processing_time_seconds": round(processing_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Error in force precompute for {site_id}: {e}")
            return {"success": False, "message": str(e)}


# Global precompute service instance
_precompute_service = None

def get_rack_precompute_service() -> RackPrecomputeService:
    """Get the global rack precompute service instance"""
    global _precompute_service
    if _precompute_service is None:
        _precompute_service = RackPrecomputeService()
    return _precompute_service
