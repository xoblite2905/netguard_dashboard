# backend/app/services/ids_query_service.py
import os
from elasticsearch import Elasticsearch, RequestError
from datetime import datetime, timedelta # Import timedelta for dynamic time ranges
import json

# This service is dedicated to querying IDS data from Elasticsearch
es_host = os.getenv("ELASTICSEARCH_URI", "http://elasticsearch:9200")

# ### --- START OF CHANGES --- ###
# Increase default timeout for Elasticsearch client substantially for complex aggregations.
# 60 seconds should give it plenty of time now, especially with the time range filter.
es_client = Elasticsearch(es_host, timeout=60)
# ### --- END OF CHANGES --- ###


def get_latest_zeek_connections(limit: int = 100):
    """
    Queries Elasticsearch for the latest Zeek connection logs.
    """
    # This index pattern correctly matches your Filebeat configuration.
    index_pattern = "netguard-zeek-7.17.20-*"

    if not es_client.indices.exists(index=index_pattern):
        print(f"WARNING: Zeek index pattern '{index_pattern}' not found.")
        return []
    try:
        query = {
            "size": limit,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        { "exists": { "field": "proto" } }
                    ]
                }
            }
        }

        res = es_client.search(index=index_pattern, body=query)
        return [hit['_source'] for hit in res['hits']['hits']]
    except Exception as e:
        print(f"ERROR: Failed to query Zeek connections: {e}")
        return []

def get_latest_suricata_flows(limit: int = 100):
    """
    Queries Elasticsearch for the latest Suricata flow logs.
    """
    if not es_client.indices.exists(index="netguard-suricata-*"):
        print("WARNING: Suricata index 'netguard-suricata-*' not found.")
        return []
    try:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"event_type": "flow"}}
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": limit
        }
        res = es_client.search(index="netguard-suricata-*", body=query)
        return [hit['_source'] for hit in res['hits']['hits']]
    except Exception as e:
        print(f"ERROR: Failed to query Suricata flows: {e}")
        return []


def get_zeek_protocol_distribution(limit: int = 10):
    """
    Queries Elasticsearch for the top protocols by total bytes transferred (orig_ip_bytes + resp_ip_bytes)
    from Zeek connection logs. This version attempts to infer application-layer protocols based on ports.
    Critically, this query now only aggregates data from the last hour for performance.
    """
    index_pattern = "netguard-zeek-7.17.20-*"

    if not es_client.indices.exists(index=index_pattern):
        print(f"WARNING: Zeek index pattern '{index_pattern}' not found for protocol distribution.")
        return []
    try:
        # ### --- START OF CHANGES --- ###
        # Calculate time range: last 1 hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1) # Aggregate over the last 1 hour
        time_window_start = start_time.isoformat().replace('+00:00', 'Z')
        time_window_end = end_time.isoformat().replace('+00:00', 'Z')
        # ### --- END OF CHANGES --- ###

        query = {
            "size": 0, # We only need aggregations
            "query": {
                "bool": {
                    "must": [
                        { "exists": { "field": "proto" } }, # Ensure it's a connection log with protocol info
                        { "exists": { "field": "orig_ip_bytes" } }, # Ensure byte fields exist
                        { "exists": { "field": "resp_ip_bytes" } },
                        # ### --- START OF CHANGES (Added time range filter) --- ###
                        { "range": { "@timestamp": { "gte": time_window_start, "lte": time_window_end } } }
                        # ### --- END OF CHANGES --- ###
                    ]
                }
            },
            "aggs": {
                "protocol_traffic": {
                    "terms": {
                        "script": {
                            "lang": "painless",
                            "source": """
                                def final_protocol = "UNKNOWN"; // Use def for more dynamic typing if field is empty or absent
                                if (doc.containsKey('proto') && !doc['proto'].empty) {
                                    final_protocol = doc['proto'].value.toUpperCase();
                                }

                                int port = 0;
                                // Prefer id_orig_p, cast to int
                                if (doc.containsKey('id_orig_p') && !doc['id_orig_p'].empty) {
                                    port = (int) doc['id_orig_p'].value;
                                }
                                // If orig_p is not present or 0, check id_resp_p, cast to int
                                else if (doc.containsKey('id_resp_p') && !doc['id_resp_p'].empty) {
                                    port = (int) doc['id_resp_p'].value;
                                }

                                if (port == 80) return "HTTP";
                                if (port == 443) return "HTTPS";
                                if (port == 21) return "FTP";
                                if (port == 22) return "SSH";
                                if (port == 23) return "TELNET";
                                if (port == 25) return "SMTP";
                                if (port == 53) return "DNS";
                                if (port == 110) return "POP3";
                                if (port == 143) return "IMAP";
                                if (port == 3389) return "RDP";
                                if (port == 445) return "SMB";
                                // Fallback to the defensively retrieved transport protocol
                                return final_protocol;
                            """
                        },
                        "size": limit,
                        "order": {
                            "total_bytes": "desc"
                        }
                    },
                    "aggs": {
                        "total_bytes": {
                            "sum": {
                                "script": {
                                    "source": "doc['orig_ip_bytes'].value + doc['resp_ip_bytes'].value",
                                    "lang": "painless"
                                }
                            }
                        }
                    }
                }
            }
        }

        #print(f"DEBUG: Executing ES query for protocol distribution (last 1 hour): {json.dumps(query, indent=2)}")
        res = es_client.search(index=index_pattern, body=query) # Now uses client's new default 60s timeout
        #print(f"DEBUG: ES response for protocol distribution (full response, if no error): {json.dumps(res, indent=2)}")

        distribution_data = []
        if 'aggregations' in res and 'protocol_traffic' in res['aggregations'] and 'buckets' in res['aggregations']['protocol_traffic']:
            for bucket in res['aggregations']['protocol_traffic']['buckets']:
                protocol_name = bucket.get('key', "UNKNOWN")
                total_bytes_value = bucket.get('total_bytes', {}).get('value', 0)
                distribution_data.append({
                    "protocol": protocol_name,
                    "count": total_bytes_value
                })
            #print(f"DEBUG: Parsed protocol distribution data: {distribution_data}")
        else:
            print("WARNING: No or incomplete aggregations found in Elasticsearch response for protocol distribution.")
            if 'aggregations' in res:
                print(f"  Aggregations content: {json.dumps(res['aggregations'], indent=2)}")

        return distribution_data
    except RequestError as e:
        print(f"ERROR: Elasticsearch Request Error during protocol distribution: {e.status_code} - {e.error}")
        print(f"ERROR: Elasticsearch detailed error info: {json.dumps(e.info, indent=2)}")
        return []
    except Exception as e:
        print(f"ERROR: An unexpected Python error occurred during protocol distribution: {e}")
        return []


def query_alerts_by_ip_and_time(target_ip: str, start_time: datetime, end_time: datetime):
    """
    Queries Elasticsearch for Suricata alerts involving a specific IP within a given time window.
    This is specifically for IDS test validation.
    """
    if not es_client.indices.exists(index="filebeat-*"):
        return [] # Return empty if the index doesn't even exist

    try:
        # Give Filebeat a moment to process and ship the logs
        import time
        time.sleep(10)

        # Format timestamps for Elasticsearch query
        time_window_start = start_time.isoformat().replace('+00:00', 'Z')
        time_window_end = end_time.isoformat().replace('+00:00', 'Z')

        query = {
            "query": {
                "bool": {
                    "must": [
                        { "match": { "event.kind": "alert" } },
                        { "range": { "@timestamp": { "gte": time_window_start, "lte": time_window_end } } }
                    ],
                    "filter": [
                        { "bool": { "should": [
                            { "match": { "source.ip": target_ip } },
                            { "match": { "destination.ip": target_ip } }
                        ], "minimum_should_match": 1 } }
                    ]
                }
            }
        }

        res = es_client.search(index="filebeat-*", body=query, size=100)
        return [hit['_source'] for hit in res['hits']['hits']]

    except Exception as e:
        print(f"ERROR: IDS Query Service failed to query Elasticsearch: {e}")
        return []
