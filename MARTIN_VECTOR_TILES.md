# Martin Vector Tiles: Key Learnings

## Overview
Martin is a powerful PostGIS vector tile server written in Rust that can efficiently serve vector tiles directly from a PostgreSQL/PostGIS database. It's designed for high performance and can handle millions of features, making it ideal for visualizing large geospatial datasets like our building energy data.

## Key Features

### 1. Direct Database Connection
- Martin connects directly to PostgreSQL/PostGIS and generates vector tiles on-the-fly
- No need for pre-generating tiles or intermediate file formats
- Supports real-time data updates (changes in the database are immediately reflected in the tiles)

### 2. Performance Optimizations
- Written in Rust for high performance
- Supports connection pooling to efficiently handle multiple requests
- Can be configured with worker processes to utilize multiple CPU cores
- Includes tile caching to improve response times for frequently requested tiles

### 3. Feature Limits and Configuration
- Default limit of 10,000 features per tile (can be increased via configuration)
- Can handle millions of features with proper configuration
- Supports custom SQL functions for advanced tile generation logic
- Configurable via environment variables or a YAML configuration file

### 4. Integration with MapLibre GL JS
- Provides a TileJSON endpoint that MapLibre GL JS can consume directly
- Vector tiles are served in MVT (Mapbox Vector Tile) format
- Source layers are automatically named based on table names

## Best Practices

### Configuration
- Use a configuration file for complex setups instead of environment variables
- Increase `max_feature_count` for datasets with millions of features
- Adjust `pool_size` based on expected concurrent connections
- Set appropriate `worker_processes` based on available CPU cores
- Enable caching with `cache_size_mb` for frequently accessed tiles

### Performance
- Ensure proper indexing on the geometry column in PostgreSQL
- Set appropriate zoom level ranges (minzoom and maxzoom) for your data
- Consider using explicit bounds to optimize tile generation
- For extremely large datasets, consider using function sources with custom SQL

### Integration with Web Maps
- Use the TileJSON endpoint URL in MapLibre GL JS source configuration
- Match the source-layer name with the table name or ID from TileJSON
- For boolean values in styling expressions, convert to strings using `to-string`
- Consider client-side filtering for specific visualization needs

## Troubleshooting

### Common Issues
1. **404 Not Found for Tiles**: 
   - Check if the table exists and is accessible to Martin
   - Verify the source-layer name matches the table name
   - Ensure the geometry column is properly indexed

2. **Too Many Features Error**:
   - Increase `max_feature_count` in configuration
   - Add client-side filtering based on zoom levels
   - Consider simplifying geometries at lower zoom levels

3. **Slow Tile Generation**:
   - Check database indexes on the geometry column
   - Increase connection pool size and worker processes
   - Enable caching for frequently accessed tiles

4. **Integration with MapLibre**:
   - Use the TileJSON endpoint instead of direct tile URLs
   - Ensure source-layer name matches the layer ID from TileJSON
   - Convert boolean values to strings in styling expressions

## Advanced Usage

### Custom Functions
Martin supports custom SQL functions for advanced tile generation, which can be useful for:
- Dynamic data aggregation at different zoom levels
- Custom filtering or data transformations
- Combining multiple data sources into a single tile layer

### Bulk Tile Generation
For offline use or performance optimization, Martin provides a tool called `martin-cp` that can:
- Generate tiles for a specified area and zoom range
- Save tiles to MBTiles format for offline use
- Combine multiple sources into a single tileset

### Multiple Data Sources
Martin can serve tiles from various sources:
- Multiple PostgreSQL tables
- MBTiles files
- PMTiles files
- Remote tile sources

## Conclusion
Martin is an excellent solution for serving vector tiles directly from a PostGIS database. With proper configuration, it can efficiently handle millions of features and provide a seamless integration with web mapping libraries like MapLibre GL JS. Its flexibility and performance make it ideal for visualizing large geospatial datasets like our building energy data across Senegal.
