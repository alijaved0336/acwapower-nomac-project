import math
from constants import Dash032Config
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository


class Dash032Service:
    def __init__(self):
        self.clickhouse_repository = ClickHouseRepository()

    def __del__(self):
        """Cleanup repository connection when service is destroyed"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def sanitize_value(value):
        """
        Sanitize numeric values to ensure JSON compliance.
        Converts inf, -inf, and NaN to None.
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            # Check for inf, -inf, or NaN
            if math.isinf(value) or math.isnan(value):
                return None

        return value

    def get_normalized_data_pass_1(self, site_id, from_date, to_date, norm_pass):

        if site_id not in ["jubail-jazlah", "Jubail-Jazlah", 'JUBAIL-JAZLAH']:
            columns = Dash032Config.SITE_TABLE_MAPPINGS.get(site_id.lower()).get("columns")
        else:
            columns = Dash032Config.SITE_TABLE_MAPPINGS.get(site_id.lower()).get("columns").get(norm_pass)

        print("columns: ", columns)
        column_name = []
        for column in columns:
            column_name.append(column["column_name"])

        print("column_name: ", column_name)
        data = None
        where_condition = []
        query_params = {}
        if from_date and to_date:
            where_condition = ["`DateTime` >= {from_date:String}",
                               "`DateTime` <= {to_date:String}"]
            query_params = {
                "from_date": from_date,
                "to_date": to_date,
            }
        table_name = Dash032Config.SITE_TABLE_MAPPINGS.get(site_id.lower()).get("table").get(norm_pass)

        if site_id not in ["UAQ", "uaq"]:
            print("tables name : ", table_name)
            data = self.clickhouse_repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=column_name[1:],
                datetime_column=column_name[0],
                where_conditions=where_condition if where_condition else [],
                query_params=query_params if query_params else {},
            )
            print("Data: ", data)
            response = self.format_response(data.get("result_rows"), column_name)
            print("Response : ", response)
            response["data_availability_for_given_date"] = data.get("data_availability_for_given_date")
            response["from_date"] = data.get("from_date")
            response["to_date"] = data.get("to_date")
            return response
        else:

            table_name_uaq = table_name.get("stream_1", None)
            print("table_name: ", table_name_uaq)
            stream_1_data = self.clickhouse_repository.get_column_data_for_table(
                clickhouse_table_name=table_name_uaq,
                column_names=column_name[1:],
                datetime_column=column_name[0],
                where_conditions=where_condition if where_condition else [],
                query_params=query_params if query_params else {})
            formatted_stream_1_data = self.format_response(stream_1_data.get("result_rows"), column_name)
            formatted_stream_1_data["data_availability_for_given_date"] = stream_1_data.get("data_availability_for_given_date")
            formatted_stream_1_data["from_date"] = formatted_stream_1_data.get("from_date")
            formatted_stream_1_data["to_date"] = formatted_stream_1_data.get("to_date")

            table_name_uaq = table_name.get("stream_2", None)
            stream_2_data = self.clickhouse_repository.get_column_data_for_table(
                clickhouse_table_name=table_name_uaq,
                column_names=column_name[1:],
                datetime_column=column_name[0],
                where_conditions=where_condition if where_condition else [],
                query_params=query_params if query_params else {})
            formatted_stream_2_data = self.format_response(stream_2_data.get("result_rows"), column_name)
            formatted_stream_2_data["data_availability_for_given_date"] = formatted_stream_2_data.get("data_availability_for_given_date")
            formatted_stream_2_data["from_date"] = formatted_stream_2_data.get("from_date")
            formatted_stream_2_data["to_date"] = formatted_stream_2_data.get("to_date")

            table_name_uaq = table_name.get("stream_3", None)
            stream_3_data = self.clickhouse_repository.get_column_data_for_table(
                clickhouse_table_name=table_name_uaq,
                column_names=column_name[1:],
                datetime_column=column_name[0],
                where_conditions=where_condition if where_condition else [],
                query_params=query_params if query_params else {})
            formatted_stream_3_data = self.format_response(stream_3_data.get("result_rows"), column_name)
            formatted_stream_3_data["data_availability_for_given_date"] = formatted_stream_3_data.get("data_availability_for_given_date")
            formatted_stream_3_data["from_date"] = formatted_stream_3_data.get("from_date")
            formatted_stream_3_data["to_date"] = formatted_stream_3_data.get("to_date")
            response = {
                "stream_1": formatted_stream_1_data,
                "stream_2": formatted_stream_2_data,
                "stream_3": formatted_stream_3_data,
            }
            if not stream_1_data or not stream_2_data or not stream_3_data:
                return "No Data found!"

            return response

    def format_response(self, data, column_name):
        # Group data by RACK
        rack_grouped_data = {}

        # Store all records for calculating averages
        all_records = []

        for value_list in data:
            temp = {}
            for idx, col in enumerate(column_name):
                # Sanitize values as they're being added
                temp[column_name[idx]] = self.sanitize_value(value_list[idx])

            rack = temp.get("RACK") or temp.get("Rack")

            if not rack or rack == 'NaN':
                continue

            # If RACK is None, use "Overall" or "ALL" as key
            rack_key = rack

            # Initialize rack group if it doesn't exist
            if rack_key not in rack_grouped_data:
                rack_grouped_data[rack_key] = []

            # Add this record to the appropriate rack group
            rack_grouped_data[rack_key].append(temp)

            # Store for average calculation
            all_records.append(temp)

        print("rack_grouped_data: ", rack_grouped_data)

        # Calculate averages at each datetime instance
        overall = self.calculate_averages_by_datetime(all_records)
        return {
            "overall": overall,
            "separate": rack_grouped_data,
        }

    def calculate_averages_by_datetime(self, records):
        """
        Calculate averages of metrics at each datetime instance
        """
        # Group records by DateTime
        datetime_groups = {}

        for record in records:
            dt = record.get("DateTime")
            if dt is None:
                continue

            if dt not in datetime_groups:
                datetime_groups[dt] = []

            datetime_groups[dt].append(record)

        # Calculate averages for each datetime
        graph_data = []
        metric_columns = [
            "Nominal_Recovery",
            "Overall_DP_Normalized_BAR",
            "Overall_Perm_Flow_Normalized",
            "Overall_Salt_Passage_Normalized"
        ]

        for dt, group in sorted(datetime_groups.items()):
            avg_record = {"DateTime": dt}

            for metric in metric_columns:
                # Filter out None values and calculate average
                values = [r.get(metric) for r in group if r.get(metric) is not None]

                if values:
                    avg_value = sum(values) / len(values)
                    # Sanitize the calculated average
                    avg_record[metric] = self.sanitize_value(avg_value)
                else:
                    avg_record[metric] = None

            graph_data.append(avg_record)

        return graph_data

    def stream_filter(self, site_id):
        if site_id.lower() == "uaq":
            return [
                {"id": "stream_1", "name": "Stream 1"},
                {"id": "stream_2", "name": "Stream 2"},
                {"id": "stream_3", "name": "Stream 3"},
            ]
        else:
            return [
                {"id": "stream_1", "name": "Stream 1"},
            ]