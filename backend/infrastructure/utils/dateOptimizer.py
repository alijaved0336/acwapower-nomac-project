from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict


class DateOptimizer:
    """
    Production-ready date optimization for API performance.
    """
    
    def __init__(self):
        pass
    
    def get_performance_optimized_range(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        default_days_ago: int = 3
    ) -> Tuple[Optional[str], Optional[str], Dict]:
        """
        Get optimized date range for production performance.
        """
        metadata = {
            "applied_default": False,
            "optimized": False,
            "cache_used": False,
            "performance_mode": True
        }
        
        # If both dates provided, use as-is for best performance
        if from_date and to_date:
            return from_date, to_date, metadata
        
        # Apply intelligent defaults for better performance
        current_time = datetime.now(timezone.utc)
        
        if not from_date and not to_date:
            # No dates provided - use recent data for fast response
            to_date_dt = current_time
            from_date_dt = current_time - timedelta(days=default_days_ago)
            metadata["applied_default"] = True
        elif not from_date:
            # Only to_date provided
            to_date_dt = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            from_date_dt = to_date_dt - timedelta(days=default_days_ago)
            metadata["applied_default"] = True
        else:
            # Only from_date provided
            from_date_dt = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            to_date_dt = from_date_dt + timedelta(days=default_days_ago)
            metadata["applied_default"] = True
        
        optimized_from = from_date or from_date_dt.strftime("%Y-%m-%d")
        optimized_to = to_date or to_date_dt.strftime("%Y-%m-%d")
        
        return optimized_from, optimized_to, metadata
    
    def get_query_optimization_hints(self, from_date: Optional[str], to_date: Optional[str]) -> Dict:
        """
        Get query optimization hints based on date range.
        """
        if not from_date or not to_date:
            return {
                "days_span": 3,
                "query_complexity": "low",
                "recommended_method": "direct_sql",
                "partition_strategy": "single",
                "caching_recommended": False
            }
        
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
            days_span = (to_dt - from_dt).days
            
            if days_span <= 7:
                complexity = "low"
                method = "direct_sql"
                strategy = "single"
            elif days_span <= 30:
                complexity = "medium"
                method = "sparksql"
                strategy = "weekly"
            else:
                complexity = "high"
                method = "pyarrow_parallel"
                strategy = "monthly"
            
            return {
                "days_span": days_span,
                "query_complexity": complexity,
                "recommended_method": method,
                "partition_strategy": strategy,
                "caching_recommended": days_span > 7
            }
            
        except Exception:
            return {
                "days_span": 7,
                "query_complexity": "low",
                "recommended_method": "direct_sql",
                "partition_strategy": "single",
                "caching_recommended": False
            }