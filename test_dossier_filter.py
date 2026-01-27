#!/usr/bin/env python3
"""
Quick test script for the dossier filter endpoint.
Run this after restarting the server.
"""

import requests

BASE_URL = "http://127.0.0.1:8001"

def test_filter_no_params():
    response = requests.get(f"{BASE_URL}/dossiers/filter")
    print(f"No params: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found {len(data)} dossiers")
    return response

def test_filter_by_provenance():
    response = requests.get(f"{BASE_URL}/dossiers/filter", params={"provenance": "Babylon"})
    print(f"\nProvenance=Babylon: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found {len(data)} dossiers")
        if data:
            print(f"  First dossier: {data[0]['_id']}")
    return response

def test_filter_by_script_period():
    response = requests.get(f"{BASE_URL}/dossiers/filter", params={"scriptPeriod": "Old Babylonian"})
    print(f"\nScriptPeriod=Old Babylonian: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found {len(data)} dossiers")
        if data:
            print(f"  First dossier: {data[0]['_id']}")
    return response

def test_filter_multiple():
    response = requests.get(
        f"{BASE_URL}/dossiers/filter",
        params={"provenance": "Sippar-Amnānum", "scriptPeriod": "Old Babylonian"}
    )
    print(f"\nMultiple filters: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found {len(data)} dossiers")
        if data:
            print(f"  Dossiers: {[d['_id'] for d in data[:3]]}")
    return response

if __name__ == "__main__":
    print("Testing /dossiers/filter endpoint\n" + "="*50)
    try:
        test_filter_no_params()
        test_filter_by_provenance()
        test_filter_by_script_period()
        test_filter_multiple()
        print("\n All tests completed!")
    except requests.exceptions.ConnectionError:
        print("\n Could not connect to server. Make sure it's running on port 8001")
    except Exception as e:
        print(f"\n Error: {e}")
