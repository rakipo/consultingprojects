# Batch Neo4j Data Loader

## Overview

The Batch Neo4j Data Loader is designed to handle large datasets efficiently by processing data in configurable batches. This prevents the system from getting stuck when processing huge amounts of data.

## Key Features

- **Batch Processing**: Processes records in configurable batch sizes
- **Status Tracking**: Updates `status_neo4j` field after each successful batch
- **Progress Monitoring**: Shows progress percentage and batch completion status
- **Error Recovery**: Continues processing even if individual batches fail
- **Memory Efficient**: Only loads batch_size records into memory at a time

## Configuration

### Batch Configuration

Add the following section to your config file:

```yaml
# Batch Processing Configuration
batch_config:
  batch_size: 5  # Process 5 records at a time
  enable_status_tracking: true  # Update status_neo4j after each batch
```

### Query Modification

Update your query to only fetch unprocessed records:

```yaml
queries:
  trending: 'SELECT * from structured_content WHERE status_neo4j = false OR status_neo4j IS NULL;'
```

## Usage

### Command Line

```bash
# Basic usage
python src/batch_loader.py config/config_boomer_model_userdefined.yml

# With custom model and metrics files
python src/batch_loader.py config/config_boomer_model_userdefined.yml \
  --model-file output/data/my_model.json \
  --metrics-file output/metrics/my_metrics.txt
```

### Test Script

```bash
# Run the test script
python test_batch_loader.py
```

## How It Works

1. **Initialization**: 
   - Loads configuration and determines batch size
   - Connects to PostgreSQL and Neo4j
   - Gets total record count

2. **Batch Processing**:
   - Fetches `batch_size` records from PostgreSQL
   - Processes embeddings and chunks for each record
   - Loads nodes and relationships into Neo4j
   - Updates `status_neo4j = true` for processed records

3. **Progress Tracking**:
   - Shows progress percentage after each batch
   - Logs batch completion status
   - Continues to next batch regardless of individual batch failures

4. **Completion**:
   - Writes comprehensive metrics to output file
   - Closes database connections

## Output Files

### Model File
- Contains the Neo4j model configuration used for loading
- Generated with timestamp: `neo4j_model_clean_YYYYMMDD_HHMMSS.json`

### Metrics File
- Contains detailed batch processing metrics
- Generated with timestamp: `batch_load_metrics_YYYYMMDD_HHMMSS.txt`

## Metrics Structure

```json
{
  "batch_metrics": {
    "total_batches": 20,
    "completed_batches": 18,
    "failed_batches": 2,
    "total_records_processed": 90,
    "batch_errors": [...]
  },
  "load_metrics": {
    "nodes_created": {...},
    "relationships_created": {...},
    "chunks_created": 450,
    "embeddings_generated": 450
  },
  "cypher_usage": {...},
  "timestamp": "2025-08-12T23:30:00"
}
```

## Error Handling

- **Individual Batch Failures**: Logged but don't stop the entire process
- **Database Connection Issues**: Retry logic for transient failures
- **Status Update Failures**: Logged but processing continues
- **Memory Issues**: Reduced by processing smaller batches

## Performance Tips

1. **Start Small**: Begin with `batch_size: 5` and increase gradually
2. **Monitor Memory**: Watch system resources during processing
3. **Check Logs**: Review batch error logs for failed batches
4. **Resume Processing**: Failed batches can be retried by resetting `status_neo4j = false`

## Troubleshooting

### Common Issues

1. **Process Gets Stuck**: Reduce batch size
2. **Memory Errors**: Decrease batch size further
3. **Database Timeouts**: Increase connection timeout settings
4. **Failed Batches**: Check logs for specific error details

### Recovery

To retry failed batches:

```sql
-- Reset status for failed records
UPDATE structured_content 
SET status_neo4j = false 
WHERE id IN (list_of_failed_ids);
```

Then re-run the batch loader.

## Comparison with Original Loader

| Feature | Original Loader | Batch Loader |
|---------|----------------|--------------|
| Memory Usage | High (all records) | Low (batch_size records) |
| Progress Tracking | None | Real-time progress |
| Error Recovery | Stops on error | Continues processing |
| Status Tracking | None | Updates after each batch |
| Scalability | Limited | High |
| Monitoring | Basic logs | Detailed metrics |

## Example Output

```
2025-08-12 23:30:00 - __main__ - INFO - [load_data_in_batches:245] - Processing 100 records in 20 batches of size 5
2025-08-12 23:30:05 - __main__ - INFO - [process_batch:180] - Batch 1: Completed successfully
2025-08-12 23:30:05 - __main__ - INFO - [load_data_in_batches:260] - Progress: 5.0% (1/20 batches completed)
2025-08-12 23:30:10 - __main__ - INFO - [process_batch:180] - Batch 2: Completed successfully
2025-08-12 23:30:10 - __main__ - INFO - [load_data_in_batches:260] - Progress: 10.0% (2/20 batches completed)
...
2025-08-12 23:35:00 - __main__ - INFO - [load_data_in_batches:265] - Batch Neo4j data loading completed successfully
```
