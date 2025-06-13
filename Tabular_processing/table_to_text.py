
def table_to_readable_paragraph(data_dict):
    # Extract all keys and sort them by row and column numbers
    sorted_items = sorted(data_dict.items(), key=lambda x: (int(x[0].split()[1]), int(x[0].split()[3])))

    headers = []
    table_rows = {}

    for key, value in sorted_items:
        parts = key.split()
        row_num = int(parts[1])
        col_num = int(parts[3])

        if row_num == 1:
            headers.append(value)
        else:
            if row_num not in table_rows:
                table_rows[row_num] = {}
            table_rows[row_num][col_num] = value

    # Now build the paragraph
    paragraph = []
    for row in sorted(table_rows.keys()):
        row_data = table_rows[row]
        sentence = ", ".join(
            f"{headers[col - 1]} is {row_data[col]}" for col in sorted(row_data.keys()) if col <= len(headers)
        )
        paragraph.append(sentence + ".")

    return " ".join(paragraph)
data = {
    "Row 1 Column 1": "Time (drops of water)",
    "Row 1 Column 2": "Distance (cm)",
    "Row 1 Column 3": "Car",
    "Row 1 Column 4": "Engine",
    "Row 1 Column 5": "Date",
    "Row 2 Column 1": "1",
    "Row 2 Column 2": "10,11,9",
    "Row 2 Column 3": "Spirit of America",
    "Row 2 Column 4": "GE J47",
    "Row 2 Column 5": "8/5/63",
    "Row 3 Column 1": "2",
    "Row 3 Column 2": "29,31, 30",
    "Row 3 Column 3": "Wingfoot Express",
    "Row 3 Column 4": "WE J46",
    "Row 3 Column 5": "10/2/64",
    # ...
}

result = table_to_readable_paragraph(data)
print(result)
