def build_heatmap(results):
    """
    Builds a severity × risk matrix for dashboard visualization
    """
    matrix = {}
    for r in results:
        key = f"{r['severity']}|{r['risk']}"
        matrix[key] = matrix.get(key, 0) + 1
    return matrix
