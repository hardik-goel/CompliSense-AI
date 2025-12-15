def build_heatmap(results):
    matrix = {}
    for r in results:
        key = f"{r['severity']}|{r['risk']}"
        matrix[key] = matrix.get(key, 0) + 1
    return matrix
