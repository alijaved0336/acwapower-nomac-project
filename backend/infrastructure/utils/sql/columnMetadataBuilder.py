from typing import List, Dict


class ColumnMetadataBuilder:
    """
    Builds column metadata from schema and sample data.
    """
    
    def build_column_metadata_from_schema(self, schema_info: List[Dict], sample_data: List, table_id: str) -> List[Dict]:
        """
        Build column metadata from schema dictionary and sample data.
        """
        columns = []
        
        for col_meta in schema_info:
            col_name = col_meta["col_name"]
            col_type = col_meta["data_type"]
            
            # Extract sample values
            sample_values = []
            for sample_row in sample_data[:10]:
                try:
                    if hasattr(sample_row, col_name):
                        value = getattr(sample_row, col_name)
                    elif isinstance(sample_row, dict) and col_name in sample_row:
                        value = sample_row[col_name]
                    else:
                        value = sample_row[col_name] if col_name in sample_row else None
                    
                    if value is not None:
                        sample_values.append(str(value))
                    
                    if len(sample_values) >= 5:
                        break
                except Exception:
                    continue
            
            columns.append({
                "name": col_name,
                "type": col_type,
                "nullable": col_meta.get("nullable", True),
                "dataSource": sample_values,
                "table": table_id
            })
        
        return columns
    
    def build_column_metadata(self, schema_info: List, sample_data: List, table_id: str) -> List[Dict]:
        """
        Build column metadata from schema and sample data.
        """
        columns = []
        
        for col_info in schema_info:
            col_name = col_info.col_name
            col_type = col_info.data_type
            
            # Extract sample values from first few rows
            sample_values = []
            for sample_row in sample_data[:10]:
                try:
                    if hasattr(sample_row, col_name):
                        value = getattr(sample_row, col_name)
                        if value is not None:
                            sample_values.append(str(value))
                    
                    if len(sample_values) >= 5:
                        break
                except Exception:
                    continue
            
            columns.append({
                "name": col_name,
                "type": col_type,
                "nullable": col_info.comment == "null" if hasattr(col_info, 'comment') else True,
                "dataSource": sample_values,
                "table": table_id
            })
        
        return columns
