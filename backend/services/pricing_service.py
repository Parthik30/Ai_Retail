def calculate_final_price(price, discount):
    return round(price * (1 - discount / 100), 2)


def calculate_profit(price, cost, sales):
    return round((price - cost) * sales, 2)
