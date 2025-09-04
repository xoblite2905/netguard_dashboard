# backend/app/services/alert_service.py
import os
from elasticsearch import Elasticsearch

# Use the environment variable for the ES host, defaulting to localhost
es_host = os.getenv("ELASTICSEARCH_URI", "http://elasticsearch:9200")
es_client = Elasticsearch(es_host)

def get_latest_alerts(limit: int = 500):
    """
    Queries Elasticsearch for the latest Suricata alerts.
    """
    # The index name we discovered from our investigation
    index_name = "netguard-suricata-*"

    if not es_client.indices.exists(index=index_name):
        print(f"Index {index_name} does not exist.")
        return []

    try:
        # This is the corrected query to find actual alerts
        query = {
            "query": {
                "bool": {
                    "must": [
                        # Suricata's alert documents are identified by this field.
                        # If this doesn't work, change "event_type" to "event.kind".
                        { "match": { "event_type": "alert" } }
                    ]
                }
            },
            "sort": [
                { "@timestamp": "desc" }
            ],
            "size": limit
        }

        res = es_client.search(index=index_name, body=query)
        # We return the full source of each alert document
        return [hit['_source'] for hit in res['hits']['hits']]

    except Exception as e:
        print(f"ERROR: Alert Service failed to query Elasticsearch: {e}")
        return []