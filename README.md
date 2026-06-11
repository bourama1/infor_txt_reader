# infor-txt-reader

A standalone library for parsing Infor BOM text files.

## Usage

```python
from infor_txt_reader.reader import InforReader

reader = InforReader()
results = reader.read("path/to/infor_bom.txt")

for config in results:
    print(config['meta']['reference_order'])
    # Access sections and features
    door_leaf = config.get('Door leaf', {})
    width = door_leaf.get('T06210134')
```

## Data Example

``` json
[
    {
            "meta": {
                "reference_order": "TQ1000514",
                "reference_position": "010",
                "product_configuration_date": "10.06.2026"
            },
            "Industrial door (T10 gen. 02)": {
                "T06090305": "500",
            "T06090309": "5",
            "T06210023": "3",
            # ... other features
        },
        "Door leaf": {
            "T06210134": "3050",
            "T06091430": "n",
            # ... other features
        },
        "1. Panel section": {
            "T06800010": "n",
            "T06110165": "610",
            # ... other features
        },
        "5. Glazing for FVE": {
            "T66211580": "637",
            "T66211581": "305",
        }
    },
    # ... additional positions found in the same file
]
```
