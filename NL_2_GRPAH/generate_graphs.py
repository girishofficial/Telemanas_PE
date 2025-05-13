import matplotlib.pyplot as plt

class FlexiblePieChart:
    def __init__(self, columns, rows):
        """
        columns: list of column names
        rows: list of tuples (each tuple is one row)
        
        Supports:
         - Single‑column count data: columns=['Category'], rows=[(count1,), (count2,), …]
         - Two‑column label+count: columns=['Label','Count'], rows=[(label1,count1),…]
         - Multi‑column single row: columns=['A','B','C'], rows=[(vA,vB,vC)]
        """
        self.columns = columns
        self.rows = rows

    def _extract_label_counts(self):
        # Case A: Two columns and each row is (label, count)
        if len(self.columns) == 2 and all(isinstance(r[0], str) and isinstance(r[1], (int, float)) for r in self.rows):
            return [(r[0], r[1]) for r in self.rows]

        # Case B: Single row with >1 numeric values: use columns as labels
        if len(self.rows) == 1 and all(isinstance(v, (int, float)) for v in self.rows[0]):
            return list(zip(self.columns, self.rows[0]))

        # Case C: Single‑column counts: use index as label
        if len(self.columns) == 1 and all(isinstance(r[0], (int, float)) for r in self.rows):
            return [(str(idx), r[0]) for idx, r in enumerate(self.rows, start=1)]

        # Otherwise, fall back to interpreting the *last* column as count, 
        # and all preceding columns concatenated as label
        data = []
        for row in self.rows:
            label = " - ".join(str(row[i]) for i in range(len(row)-1))
            count = row[-1]
            if isinstance(count, (int, float)):
                data.append((label, count))
        return data

    def _plot(self, data, title="Pie Chart"):
        labels, counts = zip(*data)
        plt.figure(figsize=(6, 6))
        wedges, texts, autotexts = plt.pie(
            counts,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=plt.cm.Paired.colors,
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )

        # Bolden label texts and percentage texts
        for text in texts + autotexts:
            text.set_fontweight('bold')

        plt.title(title, fontweight='bold')
        plt.axis('equal')
        plt.tight_layout()

        # Save to file
        plt.savefig("pie_chart.png", dpi=300)
        plt.show()

    def make_pie(self, title=None):
        data = self._extract_label_counts()
        if not data:
            raise ValueError("Could not extract label‑count pairs from input.")
        chart_title = title or "Distribution"
        self._plot(data, chart_title)


# ---------------- Example Usage ----------------

if __name__ == "__main__":
    # Example 1: Two‑column label+count
    cols2 = ['Males', 'Females']
    rows2 = [(705, 254)]
    FlexiblePieChart(cols2, rows2).make_pie("Gender Distribution")

    # Example 2: Multi-column single row
    colsX = ['A', 'B', 'C', 'D']
    rowsX = [(1, 2, 3, 4)]
    FlexiblePieChart(colsX, rowsX).make_pie("Category Distribution")

    # Example 3: Arbitrary rows of (label, count)
    cols1 = ['State', 'Count']
    rows1 = [
        ('Tamil_Nadu', 425), ('Madhya_Pradesh', 79),
        ('Telangana', 76), ('Jammu_Kashmir', 59),
        ('Uttar_Pradesh', 58),
    ]
    FlexiblePieChart(cols1, rows1).make_pie("Top 5 States by Count")
