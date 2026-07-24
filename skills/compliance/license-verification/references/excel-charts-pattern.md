# Excel Charts with openpyxl

## Imports (must be inside function to avoid import errors)
```python
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
```

## Pie Chart (License Status)
```python
pie = PieChart()
pie.title = "License Verification Status"
pie.style = 10
pie.width = 18
pie.height = 12
labels = Reference(ws, min_col=1, min_row=2, max_row=4)
data = Reference(ws, min_col=2, min_row=1, max_row=4)
pie.add_data(data, titles_from_data=True)
pie.set_categories(labels)
pie.dataLabels = DataLabelList()
pie.dataLabels.showPercent = True
pie.dataLabels.showVal = True
# Color slices
pt0 = DataPoint(idx=0)
pt0.graphicalProperties.solidFill = "00B050"  # Green for PASS
pie.series[0].data_points.append(pt0)
ws.add_chart(pie, "D1")
```

## Bar Chart (Star Ratings)
```python
bar = BarChart()
bar.type = "col"
bar.title = "CMS Overall Star Rating Distribution"
bar.y_axis.title = "Number of Facilities"
bar.x_axis.title = "Star Rating"
bar.style = 10
bar.width = 18
bar.height = 12
cats = Reference(ws, min_col=1, min_row=7, max_row=11)
vals = Reference(ws, min_col=2, min_row=6, max_row=11)
bar.add_data(vals, titles_from_data=True)
bar.set_categories(cats)
bar.shape = 4
ws.add_chart(bar, "D16")
```

## Horizontal Bar (Expiration Timeline)
```python
bar = BarChart()
bar.type = "bar"  # Horizontal
bar.title = "License Expiration Timeline"
bar.style = 10
bar.width = 18
bar.height = 12
cats = Reference(ws, min_col=1, min_row=21, max_row=27)
vals = Reference(ws, min_col=2, min_row=20, max_row=27)
bar.add_data(vals, titles_from_data=True)
bar.set_categories(cats)
ws.add_chart(bar, "D46")
```

## Data Layout
Chart data goes in columns A-B of the chart sheet. Charts are placed starting at column D.
This keeps data and charts on the same sheet without the data being obtrusive.

## Tab Colors
```python
ws.sheet_properties.tabColor = "366092"  # Blue
ws.sheet_properties.tabColor = "00B050"  # Green
ws.sheet_properties.tabColor = "FFC000"  # Orange
```
