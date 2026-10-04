# преобразования [0.12, -0.34, 0.56] в [0.12, -0.34, 0.56] которое затем передаём PostgreSQL
def vector_to_pg(vector: list[float]) -> str:
    return "[" + ",".join(map(str, vector)) + "]"