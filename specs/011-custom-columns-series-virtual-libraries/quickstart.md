# Quickstart: 011 Custom Columns, Series & Virtual Libraries

## 1. Defining Custom Columns
You can define custom columns using standard Calibre labels (e.g. `read_status`, `pages`, `difficulty`):
```bash
curl -X POST http://127.0.0.1:8000/api/libraries/default/custom-columns \
  -H "Content-Type: application/json" \
  -d '{
    "label": "read_status",
    "name": "Read Status",
    "datatype": "enumeration",
    "display": {"enum_values": ["Unread", "Reading", "Completed", "Abandoned"]}
  }'
```

Or install pre-packaged presets with 1-click:
```bash
curl -X POST http://127.0.0.1:8000/api/libraries/default/custom-columns/presets
```

## 2. Updating Book Custom Column Values & Series
```bash
# Update custom columns
curl -X PUT http://127.0.0.1:8000/api/books/1/custom-values \
  -H "Content-Type: application/json" \
  -d '{"read_status": "Reading", "pages": 350, "rating": 5}'

# Assign to a series with index
curl -X PUT http://127.0.0.1:8000/api/books/1/series \
  -H "Content-Type: application/json" \
  -d '{"name": "Foundation", "series_index": 1.0}'
```

## 3. Creating and Using Virtual Libraries
```bash
curl -X POST http://127.0.0.1:8000/api/libraries/default/virtual-libraries \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Currently Reading",
    "query": "#read_status:Reading"
  }'
```
Now click the "Currently Reading" tab in the web UI header to filter your collection instantly!
