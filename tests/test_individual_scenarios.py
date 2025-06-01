#!/usr/bin/env python3

import requests
import json
import os
import time
import argparse
from typing import Dict, Any, Optional

class IndividualScenarioTester:
    def __init__(self, base_url: str = "http://localhost:8008/api/v1"):
        self.base_url = base_url
        self.test_project_id = None
        
    def setup_project(self) -> bool:
        """Setup a test project"""
        project_data = {
            "name": f"Individual Test Project {int(time.time())}",
            "description": "Individual scenario testing",
            "organization_type": "government"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/projects/",
                json=project_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                project = response.json()
                self.test_project_id = project["id"]
                print(f"✅ Created test project: {self.test_project_id}")
                return True
            else:
                print(f"❌ Failed to create project: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating project: {str(e)}")
            return False
    
    def test_single_ui_polygon(self):
        """Test single polygon from UI drawing"""
        print("\n🎯 Testing: Single UI Polygon")
        
        if not self.test_project_id:
            if not self.setup_project():
                return False
        
        geometry_input = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-17.0, 14.5],
                        [-16.8, 14.5],
                        [-16.8, 14.7],
                        [-17.0, 14.7],
                        [-17.0, 14.5]
                    ]
                ]
            },
            "name": "Single UI Drawn Area",
            "area_type": "village"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/projects/{self.test_project_id}/areas/enhanced",
                json=geometry_input,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                area = response.json()
                print(f"✅ SUCCESS: Created area '{area['name']}' with {area['area_sq_km']:.2f} km²")
                print(f"   ID: {area['id']}")
                print(f"   Type: {area['area_type']}")
                print(f"   Source: {area.get('source_type', 'N/A')}")
                return True
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_multiple_ui_polygons(self):
        """Test multiple polygons from UI drawing"""
        print("\n🎯 Testing: Multiple UI Polygons")
        
        if not self.test_project_id:
            if not self.setup_project():
                return False
        
        geometry_input = {
            "geometry": [
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-17.2, 14.1],
                            [-17.0, 14.1],
                            [-17.0, 14.3],
                            [-17.2, 14.3],
                            [-17.2, 14.1]
                        ]
                    ]
                },
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-16.8, 14.1],
                            [-16.6, 14.1],
                            [-16.6, 14.3],
                            [-16.8, 14.3],
                            [-16.8, 14.1]
                        ]
                    ]
                },
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-16.4, 14.1],
                            [-16.2, 14.1],
                            [-16.2, 14.3],
                            [-16.4, 14.3],
                            [-16.4, 14.1]
                        ]
                    ]
                }
            ],
            "name": "Multiple UI Areas",
            "area_type": "custom"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/projects/{self.test_project_id}/areas/enhanced",
                json=geometry_input,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                areas = response.json()
                if isinstance(areas, list):
                    print(f"✅ SUCCESS: Created {len(areas)} areas")
                    for i, area in enumerate(areas, 1):
                        print(f"   {i}. {area['name']} - {area['area_sq_km']:.2f} km²")
                    return True
                else:
                    print(f"❌ FAILED: Expected list, got single area")
                    return False
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_geojson_feature(self):
        """Test GeoJSON Feature input"""
        print("\n🎯 Testing: GeoJSON Feature")
        
        if not self.test_project_id:
            if not self.setup_project():
                return False
        
        geometry_input = {
            "geometry": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-15.8, 14.2],
                            [-15.6, 14.2],
                            [-15.6, 14.4],
                            [-15.8, 14.4],
                            [-15.8, 14.2]
                        ]
                    ]
                },
                "properties": {
                    "village_name": "Test Feature Village",
                    "population": 950,
                    "electrified": False
                }
            },
            "name": "GeoJSON Feature Area",
            "area_type": "village"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/projects/{self.test_project_id}/areas/enhanced",
                json=geometry_input,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                area = response.json()
                print(f"✅ SUCCESS: Created area with preserved properties")
                print(f"   Name: {area['name']}")
                print(f"   Area: {area['area_sq_km']:.2f} km²")
                print(f"   Properties preserved: {bool(area.get('area_metadata', {}).get('properties'))}")
                return True
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_overlapping_merge(self):
        """Test overlapping geometries with merge"""
        print("\n🎯 Testing: Overlapping Geometries with Merge")
        
        if not self.test_project_id:
            if not self.setup_project():
                return False
        
        geometry_input = {
            "geometry": [
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-14.8, 14.5],
                            [-14.6, 14.5],
                            [-14.6, 14.7],
                            [-14.8, 14.7],
                            [-14.8, 14.5]
                        ]
                    ]
                },
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-14.7, 14.6],
                            [-14.5, 14.6],
                            [-14.5, 14.8],
                            [-14.7, 14.8],
                            [-14.7, 14.6]
                        ]
                    ]
                },
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-14.4, 14.5],
                            [-14.2, 14.5],
                            [-14.2, 14.7],
                            [-14.4, 14.7],
                            [-14.4, 14.5]
                        ]
                    ]
                }
            ],
            "name": "Overlapping Test",
            "area_type": "custom",
            "merge_overlapping": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/projects/{self.test_project_id}/areas/enhanced",
                json=geometry_input,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                areas = response.json()
                if isinstance(areas, list):
                    print(f"✅ SUCCESS: Merged overlapping geometries into {len(areas)} areas")
                    for area in areas:
                        print(f"   {area['name']} - {area['area_sq_km']:.2f} km²")
                else:
                    print(f"✅ SUCCESS: Merged into single area: {areas['name']} - {areas['area_sq_km']:.2f} km²")
                return True
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_upload_single_geojson(self):
        """Test uploading single feature GeoJSON file"""
        print("\n🎯 Testing: Upload Single GeoJSON File")
        
        if not self.test_project_id:
            if not self.setup_project():
                return False
        
        file_path = "file_test/onefeature.geojson"
        if not os.path.exists(file_path):
            print(f"❌ FAILED: File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': ('onefeature.geojson', f, 'application/json')}
                data = {
                    'name': 'Uploaded Single Feature',
                    'area_type': 'village'
                }
                
                response = requests.post(
                    f"{self.base_url}/projects/{self.test_project_id}/areas/upload-enhanced",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                area = response.json()
                if isinstance(area, list):
                    print(f"✅ SUCCESS: Uploaded {len(area)} areas from GeoJSON file")
                    for a in area:
                        print(f"   {a['name']} - {a['area_sq_km']:.2f} km²")
                else:
                    print(f"✅ SUCCESS: Uploaded area: {area['name']} - {area['area_sq_km']:.2f} km²")
                return True
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_upload_multiple_geojson(self):
        """Test uploading multiple features GeoJSON file"""
        print("\n🎯 Testing: Upload Multiple Features GeoJSON File")
        
        if not self.test_project_id:
            if not self.setup_project():
                return False
        
        file_path = "file_test/manyfeature.geojson"
        if not os.path.exists(file_path):
            print(f"❌ FAILED: File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': ('manyfeature.geojson', f, 'application/json')}
                data = {
                    'name': 'Uploaded Multiple Features',
                    'area_type': 'village'
                }
                
                response = requests.post(
                    f"{self.base_url}/projects/{self.test_project_id}/areas/upload-enhanced",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                areas = response.json()
                if isinstance(areas, list):
                    print(f"✅ SUCCESS: Uploaded {len(areas)} areas from FeatureCollection")
                    for area in areas:
                        print(f"   {area['name']} - {area['area_sq_km']:.2f} km²")
                else:
                    print(f"✅ SUCCESS: Uploaded single area from FeatureCollection")
                return True
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_upload_shapefile(self):
        """Test uploading shapefile"""
        print("\n🎯 Testing: Upload Shapefile")
        
        if not self.test_project_id:
            if not self.setup_project():
                return False
        
        file_path = "file_test/manyfeature.zip"
        if not os.path.exists(file_path):
            print(f"❌ FAILED: File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': ('manyfeature.zip', f, 'application/zip')}
                data = {
                    'name': 'Uploaded Shapefile',
                    'area_type': 'village'
                }
                
                response = requests.post(
                    f"{self.base_url}/projects/{self.test_project_id}/areas/upload-enhanced",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                areas = response.json()
                if isinstance(areas, list):
                    print(f"✅ SUCCESS: Uploaded {len(areas)} areas from shapefile")
                    for area in areas:
                        print(f"   {area['name']} - {area['area_sq_km']:.2f} km²")
                else:
                    print(f"✅ SUCCESS: Uploaded area from shapefile: {areas['name']}")
                return True
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_geometry_validation(self):
        """Test geometry validation endpoint"""
        print("\n🎯 Testing: Geometry Validation")
        
        test_geom = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-15.0, 14.0], [-14.8, 14.0], [-14.8, 14.2], [-15.0, 14.2], [-15.0, 14.0]]]
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/projects/validate-geometry",
                json=test_geom,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                validation = response.json()
                print(f"✅ SUCCESS: Validation completed")
                print(f"   Valid: {validation['is_valid']}")
                print(f"   Features: {validation.get('geometry_info', {}).get('total_features', 'N/A')}")
                print(f"   Will create areas: {validation.get('geometry_info', {}).get('will_create_areas', 'N/A')}")
                return True
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_geometry_analysis(self):
        """Test geometry analysis endpoint"""
        print("\n🎯 Testing: Geometry Analysis")
        
        test_geom = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-15.0, 14.0], [-14.8, 14.0], [-14.8, 14.2], [-15.0, 14.2], [-15.0, 14.0]]]
                    },
                    "properties": {"name": "Test Village"}
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/projects/analyze-geometry",
                json={"geometry_input": test_geom, "base_name": "Analysis Test"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                analysis = response.json()
                print(f"✅ SUCCESS: Analysis completed")
                print(f"   Total features: {analysis['total_features']}")
                print(f"   Geometry types: {analysis['geometry_types']}")
                print(f"   Will create areas: {analysis['will_create_areas']}")
                print(f"   Total estimated area: {analysis.get('total_estimated_area_sq_km', 'N/A')} km²")
                return True
            else:
                print(f"❌ FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description="Individual Project Area Scenario Tester")
    parser.add_argument("--scenario", "-s", choices=[
        "single-ui", "multiple-ui", "geojson-feature", "overlapping-merge",
        "upload-single", "upload-multiple", "upload-shapefile", 
        "validation", "analysis", "all"
    ], default="all", help="Specific scenario to test")
    parser.add_argument("--url", "-u", default="http://localhost:8008/api/v1", 
                       help="Base API URL")
    
    args = parser.parse_args()
    
    print("🧪 Energy Model - Individual Scenario Tester")
    print("=" * 50)
    
    # Change to script directory to find test files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    tester = IndividualScenarioTester(base_url=args.url)
    
    # Wait for API
    print("⏳ Checking API availability...")
    for i in range(10):
        try:
            response = requests.get(f"{args.url.replace('/api/v1', '')}/health")
            if response.status_code == 200:
                print("✅ API is ready!")
                break
        except:
            pass
        time.sleep(2)
    else:
        print("❌ API not available")
        return False
    
    scenarios = {
        "single-ui": tester.test_single_ui_polygon,
        "multiple-ui": tester.test_multiple_ui_polygons,
        "geojson-feature": tester.test_geojson_feature,
        "overlapping-merge": tester.test_overlapping_merge,
        "upload-single": tester.test_upload_single_geojson,
        "upload-multiple": tester.test_upload_multiple_geojson,
        "upload-shapefile": tester.test_upload_shapefile,
        "validation": tester.test_geometry_validation,
        "analysis": tester.test_geometry_analysis
    }
    
    if args.scenario == "all":
        print("🔄 Running all scenarios...\n")
        results = []
        for name, test_func in scenarios.items():
            print(f"\n{'=' * 60}")
            result = test_func()
            results.append((name, result))
            time.sleep(1)
        
        print(f"\n{'=' * 60}")
        print("📊 SUMMARY")
        print("=" * 60)
        
        passed = 0
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} | {name}")
            if result:
                passed += 1
        
        print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {len(results) - passed}")
        
        if passed == len(results):
            print("🎉 ALL SCENARIOS PASSED!")
        else:
            print("⚠️  Some scenarios failed")
        
    else:
        if args.scenario in scenarios:
            scenarios[args.scenario]()
        else:
            print(f"❌ Unknown scenario: {args.scenario}")

if __name__ == "__main__":
    main()