"""
Telemetry aggregation utility for cloudmesh-ai.
Provides tools to analyze and summarize telemetry data from various backends.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from collections import defaultdict

class TelemetryAggregator:
    """
    Analyzes telemetry records to provide summaries and statistics.
    Supports loading data from both JSONL files and SQLite databases.
    """

    def __init__(self, source: Union[str, Path]):
        """
        Initialize the TelemetryAggregator.

        Args:
            source: Path to the telemetry source (JSONL file or SQLite .db file).
        """
        self.source = Path(source).expanduser()
        self.records: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self) -> None:
        """Detects source type and loads records into memory.
        """
        if self.source.suffix == ".db":
            self._load_from_sqlite()
        else:
            self._load_from_jsonl()

    def _load_from_jsonl(self) -> None:
        """Loads records from a JSONL file.
        """
        try:
            if not self.source.exists():
                return
            with open(self.source, "r") as f:
                for line in f:
                    if line.strip():
                        self.records.append(json.loads(line))
        except Exception as e:
            print(f"Error loading JSONL telemetry: {e}")

    def _load_from_sqlite(self) -> None:
        """Loads records from a SQLite database.
        """
        try:
            with sqlite3.connect(self.source) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM telemetry")
                for row in cursor:
                    record = dict(row)
                    # Convert JSON strings back to dicts
                    record["metrics"] = json.loads(record["metrics"]) if isinstance(record["metrics"], str) else record["metrics"]
                    record["system"] = json.loads(record["system"]) if isinstance(record["system"], str) else record["system"]
                    self.records.append(record)
        except Exception as e:
            print(f"Error loading SQLite telemetry: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Calculates a high-level summary of the telemetry data.

        Returns:
            A dictionary containing total records, success rate, 
            status distribution, and command distribution.
        """
        if not self.records:
            return {"error": "No records found"}

        total = len(self.records)
        status_counts = defaultdict(int)
        command_counts = defaultdict(int)
        
        for r in self.records:
            status_counts[r.get("status", "unknown")] += 1
            command_counts[r.get("command", "unknown")] += 1

        success_count = status_counts.get("completed", 0)
        
        return {
            "total_records": total,
            "success_rate": f"{(success_count / total) * 100:.2f}%",
            "status_distribution": dict(status_counts),
            "command_distribution": dict(command_counts),
        }

    def aggregate_metric(self, metric_name: str) -> Dict[str, Any]:
        """
        Calculates average, min, and max for a specific metric across all records.

        Args:
            metric_name: The key of the metric to aggregate from the 'metrics' dictionary.

        Returns:
            A dictionary containing the count, average, minimum, and maximum values.
        """
        values = []
        for r in self.records:
            metrics = r.get("metrics", {})
            if metric_name in metrics:
                val = metrics[metric_name]
                if isinstance(val, (int, float)):
                    values.append(val)

        if not values:
            return {"metric": metric_name, "status": "no data"}

        return {
            "metric": metric_name,
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

if __name__ == "__main__":
    # Simple test if run directly
    import sys
    if len(sys.argv) > 1:
        agg = TelemetryAggregator(sys.argv[1])
        print(json.dumps(agg.get_summary(), indent=4))
    else:
        print("Usage: python aggregation.py <telemetry_file_or_db>")