from typing import Optional, List, Dict, Tuple
from datetime import datetime
import re


class QueryOptimizer:
    """
    Query optimization helper for predicate pushdown and performance enhancements.
    Handles date normalization, column pruning, and query optimization strategies.
    """
    
    @staticmethod
    def normalize_date_bounds(from_date: Optional[str], to_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Normalize date bounds for optimal query performance.
        Accepts 'YYYY-MM-DD' or full timestamps.
        Returns (from_ts_str, to_ts_str) where to_ts is inclusive end-of-day if only a date was given.
        """
        fmt_date = "%Y-%m-%d"
        
        def _is_date_only(s: str) -> bool:
            try:
                datetime.strptime(s, fmt_date)
                return True
            except:
                return False

        from_ts = None
        to_ts = None
        
        if from_date:
            from_ts = f"{from_date} 00:00:00" if _is_date_only(from_date) else from_date
        if to_date:
            # Inclusive end-of-day when only date given
            to_ts = f"{to_date} 23:59:59.999999" if _is_date_only(to_date) else to_date
            
        return from_ts, to_ts
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """
        Validate date string format for security and correctness.
        """
        if not date_str:
            return True  # Optional parameter
            
        # Check for basic YYYY-MM-DD format
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str.strip()):
            return False
            
        try:
            year, month, day = map(int, date_str.split('-'))
            if year < 2000 or year > 2030 or month < 1 or month > 12 or day < 1 or day > 31:
                return False
            return True
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_column_names(columns: List[str]) -> List[str]:
        """
        Sanitize column names to prevent SQL injection and ensure compatibility.
        """
        sanitized = []
        for col in columns:
            # Remove any potentially dangerous characters
            sanitized_col = re.sub(r'[^\w\-_]', '', col.strip())
            if sanitized_col:  # Only add non-empty columns
                sanitized.append(sanitized_col)
        return sanitized
    
    @staticmethod
    def build_where_clause(
        from_date: Optional[str],
        to_date: Optional[str],
        date_column: str = "Datetime",
        additional_conditions: Optional[List[str]] = None
    ) -> str:
        """
        Build optimized WHERE clause for SQL queries.
        """
        conditions = []
        
        # Date filtering conditions
        from_ts, to_ts = QueryOptimizer.normalize_date_bounds(from_date, to_date)
        
        if from_ts:
            conditions.append(f"`{date_column}` >= timestamp('{from_ts}')")
        if to_ts:
            conditions.append(f"`{date_column}` <= timestamp('{to_ts}')")
        
        # Additional conditions
        if additional_conditions:
            conditions.extend(additional_conditions)
        
        return f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    @staticmethod
    def build_select_clause(columns: Optional[List[str]]) -> str:
        """
        Build optimized SELECT clause with column pruning.
        """
        if not columns:
            return "*"
        
        # Sanitize and quote column names
        sanitized_columns = QueryOptimizer.sanitize_column_names(columns)
        return ", ".join([f"`{col}`" for col in sanitized_columns])
    
    @staticmethod
    def estimate_query_complexity(
        columns: Optional[List[str]],
        from_date: Optional[str],
        to_date: Optional[str],
        limit: Optional[int]
    ) -> Dict[str, any]:
        """
        Estimate query complexity and suggest optimizations.
        """
        complexity = {
            "score": 0,  # 0-100, higher is more complex
            "optimizations": [],
            "estimated_time": "fast"  # fast, medium, slow
        }
        
        # Column pruning assessment
        if not columns:
            complexity["score"] += 20
            complexity["optimizations"].append("Consider specifying specific columns to reduce I/O")
        else:
            complexity["score"] += max(0, len(columns) - 10) * 2  # Penalty for many columns
        
        # Date range assessment
        if from_date and to_date:
            try:
                from_dt = datetime.strptime(from_date.split()[0], "%Y-%m-%d")
                to_dt = datetime.strptime(to_date.split()[0], "%Y-%m-%d")
                days_diff = (to_dt - from_dt).days
                
                if days_diff > 30:
                    complexity["score"] += 30
                    complexity["optimizations"].append("Consider reducing date range for better performance")
                elif days_diff > 7:
                    complexity["score"] += 15
            except:
                complexity["score"] += 10
        else:
            complexity["score"] += 40
            complexity["optimizations"].append("Specify date range to enable predicate pushdown")
        
        # Limit assessment
        if not limit:
            complexity["score"] += 20
            complexity["optimizations"].append("Consider adding LIMIT for faster response")
        elif limit > 10000:
            complexity["score"] += 15
            complexity["optimizations"].append("Large result set - consider pagination")
        
        # Determine estimated time
        if complexity["score"] > 60:
            complexity["estimated_time"] = "slow"
        elif complexity["score"] > 30:
            complexity["estimated_time"] = "medium"
        else:
            complexity["estimated_time"] = "fast"
        
        return complexity
    
    @staticmethod
    def suggest_partition_strategy(
        file_count: int,
        estimated_size_mb: float,
        date_range_days: Optional[int]
    ) -> Dict[str, any]:
        """
        Suggest optimal partitioning strategy based on data characteristics.
        """
        strategy = {
            "recommended_partitions": 2,
            "coalesce": True,
            "cache": False,
            "reasoning": []
        }
        
        # File count based partitioning
        if file_count > 10:
            strategy["recommended_partitions"] = min(4, file_count // 3)
            strategy["reasoning"].append(f"Multiple files ({file_count}) benefit from parallel processing")
        
        # Size based partitioning
        if estimated_size_mb > 100:
            strategy["recommended_partitions"] = max(strategy["recommended_partitions"], 4)
            strategy["reasoning"].append(f"Large dataset ({estimated_size_mb}MB) needs more partitions")
        elif estimated_size_mb < 10:
            strategy["recommended_partitions"] = 1
            strategy["coalesce"] = True
            strategy["reasoning"].append("Small dataset benefits from single partition")
        
        # Date range based strategy
        if date_range_days and date_range_days > 7:
            strategy["cache"] = True
            strategy["reasoning"].append("Large date range benefits from caching")
        
        return strategy
    
    @staticmethod
    def optimize_sql_query(
        base_query: str,
        complexity_assessment: Dict[str, any]
    ) -> str:
        """
        Apply SQL query optimizations based on complexity assessment.
        """
        optimized_query = base_query
        
        # Add query hints based on complexity
        if complexity_assessment["estimated_time"] == "slow":
            # Add hints for slow queries
            optimized_query = f"/* HINT: SLOW_QUERY */ {optimized_query}"
        
        # Ensure proper ordering for performance
        if "ORDER BY" not in optimized_query and "LIMIT" in optimized_query:
            # Add default ordering before LIMIT for consistency
            limit_pos = optimized_query.find("LIMIT")
            optimized_query = (
                optimized_query[:limit_pos] + 
                "ORDER BY `Datetime` DESC " + 
                optimized_query[limit_pos:]
            )
        
        return optimized_query.strip()
    
    @staticmethod
    def get_performance_recommendations(
        siteName: str,
        tableName: str,
        from_date: Optional[str],
        to_date: Optional[str],
        columns: Optional[List[str]]
    ) -> List[str]:
        """
        Get performance recommendations for the specific query.
        """
        recommendations = []
        
        # Column recommendations
        if not columns:
            recommendations.append("Specify only required columns to reduce data transfer")
        elif len(columns) > 20:
            recommendations.append("Consider reducing the number of columns for better performance")
        
        # Date range recommendations
        if not from_date or not to_date:
            recommendations.append("Specify date range to enable predicate pushdown optimization")
        else:
            try:
                from_dt = datetime.strptime(from_date.split()[0], "%Y-%m-%d")
                to_dt = datetime.strptime(to_date.split()[0], "%Y-%m-%d")
                days_diff = (to_dt - from_dt).days
                
                if days_diff > 30:
                    recommendations.append("Consider breaking large date ranges into smaller chunks")
                if days_diff > 90:
                    recommendations.append("Very large date range - consider using data aggregation")
            except:
                pass
        
        # Table-specific recommendations
        if "chemicals" in tableName.lower():
            recommendations.append("Chemical data tables benefit from column filtering")
        
        return recommendations
